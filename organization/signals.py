from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from role.models import Permission
from organization.models import Organization
from role.models import Role
from utils.permissions import HOST_PERMISSIONS, NON_HOST_PERMISSIONS
from utils.http_service import update_ezviz_config
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Organization)
def create_default_roles(sender, instance, created, **kwargs):
    """ Signal to create Host and Non Host roles when an organization is created. """
    if created:
        all_permissions = Permission.objects.all().values_list('codename', flat=True)
        print(list(all_permissions))
        # Create Host role
        host_role = Role.objects.create(
            name="Host",
            organization=instance,
            description="Limited access: can only read and list sites & cameras",
        )

        # Create Non Host role
        non_host_role = Role.objects.create(
            name="Non Host",
            organization=instance,
            description="Full access to manage sites & cameras",
        )

        # Assign permissions to Host
        host_permissions = Permission.objects.filter(codename__in=list(HOST_PERMISSIONS))
        host_role.permissions.set(host_permissions)

        # Assign permissions to Non Host (use full names)
        non_host_permissions = Permission.objects.filter(codename__in=list(NON_HOST_PERMISSIONS))
        non_host_role.permissions.set(non_host_permissions)

        print(f"Roles created for Organization {instance.name}: Host & Non Host")

@receiver(pre_save, sender=Organization)
def handle_organization_save(sender, instance, **kwargs):
    """
    Signal handler for organization creation and updates
    Only triggers ML API call when:
    1. Organization is newly created
    2. api_key or secret_key fields are updated
    """
    try:
        # For new organizations
        if not instance.pk:
            if instance.api_key and instance.secret_key:
                success, response = update_ezviz_config(
                    ezv_key=instance.api_key,
                    ezv_secret=instance.secret_key
                )
                
                if not success:
                    logger.error(f"Failed to update EZVIZ config for new organization: {response}")
                else:
                    logger.info(f"Successfully updated EZVIZ config for new organization")
            return

        # For existing organizations, check if api_key or secret_key changed
        try:
            old_instance = Organization.objects.get(pk=instance.pk)
            if (old_instance.api_key != instance.api_key or 
                old_instance.secret_key != instance.secret_key):
                
                if instance.api_key and instance.secret_key:
                    success, response = update_ezviz_config(
                        ezv_key=instance.api_key,
                        ezv_secret=instance.secret_key
                    )
                    
                    if not success:
                        logger.error(f"Failed to update EZVIZ config for organization {instance.id}: {response}")
                    else:
                        logger.info(f"Successfully updated EZVIZ config for organization {instance.id}")
                else:
                    logger.warning(f"Organization {instance.id} has missing API credentials")
        except Organization.DoesNotExist:
            pass

    except Exception as e:
        logger.error(f"Error in handle_organization_save: {str(e)}")
