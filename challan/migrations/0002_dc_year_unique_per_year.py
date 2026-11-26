from django.db import migrations, models


def populate_dc_year(apps, schema_editor):
    DeliveryChallan = apps.get_model('challan', 'DeliveryChallan')
    for record in DeliveryChallan.objects.all().only('id', 'dc_date').iterator():
        DeliveryChallan.objects.filter(pk=record.pk).update(dc_year=record.dc_date.year)


class Migration(migrations.Migration):
    dependencies = [('challan', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='deliverychallan',
            name='dc_year',
            field=models.PositiveSmallIntegerField(db_index=True, editable=False, null=True, verbose_name='DC Year'),
        ),
        migrations.RunPython(populate_dc_year, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='deliverychallan',
            name='dc_no',
            field=models.CharField(max_length=20, verbose_name='DC No'),
        ),
        migrations.AlterField(
            model_name='deliverychallan',
            name='dc_year',
            field=models.PositiveSmallIntegerField(db_index=True, editable=False, verbose_name='DC Year'),
        ),
        migrations.AddConstraint(
            model_name='deliverychallan',
            constraint=models.UniqueConstraint(fields=('dc_no', 'dc_year'), name='uniq_dc_no_per_year'),
        ),
    ]
