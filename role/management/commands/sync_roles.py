from django.core.management.base import BaseCommand
from role.models import Role, Permission
from utils.permissions import SUPERUSER_PERMISSIONS

# Excluded permissions for Organization Admin

class Command(BaseCommand):
    help = "Sync Super Admin and Organization Admin roles with the latest permissions"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Syncing roles and permissions...")

        # Ensure Super Admin role exists
        super_admin, _ = Role.objects.get_or_create(name="Super Admin", defaults={"description": "Full access to all features except site, camera, and user management"})

        # Get current permissions for Super Admin
        current_super_admin_permissions = set(super_admin.permissions.values_list("codename", flat=True))

        # Add new permissions to Super Admin
        new_permissions = SUPERUSER_PERMISSIONS - current_super_admin_permissions
        if new_permissions:
            super_admin.permissions.add(*Permission.objects.filter(codename__in=new_permissions))
            self.stdout.write(self.style.SUCCESS(f"✔ Added {len(new_permissions)} permissions to Super Admin"))

        # Remove extra permissions
        extra_permissions = current_super_admin_permissions - SUPERUSER_PERMISSIONS
        if extra_permissions:
            super_admin.permissions.remove(*Permission.objects.filter(codename__in=extra_permissions))
            self.stdout.write(self.style.WARNING(f"❌ Removed {len(extra_permissions)} stale permissions from Super Admin"))

        self.stdout.write(self.style.SUCCESS("✅ Super Admin role synced."))


        self.stdout.write(self.style.SUCCESS("🎉 Role synchronization completed!"))
