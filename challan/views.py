import os
import tempfile
from functools import wraps
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from collections import Counter

from . import backup as bk
from . import importer
from .forms import ChallanForm, make_item_formset
from .models import DeliveryChallan


def staff_required(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


@login_required
def home(request):
    today = timezone.localdate()
    qs = DeliveryChallan.objects
    return render(request, "challan/home.html", {
        "total": qs.count(),
        "this_month": qs.filter(dc_date__year=today.year, dc_date__month=today.month).count(),
        "latest": qs.first(),
    })


# ---------- Delivery challan: create / edit / print / delete ----------

@login_required
def dc_form(request, pk=None):
    challan = get_object_or_404(DeliveryChallan, pk=pk) if pk else None
    FormSet = make_item_formset(extra=0 if challan else 1)

    if request.method == "POST":
        form = ChallanForm(request.POST, instance=challan)
        formset = FormSet(request.POST, instance=challan)
        if form.is_valid() and formset.is_valid():
            kept = [f for f in formset.forms
                    if f.cleaned_data and not f.cleaned_data.get("DELETE")]
            if not kept:
                messages.error(request, "Add at least one item before saving.")
            else:
                with transaction.atomic():
                    obj = form.save(commit=False)
                    if not obj.pk:
                        obj.created_by = request.user
                    obj.save()
                    formset.instance = obj
                    formset.save()
                messages.success(request, f"Delivery Challan {obj.dc_no} saved.")
                if "save_print" in request.POST:
                    return redirect(reverse("dc_print", args=[obj.pk]) + "?auto=1")
                return redirect("dc_edit", pk=obj.pk)
    else:
        form = ChallanForm(instance=challan,
                           initial=None if challan else {"dc_no": DeliveryChallan.next_number()})
        formset = FormSet(instance=challan)

    return render(request, "challan/dc_form.html", {
        "form": form, "formset": formset, "challan": challan,
        "empty_form": formset.empty_form,
    })


@login_required
def dc_print(request, pk):
    challan = get_object_or_404(DeliveryChallan, pk=pk)
    return render(request, "challan/dc_print.html", {
        "challan": challan,
        "items": challan.items.all(),
        "auto": request.GET.get("auto") == "1",
    })


@login_required
@require_POST
def dc_delete(request, pk):
    challan = get_object_or_404(DeliveryChallan, pk=pk)
    no = challan.dc_no
    challan.delete()
    messages.success(request, f"Delivery Challan {no} deleted.")
    return redirect("dc_list")


@login_required
def dc_list(request):
    qs = DeliveryChallan.objects.select_related("created_by").annotate(
        item_count=Count("items", distinct=True)).order_by("-dc_date", "-id")
    q = request.GET.get("q", "").strip()
    dtype = request.GET.get("type", "")
    d_from = request.GET.get("from", "")
    d_to = request.GET.get("to", "")
    year = request.GET.get("year", "")
    if q:
        qs = qs.filter(Q(dc_no__icontains=q) | Q(to_name__icontains=q) |
                       Q(to_company__icontains=q) | Q(items__particulars__icontains=q)).distinct()
    if dtype in ("R", "N"):
        qs = qs.filter(challan_type=dtype)
    if d_from:
        qs = qs.filter(dc_date__gte=d_from)
    if d_to:
        qs = qs.filter(dc_date__lte=d_to)
    if year.isdigit():
        qs = qs.filter(dc_date__year=int(year))

    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "challan/dc_list.html", {
        "page": page, "q": q, "dtype": dtype, "d_from": d_from, "d_to": d_to,
        "year": year, "years": list(DeliveryChallan.objects.order_by().dates("dc_date", "year", order="DESC")),
        "qs_str": params.urlencode(),
    })


@staff_required
@require_POST
def dc_bulk_delete_year(request):
    year = request.POST.get("year", "")
    if not year.isdigit() or len(year) != 4:
        messages.error(request, "Choose a valid four-digit year.")
        return redirect("dc_list")
    year = int(year)
    qs = DeliveryChallan.objects.filter(dc_date__year=year)
    count = qs.count()
    if count == 0:
        messages.info(request, f"No Delivery Challans found for {year}.")
    else:
        qs.delete()
        messages.success(request, f"Deleted {count} Delivery Challan(s) for {year}, including their goods rows.")
    return redirect("dc_list")


# ---------- Backup / restore (staff only) ----------

@staff_required
def backup_page(request):
    return render(request, "challan/backup.html", {
        "backups": bk.list_backups(),
        "backup_dir": bk.backup_dir(),
    })


@staff_required
@require_POST
def backup_create(request):
    path = bk.make_backup()
    messages.success(request, f"Backup saved on the server: {path.name}")
    return redirect("backup")


@staff_required
def backup_download(request):
    path = bk.make_backup()
    return FileResponse(open(path, "rb"), as_attachment=True, filename=path.name)


@staff_required
def backup_download_file(request, name):
    path = bk.backup_dir() / Path(name).name
    if not path.is_file():
        raise Http404
    return FileResponse(open(path, "rb"), as_attachment=True, filename=path.name)


@staff_required
@require_POST
def backup_restore(request):
    if request.POST.get("confirm") != "yes":
        messages.error(request, "Tick the confirmation box to restore.")
        return redirect("backup")

    tmp = None
    try:
        server_file = request.POST.get("server_file")
        if server_file:
            path = bk.backup_dir() / Path(server_file).name
            if not path.is_file():
                raise ValueError("Backup file not found on the server.")
        else:
            upload = request.FILES.get("backup_file")
            if not upload:
                raise ValueError("Choose a backup file to upload.")
            fd, tmp = tempfile.mkstemp(suffix=".sqlite3")
            with os.fdopen(fd, "wb") as fh:
                for chunk in upload.chunks():
                    fh.write(chunk)
            path = Path(tmp)
        bk.restore_backup(path)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("backup")
    except Exception as exc:  # unexpected - show the reason instead of a crash page
        messages.error(request, f"Restore failed: {exc}")
        return redirect("backup")
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

    logout(request)
    messages.success(request, "Database restored. Please log in again.")
    return redirect("login")


# ---------- Import old challans from Word (staff only) ----------

@staff_required
def import_page(request):
    results, counts, dry = None, {}, False
    if request.method == "POST":
        files = request.FILES.getlist("files")
        dry = request.POST.get("dry_run") == "1"
        if not files:
            messages.error(request, "Choose one or more Word (.docx) files.")
        else:
            results = importer.import_files([(f.name, f) for f in files],
                                            user=request.user, dry_run=dry)
            counts = dict(Counter(r["status"] for r in results))
    return render(request, "challan/import.html",
                  {"results": results, "counts": counts, "dry": dry})
