from django.contrib import admin

from .models import DCItem, DeliveryChallan


class ItemInline(admin.TabularInline):
    model = DCItem
    extra = 0


@admin.register(DeliveryChallan)
class DeliveryChallanAdmin(admin.ModelAdmin):
    list_display = ("dc_no", "dc_date", "challan_type", "to_name", "created_by")
    search_fields = ("dc_no", "to_name", "to_company")
    inlines = [ItemInline]
