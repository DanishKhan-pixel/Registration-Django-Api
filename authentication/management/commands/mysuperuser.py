from django.core.management.base import BaseCommand
from authentication.models import User
from role.models import Role
import os

class Command(BaseCommand):
    def handle(self, *args, **options):
        print("------------------------test-1--------------")
        role = Role.objects.filter(name="Super Admin").first()
        if not User.objects.filter(email='superadmin@pulsse.io').exists():
            try:
                if not User.objects.filter(email="superadmin@pulsse.io").exists():
                    user = User.objects.create_superuser(username='super_admin',email="superadmin@pulsse.io", password=')56u@10/^Z£s', is_active=True, role=role)
                    user.set_password(')56u@10/^Z£s')
                    user.save()
                    print("superuser created")

            except Exception as e:
                print(e)
                pass
