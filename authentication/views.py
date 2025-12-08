from datetime import datetime, timedelta
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.timezone import now
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from .models import LoginHistory, Profile, Token, User
from .serializers import (
    ForgotPasswordRequestSerializer,
    ForgotPasswordResponseSerializer,
    LoginHistorySerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    LogoutResponseSerializer,
    ResetPasswordRequestSerializer,
    TokenSerializer,
    UserSerializer,
)
from utils.custom_pagination import CustomPageNumberPagination
from utils.custom_response import (
    Exception_Response_400,
    Except_Exception_Response_400,
    True_Response_200,
)
from utils.helpers import dynamic_filter, generate_unique_token, send_email
from utils.serializers import InternalServerErrorSerializer, ValidationErrorSerializer



class LoginView(ViewSet):

    @extend_schema(
        operation_id="auth_login",
        summary="Login",
        request=LoginRequestSerializer, 
        description="Authenticate using email/username and password. Returns JWT tokens and user details.",
        tags=["Authentication"],
        responses={
            200: OpenApiResponse(response=LoginResponseSerializer, description="Login successful"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def login(self, request, *args, **kwargs):
        data = request.data
        try:
            identifier = data.get('identifier')
            password = data.get('password')

            if not identifier or not password:
                return Exception_Response_400("Email, username, and password are required.")

            if "@" in identifier:
                user = User.objects.filter(email=identifier).first()
            else:
                user = User.objects.filter(username=identifier).first()

            if not user:
                return Exception_Response_400("Invalid credentials.")

            auth = authenticate(request, username=user.username, password=password)
            if not auth:
                print("Authentication failed.")
                return Exception_Response_400("Invalid credentials.")



            role = user.role.name if user.role else None

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            last_login_entry = LoginHistory.objects.filter(user=user, logout_time__isnull=True).last()
            if last_login_entry:
                last_login_entry.logout_time = now()
                last_login_entry.type = 'token_expire'
                last_login_entry.save()

            LoginHistory.objects.create(user=user)

            response = {
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token
                },
                "user_id": user.id,
                "is_superuser": user.is_superuser,
                "token_type": "bearer",
                "role": role,

            }
            return True_Response_200(message="Login successfully", data=response)
        except Exception as e:
            return Except_Exception_Response_400(e)


class ProfileView(ViewSet):

    @extend_schema(
        operation_id="profile_retrieve",
        summary="Get user profile",
        description="Retrieve a user's profile, including organization and permissions.",
        tags=["Profile"],       
        responses={
            200: OpenApiResponse(response= UserSerializer, description="Profile retrieved successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def retrieve(self, request, id, *args, **kwargs):
        try:
            if not id:
                return Exception_Response_400("User ID is required")

            user = User.objects.filter(id=id, is_active=True).first()
            if not user:
                return Exception_Response_400("User does not exist or is not active")

            serializer = UserSerializer(user)

            # Fetch additional details separately (not in serializer)
            permissions = list(user.role.permissions.values("id", "name", "codename", "model")) if user.role else []
            # role = user.role.name if user.role else None


            # Construct the response manually
            response_data = serializer.data
            # response_data["organization"] = organization_id
            response_data["permissions"] = permissions
            # response_data["role"] = role

            return True_Response_200(message="User profile retrieved successfully", data=response_data)

        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="profile_update",
        summary="Update user profile",
        description="Partially update a user's profile.",
        tags=["Profile"],
        responses={
            200: OpenApiResponse(response=UserSerializer, description="Profile updated successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def update(self, request, id, *args, **kwargs):
        try:
            if not id:
                return Exception_Response_400("User ID id required")
            user = User.objects.filter(id=id, is_active=True).first()
            if not user:
                return Exception_Response_400("User not exist or not active")
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return True_Response_200(message="User update successfully", data=serializer.data)
        except Exception as e:
            Except_Exception_Response_400(e)



class LogoutView(ViewSet):
    @extend_schema(
        operation_id="auth_logout",
        summary="Logout",
        description="Logs out the current session by closing the last open login history entry.",
        tags=["Authentication"],
        responses={
            200: OpenApiResponse(response=LogoutResponseSerializer, description="Logout successful"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def logout(self, request, *args, **kwargs):
        try:
            user_id = self.kwargs.get('user_id')
            if not user_id:
                return Exception_Response_400("User id is required.")
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Exception_Response_400("User not found.")
            last_login_entry = LoginHistory.objects.filter(user=user, logout_time__isnull=True).last()
            if last_login_entry:
                last_login_entry.logout_time = now()
                last_login_entry.type = 'hard_logout'
                last_login_entry.save()
                return True_Response_200("Logout successfully", [])
            # Idempotent response when there is no active session
            return True_Response_200("No active session. Already logged out.", [])
        except Exception as e:
                return Except_Exception_Response_400(e)


class LoginHistoryView(ViewSet):
    serializer_class = LoginHistorySerializer

    def get_queryset(self):
        return LoginHistory.objects.select_related('user')

    @extend_schema(
        operation_id="login_history_list",
        summary="List login history",
        description="List login history entries , search and sorting.",
        tags=["Login History"],
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, required=False, description="Search by username"),
            OpenApiParameter(name="sort", type=OpenApiTypes.STR, required=False, description="Sort field (e.g., -created_at)"),
        ],
        responses={
            200: OpenApiResponse(response=LoginHistorySerializer, description="Login history list"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def list(self, request, *args, **kwargs):
        try:
            filters = request.query_params.dict()
            search_query = request.query_params.get('search')
            sort = request.query_params.get('sort')
            data = dynamic_filter(
                LoginHistory,
                search_fields=['user__username'],
                search_query=search_query,
                sort_by=sort,
                **filters
            )

            paginator = CustomPageNumberPagination()
            paginated_result = paginator.paginate_queryset(data, request)
            serializer = self.serializer_class(paginated_result, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="login_history_user",
        summary="User's login history",
        description="Retrieve paginated login history for a specific user.",
        tags=["Login History"],
        responses={
            200: OpenApiResponse(response=LoginHistorySerializer, description="Paginated login history list for user"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            user_id = self.kwargs.get('user_id')
            if not user_id:
                return Exception_Response_400("User id is required.")
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Exception_Response_400("User not found.")
            data = self.get_queryset().filter(user=user, is_deleted=False)
            paginator = CustomPageNumberPagination()
            paginated_result = paginator.paginate_queryset(data, request)
            
            serializer = self.serializer_class(paginated_result, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)


class ForgotPasswordView(ViewSet):
    serializer_class = TokenSerializer

    @extend_schema(
        operation_id="auth_forgot_password",
        summary="Forgot password",
        request=ForgotPasswordRequestSerializer,
        description="Initiate password reset by sending OTP to user's email.",
        tags=["Authentication"],
        responses={
            200: OpenApiResponse(response=ForgotPasswordResponseSerializer, description="OTP sent to email"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def forgot_password(self, request, *args, **kwargs):
        try:
            data = request.data
            identifier = data.get('identifier')

            if not identifier:
                return Exception_Response_400("Provide a email or username.")

            if "@" in identifier:
                user = User.objects.filter(email=identifier).first()
            else:
                user = User.objects.filter(username=identifier).first()
            if not user:
                return Exception_Response_400("Invalid email or username.")

            token = Token.objects.filter(user=user).first()
            # if token and now() < token.expires:
            #     return True_Response_200("An OTP already sent to your email.", [])

            if token:
                token.delete()

            otp = generate_unique_token(alpha_count=4, digit_count=2)

            data = {
                'user': user.id,
                'code': otp,
                'expires': datetime.now() + timedelta(days=1),
                'type': "forgot_password",
            }

            # email details
            subject = "Password Reset Request - Pulsse"
            body = f"""
Hello {user.first_name},

We received a request to reset your password for your Pulsse account.

Your One-Time Password (OTP) is: {otp}

This OTP will expire in 24 hours.

If you didn't request this password reset, please ignore this email or contact support if you have concerns.

Best regards,
Pulsse Team
            """

            serializer = self.serializer_class(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            send_email(subject=subject, body=body, emails=[user.email])
            return True_Response_200("An OTP sent to your email", [])
        except Exception as e:
            return Except_Exception_Response_400(e)


class ResetPasswordView(ViewSet):

    @extend_schema(
        operation_id="auth_reset_password",
        summary="Reset password",
        request=ResetPasswordRequestSerializer,
        description="Reset password using the OTP code received via email.",
        tags=["Authentication"],
        responses={
            200: OpenApiResponse(description="Password reset successful"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def reset_password(self, request, *args, **kwargs):
        try:
            data = request.data
            unique_code = data.get('code')
            password = data.get('password')

            if not unique_code or not password:
                return Exception_Response_400("Provide your unique code and new password.")

            token = Token.objects.filter(code=unique_code).first()
            if not token:
                return Exception_Response_400("Invalid reset code.")

            if token.expires < now():
                return Exception_Response_400("Your OTP has been expired. Please request a new one.")

            user = User.objects.filter(email=token.user.email).first()
            if not user:
                return Exception_Response_400("User not found.")

            # Validate password strength
            try:
                validate_password(password, user)
            except Exception as e:
                return Exception_Response_400(f"Password error: {', '.join(e)}")

            # Ensure atomicity
            with transaction.atomic():
                user.set_password(password)
                user.save()
                token.delete()

            return True_Response_200("Your password has been successfully changed.", [])

        except Exception as e:
            return Except_Exception_Response_400(e)



class HealthCheckView(APIView):

    @extend_schema(
        operation_id="health_check",
        summary="Health check",
        description="Returns 204 if the service is healthy.",
        tags=["Health"],
        responses={204: OpenApiResponse(description="No Content")},
    )
    def get(self, request, *args, **kwargs):
            return Response(status=status.HTTP_204_NO_CONTENT)
