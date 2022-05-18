import os

from django.contrib.auth.models import User
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        if User.objects.count() == 0:
            admin = User.objects.create_superuser(
                email=os.getenv("ADMIN_EMAIL"),
                username=os.getenv("ADMIN_USER"),
                password=os.getenv("ADMIN_PASSWORD"),
            )
            admin.is_active = True
            admin.is_admin = True
            admin.save()
        else:
            print("Admin accounts can only be initialized if no Accounts exist")
