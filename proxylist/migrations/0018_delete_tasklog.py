# Generated by Django 5.1 on 2024-08-28 19:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("proxylist", "0017_tasklog_details"),
    ]

    operations = [
        migrations.DeleteModel(
            name="TaskLog",
        ),
    ]