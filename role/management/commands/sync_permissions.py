import json
import os
from django.core.management.base import BaseCommand
from role.models import Permission
from django.conf import settings


class Command(BaseCommand):
    help = "Syncs permissions from a JSON file."

    def handle(self, *args, **kwargs):
        # Define the path to the JSON file
        json_file_path = os.path.join(settings.BASE_DIR, "permissions.json")

        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f"JSON file not found: {json_file_path}"))
            return

        # Load JSON data
        try:
            with open(json_file_path, "r") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR("Invalid JSON format in permissions file."))
            return

        new_permissions = []
        valid_codenames = set()

        # Process the JSON data
        for model, actions in data.items():
            for action in actions:
                codename = f"{model}::{action.title()}"  # Format: model::action
                name = f"{action.title()} {model.replace('_', ' ').title()}"  # Keep the name as in JSON
                valid_codenames.add(codename)

                # Check if permission already exists
                if not Permission.objects.filter(codename=codename).exists():
                    new_permissions.append(Permission(name=name, codename=codename, model=model))

        # Bulk insert new permissions
        if new_permissions:
            Permission.objects.bulk_create(new_permissions)
            self.stdout.write(self.style.SUCCESS(f"Added {len(new_permissions)} new permissions."))
        else:
            self.stdout.write(self.style.SUCCESS("No new permissions to add."))

        # Remove outdated permissions
        existing_permissions = Permission.objects.all()
        permissions_to_remove = existing_permissions.exclude(codename__in=valid_codenames)
        removed_count = permissions_to_remove.count()

        if removed_count > 0:
            permissions_to_remove.delete()
            self.stdout.write(self.style.SUCCESS(f"Removed {removed_count} outdated permissions."))
        else:
            self.stdout.write(self.style.SUCCESS("No outdated permissions to remove."))
