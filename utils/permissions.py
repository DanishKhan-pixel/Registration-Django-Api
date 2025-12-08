from rest_framework.permissions import BasePermission
from utils.custom_response import Exception_Response_400
from functools import wraps
from rest_framework import status



# Host Permissions
HOST_PERMISSIONS = {
    "site::Read", "site::List",
    "camera::Read", "camera::List"
}

# Non Host Permissions
NON_HOST_PERMISSIONS = {
    "site::Create", "site::Read", "site::Update", "site::Delete", "site::List", "site::Trash", "site::Restore",
    "camera::Create", "camera::Read", "camera::Update", "camera::Delete", "camera::List", "camera::Trash", "camera::Restore"
}

# Superuser Permissions - All permissions except site, camera, and user permissions
SUPERUSER_PERMISSIONS = {

    
    # Role permissions
    "role::Create", "role::Read", "role::Update", "role::Delete", "role::List", "role::Trash", "role::Restore",
    
    # Plan permissions
    "plan::Create", "plan::Read", "plan::Update", "plan::Delete", "plan::List", "plan::Trash", "plan::Restore",
    
    # Subscription permissions
    "subscription::Create", "subscription::Read", "subscription::List",
    
    # Login History permissions
    "login_history::Read", "login_history::List",

    # User Permissions
    "user::Read", "user::Update", "user::Delete"

}

class IsSuperUser(BasePermission):
    """
    Allows access only to superusers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


def check_permission(required_permission):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # Superuser bypasses all permission checks
            if request.user.is_superuser:
                return view_func(self, request, *args, **kwargs)

            # Get user's role and check permissions
            if hasattr(request.user, "employee") and request.user.employee.role:
                user_role = request.user.employee.role
                if user_role.permissions.filter(codename=required_permission).exists():
                    return view_func(self, request, *args, **kwargs)

            return Exception_Response_400("You don't have permission to perform this task")
        return _wrapped_view

    return decorator
