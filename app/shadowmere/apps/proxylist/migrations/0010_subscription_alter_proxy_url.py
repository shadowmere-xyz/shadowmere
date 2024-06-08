# Generated by Django 4.1.7 on 2023-03-04 14:37

from django.db import migrations, models
from utils import validators


class Migration(migrations.Migration):
    dependencies = [
        ("proxylist", "0009_proxy_port"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("url", models.URLField(unique=True)),
                ("kind", models.CharField(choices=[("1", "plain"), ("2", "base64")], default="1", max_length=10)),
            ],
        ),
        migrations.AlterField(
            model_name="proxy",
            name="url",
            field=models.CharField(max_length=1024, unique=True, validators=[validators.proxy_validator]),
        ),
    ]
