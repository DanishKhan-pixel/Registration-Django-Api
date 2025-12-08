from accounts.models import User
from accounts.serializers import UserSerializer
from utils.custom_response import *
from django.core.exceptions import ValidationError


class BaseUserMixin:

    """
    Mixin to handle user creation and update logic.
    """
    user_serializer_class = UserSerializer
    RESTRICTED_FIELDS = {'email', 'username', 'password', 'is_superuser', 'is_staff'}

    from rest_framework.exceptions import ValidationError

    def create_user(self, data):
        try:
            email = data.get("email")
            username = data.get("username")
            password = data.get("password")

            if not email or not username or not password:
                return None, Exception_Response_400("Email, username, and password are required.")

            if User.objects.filter(email=email).exists():
                return None, Exception_Response_400("A user with this email already exists.")

            if User.objects.filter(username=username).exists():
                return None, Exception_Response_400("A user with this username already exists.")

            # Create the user instance and run the validations
            user_serializer = self.user_serializer_class(data=data)
            if not user_serializer.is_valid():
                error_messages = " ".join(
                    [f"{field}: {', '.join(errors)}" for field, errors in user_serializer.errors.items()]
                )
                return None, Exception_Response_400(error_messages)

            user = user_serializer.save()

            # Validate password and set it
            user.set_password(password)
            user.save()

            return user, None
        except ValidationError as e:
            return None, Exception_Response_400(f"Validation failed: {str(e)}")  # Handle validation error
        except Exception as e:
            return Except_Exception_Response_400(e)

    def update_user(self, user, data):
        try:
            for field in self.RESTRICTED_FIELDS:
                data.pop(field, None)  # Prevent updating restricted fields

            user_serializer = self.user_serializer_class(user, data=data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

            return user_serializer.data
        except Exception as e:
            return Except_Exception_Response_400(e)

