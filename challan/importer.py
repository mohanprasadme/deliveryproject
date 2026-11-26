"""Import old Delivery Challans from Word (.docx) files that follow the DC layout."""
import re
from copy import deepcopy
from datetime import date
from pathlib import Path

from django.db import transaction
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from docx.table import Table

from .models import DCItem, DeliveryChallan

COMPANY_RE = re.compile(
    r"\b(limited|ltd|pvt|private|laborator\w*|industries|enterprises|company|corp\w*)\b", re.I)
DC_NO_RE = re.compile(r"DC\s*No\.?\s*[:\-]?\s*([A-Za-z0-9/\-]+)", re.I)
DC_DATE_RE = re.compile(r"DC\s*Date\.?\s*[:\-]?\s*(\d{1,2})\s*[./\-]\s*(\d{1,2})\s*[./\-]\s*(\d{2,4})", re.I)


class ParseError(Exception):
    pass


# ---------- low-level helpers ----------

def _on(el):
    """True if a Word on/off property element (w:b, w:strike) is switched on."""
    return el is not None and el.get(qn("w:val")) not in ("0", "false", "off")


def _para_text(p):
    out = []
    for el in p.iter():
        if el.tag == qn("w:t"):
            out.append(el.text or "")
        elif el.tag == qn("w:tab"):
            out.append(" ")
        elif el.tag in (qn("w:br"), qn("w:cr")):
            out.append("\n")
    return "".join(out)


