# Generated by Django 3.1.5 on 2021-03-11 23:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proxy", "0002_auto_20201122_0831"),
    ]

    operations = [
        migrations.AddField(
            model_name="relaynode",
            name="remark",
            field=models.CharField(default="", max_length=64, verbose_name="备注"),
        ),
    ]
