from datetime import date

from django.conf import settings
from django.db import models


class DeliveryChallan(models.Model):
    RETURNABLE = "R"
    NON_RETURNABLE = "N"
    TYPE_CHOICES = [(RETURNABLE, "Returnable"), (NON_RETURNABLE, "Non Returnable")]

    dc_no = models.CharField("DC No", max_length=20)
    dc_year = models.PositiveSmallIntegerField("DC Year", editable=False, db_index=True)
    dc_date = models.DateField("DC Date", default=date.today)
    challan_type = models.CharField("Type", max_length=1, choices=TYPE_CHOICES,
                                    default=NON_RETURNABLE)

    # "From" block (pre-filled with the company defaults, editable)
    from_dept = models.CharField("Department", max_length=120, blank=True,
                                 default="Information System")
    from_company = models.CharField("Company", max_length=160,
                                    default="Apex laboratories private limited")
    from_address = models.TextField(
        "Address", blank=True,
        default="SIDCO Garment Complex 3rd Floor\nGuindy\nChennai-600032")

    # "To" block
    to_name = models.CharField("Name", max_length=120)
    to_dept = models.CharField("Department", max_length=120, blank=True)
    to_company = models.CharField("Company", max_length=160, blank=True)
    to_address = models.TextField("Address", blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dc_date", "-id"]
        verbose_name = "Delivery Challan"
        constraints = [models.UniqueConstraint(fields=["dc_no", "dc_year"], name="uniq_dc_no_per_year")]

    def save(self, *args, **kwargs):
        self.dc_year = self.dc_date.year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"DC {self.dc_no}/{self.dc_year}"

    @staticmethod
    def next_number():
        nums = [int(n) for n in DeliveryChallan.objects.values_list("dc_no", flat=True)
                if n.isdigit()]
        return f"{(max(nums) if nums else 0) + 1:03d}"


class DCItem(models.Model):
    challan = models.ForeignKey(DeliveryChallan, on_delete=models.CASCADE,
                                related_name="items")
    particulars = models.TextField("Particulars")
    qty = models.PositiveIntegerField("Qty", default=1)
    uom = models.CharField("UOM", max_length=20, default="No", blank=True)
    remarks = models.CharField("Remarks", max_length=200, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.particulars[:40]
