from django import forms
from django.forms import inlineformset_factory

from .models import DCItem, DeliveryChallan


class ChallanForm(forms.ModelForm):
    class Meta:
        model = DeliveryChallan
        fields = ["dc_no", "dc_date", "challan_type",
                  "from_dept", "from_company", "from_address",
                  "to_name", "to_dept", "to_company", "to_address"]
        widgets = {
            "dc_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "challan_type": forms.RadioSelect,
            "from_address": forms.Textarea(attrs={"rows": 3}),
            "to_address": forms.Textarea(attrs={"rows": 3}),
        }


def make_item_formset(extra=1):
    return inlineformset_factory(
        DeliveryChallan, DCItem,
        fields=["particulars", "qty", "uom", "remarks"],
        extra=extra, can_delete=True,
        widgets={
            "particulars": forms.Textarea(attrs={"rows": 2, "placeholder": "Item description"}),
            "qty": forms.NumberInput(attrs={"min": 1}),
            "uom": forms.TextInput(),
            "remarks": forms.TextInput(),
        },
    )