def _styled_chars(p):
    chars = []
    for r in p.iter(qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        bold = rpr is not None and _on(rpr.find(qn("w:b")))
        strike = rpr is not None and (_on(rpr.find(qn("w:strike"))) or _on(rpr.find(qn("w:dstrike"))))
        text = "".join(t.text or "" for t in r.iter(qn("w:t")))
        chars.extend((c, bold, strike) for c in text)
    return chars


def _in_fallback(p):
    return any(a.tag.endswith("}Fallback") for a in p.iterancestors())


def _score(chars, start, end):
    seg = [c for c in chars[start:end] if not c[0].isspace()]
    if not seg:
        return 0.0
    return sum(c[1] for c in seg) / len(seg) - sum(c[2] for c in seg) / len(seg)


# ---------- parsing ----------

def _find_items_table(doc):
    for tbl in doc.tables:
        for row in tbl.rows[:3]:
            if any("PARTICULAR" in c.text.upper() for c in row.cells):
                return tbl
    return None


def _detect_type(paragraphs):
    found = {}
    for p in paragraphs:
        chars = _styled_chars(p)
        s = "".join(c[0] for c in chars).upper()
        for m in re.finditer(r"RETURNABLE", s):
            pre = re.search(r"NON[\s\-]*$", s[:m.start()])
            key = "N" if pre else "R"
            start = pre.start() if pre else m.start()
            found.setdefault(key, _score(chars, start, m.end()))
    if len(found) == 1:
        return next(iter(found)), None
    if len(found) == 2:
        if found["N"] > found["R"]:
            return "N", None
        if found["R"] > found["N"]:
            return "R", None
    return "N", "Could not tell Returnable from Non Returnable - set to Non Returnable, please check."


def _split_block(lines, has_name):
    name = lines[0] if (has_name and lines) else ""
    rest = lines[1:] if has_name else list(lines)
    ci = next((i for i, l in enumerate(rest) if COMPANY_RE.search(l)), None)
    if ci is None:
        dept = rest[0] if rest else ""
        company = ""
        address = "\n".join(rest[1:])
    else:
        dept = " ".join(rest[:ci])
        company = rest[ci]
        address = "\n".join(rest[ci + 1:])
    return name, dept, company, address


def _parse_document(doc, type_paragraphs=None):
    """Parse a Document containing exactly one challan."""
    items_tbl = _find_items_table(doc)
    if items_tbl is None:
        raise ParseError("Items table (S.NO / PARTICULARS / QTY ...) not found.")

    # every paragraph in reading order, outside the items table
    paras = []
    for p in doc.element.body.iter(qn("w:p")):
        if _in_fallback(p) or items_tbl._tbl in p.iterancestors():
            continue
        paras.append(p)

    warnings = []
    ctype, warn = _detect_type(paras + list(type_paragraphs or []))
    if warn:
        warnings.append(warn)

    lines = []
    for p in paras:
        for ln in _para_text(p).split("\n"):
            ln = ln.strip()
            if ln and re.search(r"\w", ln):
                lines.append(ln)
    full = "\n".join(lines)

    m = DC_NO_RE.search(full)
    if not m:
        raise ParseError("DC No not found.")
    dc_no = m.group(1).strip()

    m = DC_DATE_RE.search(full)
    if not m:
        raise ParseError("DC Date not found.")
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 100:
        y += 2000
    try:
        dc_date = date(y, mo, d)
    except ValueError:
        raise ParseError(f"Invalid DC Date: {d}.{mo}.{y}")

    # remove header/meta lines so only the From / To text is left
    clean = []
    for ln in lines:
        ln = DC_NO_RE.sub("", ln)
        ln = DC_DATE_RE.sub("", ln).strip()
        up = ln.upper()
        if (not ln or not re.search(r"\w", ln) or "DELIVERY CHALLAN" in up or "GATE PASS" in up
                or "RETURNABLE" in up or ln.lower() == "apex"):
            continue
        clean.append(ln)

    def idx(word, start=0):
        for i in range(start, len(clean)):
            if clean[i].lower().rstrip(":,. ") == word:
                return i
        return None

    fi = idx("from")
    ti = idx("to", (fi or 0) + 1)
    if fi is None or ti is None:
        raise ParseError("'From' / 'To' sections not found.")
    ei = next((i for i in range(ti + 1, len(clean))
               if clean[i].upper().startswith("PLEASE RECEIVE")), len(clean))

    _, f_dept, f_company, f_addr = _split_block(clean[fi + 1:ti], has_name=False)
    t_name, t_dept, t_company, t_addr = _split_block(clean[ti + 1:ei], has_name=True)
    if not t_name:
        t_name = t_company or "-"
        warnings.append("'To' name was empty - please check.")

    # items table
    rows = [[c.text.strip() for c in r.cells] for r in items_tbl.rows]
    hi = next(i for i, r in enumerate(rows) if any("PARTICULAR" in c.upper() for c in r))
    head = [c.upper() for c in rows[hi]]

    def col(keys, default):
        for i, h in enumerate(head):
            if any(k in h for k in keys):
                return i
        return default

    c_part = col(["PARTICULAR", "DESCRIPTION"], 1)
    c_qty = col(["QTY", "QUANTITY"], 2)
    c_uom = col(["UOM", "UNIT"], 3)
    c_rem = col(["REMARK"], 4)

    items = []
    for r in rows[hi + 1:]:
        def cell(i):
            return r[i] if i < len(r) else ""
        part = cell(c_part)
        if not part:
            continue
        q = re.search(r"\d+", cell(c_qty))
        items.append({"particulars": part, "qty": int(q.group()) if q else 1,
                      "uom": cell(c_uom)[:20], "remarks": cell(c_rem)[:200]})
    if not items:
        raise ParseError("No item rows found in the table.")

    return {
        "dc_no": dc_no[:20], "dc_date": dc_date, "challan_type": ctype,
        "from_dept": f_dept[:120], "from_company": (f_company or "")[:160], "from_address": f_addr,
        "to_name": t_name[:120], "to_dept": t_dept[:120], "to_company": t_company[:160],
        "to_address": t_addr, "items": items, "warnings": warnings,
    }


def _open_docx(source):
    try:
        return Document(source)
    except Exception:
        raise ParseError("Cannot open the file - it is not a valid .docx document.")


def parse_docx(source):
    """Read a single-challan .docx (path or file object)."""
    doc = _open_docx(source)
    header_paragraphs = [p._p for section in doc.sections for p in section.header.paragraphs]
    return _parse_document(doc, type_paragraphs=header_paragraphs)


def _split_multi_challan_document(doc):
    """Split a Word document at each top-level paragraph containing a DC No."""
    body = doc.element.body
    children = list(body)
    starts = []
    for i, element in enumerate(children):
        if element.tag == qn("w:p"):
            text = Paragraph(element, doc).text
            if DC_NO_RE.search(text):
                starts.append(i)
    if not starts:
        raise ParseError("DC No not found in the Word document.")

    segments = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(children)
        segment_doc = Document()
        segment_body = segment_doc.element.body
        sect_pr = segment_body.sectPr
        for child in list(segment_body):
            if child is not sect_pr:
                segment_body.remove(child)
        for child in children[start:end]:
            if child is sect_pr:
                continue
            segment_body.insert(len(segment_body) - (1 if segment_body.sectPr is not None else 0), deepcopy(child))
        segments.append(segment_doc)
    return segments


def parse_docx_all(source):
    """Read a DOCX containing one or many challans and return one dict per challan."""
    doc = _open_docx(source)
    segments = _split_multi_challan_document(doc)
    header_paragraphs = [p._p for section in doc.sections for p in section.header.paragraphs]
    parsed = []
    for index, segment in enumerate(segments, 1):
        try:
            parsed.append(_parse_document(segment, type_paragraphs=header_paragraphs))
        except ParseError as exc:
            raise ParseError(f"Challan section {index}: {exc}")
    return parsed


# ---------- saving ----------

def import_files(files, user=None, dry_run=False):
    """Import files; each DOCX may contain one or multiple challans."""
    results = []
    seen = set()  # (DC number, DC year) pairs
    for name, src in files:
        try:
            if str(name).lower().endswith(".doc"):
                raise ParseError("Old .doc format - save it as .docx first (see the guide).")
            challans = parse_docx_all(src)
            for data in challans:
                res = {"file": name, "dc_no": data["dc_no"], "status": "", "message": ""}
                try:
                    dc_no = data["dc_no"]
                    dc_year = data["dc_date"].year
                    identity = (dc_no, dc_year)
                    if identity in seen or DeliveryChallan.objects.filter(dc_no=dc_no, dc_year=dc_year).exists():
                        res.update(status="skipped", message=f"DC No {dc_no} already exists for year {dc_year}.")
                    elif dry_run:
                        seen.add(identity)
                        res.update(status="preview", message=f"{len(data['items'])} item(s), to {data['to_name']}, {data['dc_date']:%d.%m.%Y}. " + " ".join(data["warnings"]))
                    else:
                        items = data.pop("items")
                        warnings = data.pop("warnings")
                        with transaction.atomic():
                            dc = DeliveryChallan.objects.create(created_by=user, **data)
                            DCItem.objects.bulk_create([DCItem(challan=dc, **item) for item in items])
                        seen.add(identity)
                        res.update(status="imported", message=f"{len(items)} item(s). " + " ".join(warnings))
                except Exception as exc:
                    res.update(status="failed", message=f"Unexpected error: {exc}")
                results.append(res)
        except ParseError as exc:
            results.append({"file": name, "dc_no": "", "status": "failed", "message": str(exc)})
        except Exception as exc:
            results.append({"file": name, "dc_no": "", "status": "failed", "message": f"Unexpected error: {exc}"})
    return results


def find_docx_files(folder, recursive=True):
    base = Path(folder)
    pattern = "**/*" if recursive else "*"
    return sorted(p for p in base.glob(pattern)
                  if p.suffix.lower() in (".docx", ".doc") and not p.name.startswith("~$"))
