from django.db import transaction
from rest_framework.viewsets import ViewSet
from authentication.serializers import UserSerializer, ProfileSerializer
from organization.models import Organization
from organization.serializers import OrganizationSerializer
from utils.custom_response import True_Response_200, Except_Exception_Response_400, Created_Response_201, Exception_Response_400
from authentication.models import User, Media, Profile
from utils.custom_pagination import CustomPageNumberPagination
from role.models import Role
from django.contrib.contenttypes.models import ContentType
from .helpers import check_users_limit
from utils.helpers import dynamic_filter
from utils.microservices.subscriptions import get_active_subscriptions
from django.core.validators import validate_ipv46_address
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
)
from utils.serializers import ValidationErrorSerializer, InternalServerErrorSerializer
from .serializers import (
    OrganizationResponseSerializer,
    OrganizationCreateRequestSerializer,
    OrganizationUpdateRequestSerializer,
    BulkStatusUpdateRequestSerializer,
    UpdateResponseSerializer,
    OrganizationUserResponseSerializer,
    OrganizationUserStatsResponseSerializer,
    ResultsResponseSerializer,
    EmptyResultsResponseSerializer,
    DeleteResponseSerializer,
    OrganizationRequestSerializer,
    UserStatusUpdateRequestSerializer,
    OrganizationUserRequestSerializer
)


class OrganizationView(ViewSet):
    model = Organization
    organization_serializer_class = OrganizationSerializer
    user_serializer_class = UserSerializer
    profile_serializer_class = ProfileSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return Organization.objects.all()

    @extend_schema(
        operation_id="organization_create",
        summary="Create organization",
        description="Create an organization and admin user, returning the organization data.",
        tags=["Organization"],
        request=OrganizationCreateRequestSerializer,
        responses={
            200: OpenApiResponse(response=OrganizationResponseSerializer, description="Organization created successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def create(self, request, *args, **kwargs):
        try:
            # create admin user for organization
            role = Role.objects.filter(name="Organization Admin").first()
            if not role:
                return Except_Exception_Response_400("Something went wrong with organization admin permissions.")
            data = request.data
            # Pre-validate IP to avoid DB errors inside transaction
            ip_value = data.get("ip")
            if ip_value not in (None, ""):
                try:
                    validate_ipv46_address(ip_value)
                except DjangoValidationError:
                    return Except_Exception_Response_400("Validation error", {"ip": ["Enter a valid IPv4 or IPv6 address."]})
            with transaction.atomic():
                savepoint = transaction.savepoint()
                user_data = {
                    "email": data["email"],
                    "username": data["username"],
                    "password": data["password"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": role.id,
                    "gender": data["gender"],
                    "is_active": data["status"],
                    "contact": data["contact"],
                    "country_code": data.get("country_code", "+1"),
                }
                user_serializer = self.user_serializer_class(data=user_data)
                user_serializer.is_valid(raise_exception=True)
                user = user_serializer.save()

                # create organization
                organization_data = {
                    "user": user.id,
                    "name": data["name"],
                    "contact": data["contact"],
                    "country": data["country"],
                    "address": data["address"],
                    "status": data["status"],
                    "ip": data.get("ip") or None,
                    "ssh_key": data.get("ssh_key") or None,
                    "validation_frequency": data["validation_frequency"],
                    "api_key": data.get("api_key"),
                    "secret_key": data.get("secret_key"),
                }

                org_serializer = self.organization_serializer_class(data=organization_data)
                org_serializer.is_valid(raise_exception=True)
                organization = org_serializer.save()

                #create admin user profile
                profile_data = {
                    "user": user.id,
                    "organization": organization.id,
                }
                profile_serializer = self.profile_serializer_class(data=profile_data)
                profile_serializer.is_valid(raise_exception=True)
                profile_serializer.save()

                return True_Response_200("Organization created successfully", org_serializer.data)
        except Exception as e:
            print(e)
            transaction.savepoint_rollback(savepoint)
            return Except_Exception_Response_400(e, user_serializer.errors if user_serializer.errors else org_serializer.errors)

    @extend_schema(
        operation_id="organization_retrieve",
        summary="Retrieve organization",
        description="Get a single organization by ID.",
        tags=["Organization"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        responses={
            200: OpenApiResponse(response=OrganizationResponseSerializer, description="Organization retrieved"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def retrieve(self, request, id, *args, **kwargs):
        try:
            organization = self.get_queryset().filter(id=id).first()
            if not organization:
                return Exception_Response_400("Organization not found.")
            serializer = self.organization_serializer_class(organization)
            return True_Response_200("Organization retrieved successfully", serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_list",
        summary="List organizations",
        description="List organizations with pagination, search and sorting.",
        tags=["Organization"],
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Search by name"),
            OpenApiParameter(name="sort", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Sort by name"),
        ],
        responses={
            200: OpenApiResponse(description="Paginated organization list"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def list(self, request, *args, **kwargs):
        try:
            filters = request.query_params.dict()
            search = request.query_params.get("search")
            sort = request.query_params.get("sort")
            data = dynamic_filter(self.model, search_fields=["name"], search_query=search, sort_by=sort, **filters)
            if not data.exists():
                return True_Response_200("No data found", [])

            paginator = self.pagination_class()
            paginated_result = paginator.paginate_queryset(data, request)
            serializer = self.organization_serializer_class(paginated_result, many=True)
            
            # Get organization IDs from the paginated results
            org_ids = [org['id'] for org in serializer.data]
            
            # Fetch subscription data
            subscriptions = get_active_subscriptions(org_ids)
            
            # Add subscription data to each organization
            for org in serializer.data:
                org_id = org['id']
                if org_id in subscriptions:
                    org['plan_name'] = subscriptions[org_id]['plan_name']
                    org['expiry_date'] = subscriptions[org_id]['expiry_date']
                else:
                    org['plan_name'] = None
                    org['expiry_date'] = None
            
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_update",
        summary="Update organization",
        description="Partially update an organization by ID.",
        tags=["Organization"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        request=OrganizationUpdateRequestSerializer,
        responses={
            200: OpenApiResponse(response=OrganizationResponseSerializer, description="Organization updated"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def update(self, request, id, *args, **kwargs):
        try:
            organization = self.get_queryset().filter(id=id).first()
            if not organization:
                return Exception_Response_400("Organization not found.")

            # Pre-validate IP to avoid DB errors inside transaction
            ip_value = request.data.get("ip")
            if ip_value not in (None, ""):
                try:
                    validate_ipv46_address(ip_value)
                except DjangoValidationError:
                    return Except_Exception_Response_400("Validation error", {"ip": ["Enter a valid IPv4 or IPv6 address."]})

            with transaction.atomic():
                savepoint = transaction.savepoint()
                try:
                    # Update organization admin user
                    user = organization.user
                    user_data = {
                        "email": request.data.get("email", user.email),
                        "username": request.data.get("username", user.username),
                        "gender": request.data.get("gender", user.gender),
                        "first_name": request.data.get("first_name", user.first_name),
                        "last_name": request.data.get("last_name", user.last_name),
                        "contact": request.data.get("contact", user.contact),
                        "country_code": request.data.get("country_code", user.country_code),
                    }

                    # Update password if provided
                    if "password" in request.data:
                        user_data["password"] = request.data["password"]

                    user_serializer = self.user_serializer_class(user, data=user_data, partial=True)
                    user_serializer.is_valid(raise_exception=True)
                    user = user_serializer.save()

                    # Update organization

                    # Normalize optional fields and only update if explicitly provided
                    ssh_key_provided = "ssh_key" in request.data
                    ssh_key_value = request.data.get("ssh_key") if ssh_key_provided else None
                    if ssh_key_provided and ssh_key_value == "":
                        ssh_key_value = None

                    ip_provided = "ip" in request.data
                    ip_value = request.data.get("ip") if ip_provided else None
                    if ip_provided and ip_value == "":
                        ip_value = None

                    organization_data = {
                        "name": request.data.get("name", organization.name),
                        "contact": request.data.get("contact", organization.contact),
                        "country": request.data.get("country", organization.country),
                        "address": request.data.get("address", organization.address),
                        "status": request.data.get("status", organization.status),
                        "ip": organization.ip,
                        "validation_frequency": request.data.get("validation_frequency", organization.validation_frequency),
                        "api_key": request.data.get("api_key", organization.api_key),
                        "secret_key": request.data.get("secret_key", organization.secret_key),
                    }

                    # Conditionally apply updates for ssh_key and ip
                    if ssh_key_provided:
                        organization_data["ssh_key"] = ssh_key_value

                    if ip_provided:
                        organization_data["ip"] = ip_value

                    org_serializer = self.organization_serializer_class(organization, data=organization_data, partial=True)
                    org_serializer.is_valid(raise_exception=True)
                    organization = org_serializer.save()

                    return True_Response_200("Organization updated successfully", org_serializer.data)
                except Exception as e:
                    transaction.savepoint_rollback(savepoint)
                    return Except_Exception_Response_400(e, user_serializer.errors if user_serializer.errors else org_serializer.errors)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_delete",
        summary="Delete organizations",
        description="Soft delete multiple organizations by IDs.",
        tags=["Organization"],
        request=UpdateResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="ids",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="IDs to delete. Repeat param: ids=1&ids=2",
                many=True,
            ),
        ],
        responses={
            200: OpenApiResponse(response=DeleteResponseSerializer, description="Organizations deleted"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def destroy(self, request, *args, **kwargs):
        try:
            # Get list of IDs from request data
            ids = request.data.get('ids')
            if not ids:
                ids = request.query_params.getlist('ids')
            if not ids:
                return Exception_Response_400('No organization IDs provided for deletion.')

            # Get organizations
            organizations = self.get_queryset().filter(id__in=ids, is_deleted=False)
            
            if not organizations.exists():
                return Exception_Response_400('No valid organizations found for deletion.')

            # Soft delete all organizations
            for organization in organizations:
                organization.soft_delete()

            return True_Response_200('Organizations deleted successfully', [])
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_trash_list",
        summary="List trashed organizations",
        description="List soft-deleted organizations with pagination.",
        tags=["Organization"],
        responses={
            200: OpenApiResponse(description="Paginated trashed organization list"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def trash(self, request, *args, **kwargs):
        try:
            filters = request.query_params.dict()
            search = request.query_params.get("search")
            sort = request.query_params.get("sort")
            data = dynamic_filter(self.model, search_fields=["name"], search_query=search, sort_by=sort, is_trash=True, **filters)
            if not data.exists():
                return True_Response_200("No data found", [])

            paginator = self.pagination_class()
            paginated_result = paginator.paginate_queryset(data, request)
            serializer = self.organization_serializer_class(paginated_result, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_restore",
        summary="Restore organizations",
        description="Restore multiple soft-deleted organizations by IDs.",
        tags=["Organization"],
        request=OrganizationRequestSerializer,
        responses={
            200: OpenApiResponse(response=UpdateResponseSerializer, description="Organizations restored"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def restore(self, request, *args, **kwargs):
        try:
            # Get list of IDs from request data
            ids = request.data.get('ids', [])
            if not ids:
                return Exception_Response_400('No organization IDs provided for restoration.')

            # Get organizations
            organizations = self.get_queryset().filter(id__in=ids, is_deleted=True)
            
            if not organizations.exists():
                return Exception_Response_400('No valid organizations found for restoration.')

            # Restore all organizations
            for organization in organizations:
                organization.restore()

            return True_Response_200('Organizations restored successfully', [])
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_status_update",
        summary="Update organizations status",
        description="Bulk update status for multiple organizations.",
        tags=["Organization"],
        request=BulkStatusUpdateRequestSerializer,
        responses={
            200: OpenApiResponse(response=ResultsResponseSerializer, description="Organizations status updated"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def status_update(self, request, *args, **kwargs):
        try:
            # Get status and IDs from request data
            status = request.data.get('status')
            ids = request.data.get('ids', [])
            
            if status is None:
                return Exception_Response_400('Status is required.')
            
            if not ids:
                return Exception_Response_400('No organization IDs provided for status update.')

            # Get organizations
            organizations = self.get_queryset().filter(id__in=ids, is_deleted=False)
            
            if not organizations.exists():
                return Exception_Response_400('No valid organizations found for status update.')

            # Update status for all organizations
            organizations.update(status=status)

            return True_Response_200('Organizations status updated successfully', [])
        except Exception as e:
            return Except_Exception_Response_400(e)


class OrganizationUserView(ViewSet):
    user_serializer_class = UserSerializer
    profile_serializer_class = ProfileSerializer
    model = User

    def get_queryset(self, org_id):
        print('Getting queryset for org_id:', org_id)
        queryset = User.objects.filter(profile__organization_id=org_id)
        print('Found users:', queryset.values('id', 'username', 'profile__organization_id'))
        return queryset

    @extend_schema(
        operation_id="organization_user_create",
        summary="Create organization user",
        description="Create a sub-user under the specified organization.",
        tags=["Organization Sub User"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        request=UserSerializer,
        responses={
            201: OpenApiResponse(response=OrganizationUserResponseSerializer, description="User created successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def create(self, request, org_id, *args, **kwargs):
        try:
            if not org_id:
                return Exception_Response_400('Organization ID is required.')

            organization = Organization.objects.filter(id=org_id).first()
            if not organization:
                return Exception_Response_400('Organization not found.')

            # Collect custom validation errors (e.g. names)
            errors_map = {}
            for field_name in ["first_name", "last_name"]:
                value = request.data.get(field_name)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    errors_map[field_name] = ["This field may not be blank."]

            # Validate role field (collect errors instead of early return)
            role_error = None
            role_obj = None
            role_id = request.data.get('role')
            if not role_id or role_id == '':
                role_error = 'Role is required.'
            else:
                try:
                    role_id_int = int(role_id)
                    role_obj = Role.objects.filter(id=role_id_int, organization=organization).first()
                    if not role_obj:
                        role_error = 'Role not found.'
                except (ValueError, TypeError):
                    role_error = 'Role must be a valid number.'

            # limit_check = check_users_limit(org_id)
            # if limit_check is not True:
            #     return Exception_Response_400("Error getting organization subscription plan")

            try:
                with transaction.atomic():
                    savepoint = transaction.savepoint()
                    # create user
                    user_data = {
                        "email": request.data['email'],
                        "username": request.data['username'],
                        "password": request.data['password'],
                        "first_name": request.data.get('first_name'),
                        "last_name": request.data.get('last_name'),
                        "gender": request.data['gender'],
                        "contact": request.data['contact'],
                        "country_code": request.data.get('country_code', '+1'),
                        # "is_active": request.data['is_active'],

                    }

                    # Only include role if it is valid; otherwise, we will attach a custom role error below
                    if role_obj:
                        user_data['role'] = role_obj.id

                    # Special handling for Host role
                    if role_obj and role_obj.name == "Host":
                        user_data['is_active'] = False
                        user_data['status'] = False

                    user_serializer = self.user_serializer_class(data=user_data)

                    # Validate without raising, so we can merge custom errors into the error map
                    if not user_serializer.is_valid():
                        serializer_errors = dict(user_serializer.errors)
                        if role_error:
                            errors_map['role'] = [role_error]
                        # Merge collected errors without overwriting existing keys
                        for key, value in errors_map.items():
                            if key not in serializer_errors:
                                serializer_errors[key] = value
                        return Except_Exception_Response_400("Validation error", serializer_errors)

                    # If serializer is valid but we still have collected errors, return them
                    if errors_map or role_error:
                        merged = dict(errors_map)
                        if role_error:
                            merged['role'] = [role_error]
                        return Except_Exception_Response_400("Validation error", merged)

                    user = user_serializer.save()

                    # create user profile
                    profile_data = {
                        "user": user.id,
                        "organization": organization.id,
                    }
                    profile_serializer = self.profile_serializer_class(data=profile_data)
                    profile_serializer.is_valid(raise_exception=True)
                    profile = profile_serializer.save()

                    # create profile image object
                    image = request.data.get('image', None)
                    if image:
                        Media.objects.create(
                            content_type=ContentType.objects.get_for_model(User),
                            object_id=user.id,
                            media_type="image",
                            file=image
                        )
                    return Created_Response_201('User created successfully', user_serializer.data)
            except Exception as e:
                transaction.savepoint_rollback(savepoint)
                print(e)
                return Except_Exception_Response_400(e, user_serializer.errors)
        except Exception as e:
            return Except_Exception_Response_400(e)


    @extend_schema(
        operation_id="organization_user_list",
        summary="List organization users",
        description="List users for an organization with pagination, search, and sorting.",
        tags=["Organization Sub User"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        responses={
            200: OpenApiResponse(response=OrganizationUserResponseSerializer, description="Paginated user list"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def list(self, request, org_id, *args, **kwargs):
        try:
            # Get filters from query params and add organization filter
            filters = request.query_params.dict()
            filters['profile__organization'] = org_id
            # Apply dynamic filters and search
            search_query = request.query_params.get('search')
            sort = request.query_params.get("sort")
            data = dynamic_filter(self.model, search_fields=["first_name", "last_name", "username", "email", "full_name"], search_query=search_query, sort_by=sort, **filters)
            
            if not data.exists():
                return True_Response_200("No data found", [])

            paginator = CustomPageNumberPagination()
            paginated_result = paginator.paginate_queryset(data, request)
            serializer = self.user_serializer_class(paginated_result, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_user_stats",
        summary="Get organization user counts",
        description="Returns counts of all/active/inactive/trash users for an organization.",
        tags=["Organization Sub User"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        responses={
            200: OpenApiResponse(response=OrganizationUserStatsResponseSerializer, description="User counts"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def all_users(self, request, org_id, *args, **kwargs):
        try:
            users = self.get_queryset(org_id)
            active_users = users.filter(is_active=True, status=True)
            un_active_users = users.filter(is_active=False, status=False, is_deleted=False)
            trash_users = users.filter(is_deleted=True)

            response = {
                "all_users": users.count() - 1,
                "active_users": active_users.count() - 1,
                "un_active_users": un_active_users.count(),
                "trash_users": trash_users.count(),
            }
            return True_Response_200("All users retrieved successfully", response)
        except Exception as e:
            return Except_Exception_Response_400(e)


    @extend_schema(
        operation_id="organization_user_retrieve",
        summary="Retrieve organization user",
        description="Get a single user by ID in the given organization.",
        tags=["Organization Sub User"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="User ID"),
        ],
        responses={
            200: OpenApiResponse(response=OrganizationUserResponseSerializer, description="User retrieved"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def retrieve(self, request, org_id, id, *args, **kwargs):
        try:
            user = self.get_queryset(org_id).filter(id=id, is_deleted=False).first()
            if not user:
                return Exception_Response_400('User not found.')
            serializer = self.user_serializer_class(user)
            return True_Response_200('User retrieved successfully', serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_user_update",
        summary="Update organization user",
        description="Partially update a user by ID in the given organization.",
        tags=["Organization Sub User"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="User ID"),
        ],
        request=UserSerializer,
        responses={
            200: OpenApiResponse(response=OrganizationUserResponseSerializer, description="User updated"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def update(self, request, org_id, id, *args, **kwargs):
        try:
            if not org_id:
                return Exception_Response_400('Organization ID is required.')

            if not id:
                return Exception_Response_400('User ID is required.')

            organization = Organization.objects.filter(id=org_id).first()
            if not organization:
                return Exception_Response_400('Organization not found.')

            user = User.objects.filter(id=id).first()
            if not user:
                return Exception_Response_400('User not found.')

            with transaction.atomic():
                savepoint = transaction.savepoint()

                # Update user fields
                user_data = {
                    "email": request.data.get('email', user.email),
                    "username": request.data.get('username', user.username),
                    "first_name": request.data.get('first_name', user.first_name),
                    "last_name": request.data.get('last_name', user.last_name),
                    "gender": request.data.get('gender', user.gender),
                    "contact": request.data.get('contact', user.contact),
                    "country_code": request.data.get('country_code', user.country_code),
                    "is_active": request.data.get('is_active', user.is_active),
                    "status": request.data.get('status', user.status),
                }

                if "password" in request.data:
                    user_data["password"] = request.data["password"]

                # Update role if provided
                role_id = request.data.get('role')
                if role_id:
                    role = Role.objects.filter(id=role_id).first()
                    if not role:
                        return Exception_Response_400('Role not found.')
                    user_data["role"] = role.id

                user_serializer = self.user_serializer_class(user, data=user_data, partial=True)
                user_serializer.is_valid(raise_exception=True)
                user = user_serializer.save()

                # Update profile
                # profile = Profile.objects.filter(user=user, organization=organization).first()
                # if not profile:
                #     return Exception_Response_400('User profile not found.')
                #
                # profile_serializer = self.profile_serializer_class(profile, data=request.data, partial=True)
                # profile_serializer.is_valid(raise_exception=True)
                # profile_serializer.save()

                # Update profile image if provided
                image = request.data.get('image')
                if image:
                    media_obj, created = Media.objects.update_or_create(
                        content_type=ContentType.objects.get_for_model(User),
                        object_id=user.id,
                        defaults={"media_type": "image", "file": image}
                    )

                return True_Response_200('User updated successfully', user_serializer.data)

        except Exception as e:
            transaction.savepoint_rollback(savepoint)
            return Except_Exception_Response_400(e, user_serializer.errors)

    @extend_schema(
        operation_id="organization_user_delete",
        summary="Delete organization users",
        description="Soft delete multiple users by IDs in an organization.",
        tags=["Organization Sub User"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
            OpenApiParameter(
                name="ids",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="IDs to delete. Repeat param: ids=1&ids=2",
                many=True,
            ),
        ],
        request=UpdateResponseSerializer,
        responses={
            200: OpenApiResponse(response=UpdateResponseSerializer, description="Users deleted"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def destroy(self, request, org_id, *args, **kwargs):
        try:
            # Get list of IDs from request data
            ids = request.data.get('ids')
            if not ids:
                ids = request.query_params.getlist('ids')
            if not ids:
                return Exception_Response_400('No user IDs provided for deletion.')

            print('Request IDs:', ids)
            print('Organization ID:', org_id)

            # Get users from the organization
            users = self.get_queryset(org_id).filter(id__in=ids, is_deleted=False)
            print('Found users:', users.values('id', 'username', 'is_deleted'))

            if not users.exists():
                return Exception_Response_400('No valid users found for deletion.')

            # Soft delete all users
            for user in users:
                user.soft_delete()
                user.is_active = False
                user.save()

            return True_Response_200('Users deleted successfully', [])
        except Exception as e:
            print('Error:', str(e))
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_user_trash_list",
        summary="List trashed organization users",
        description="List soft-deleted users for an organization with pagination.",
        tags=["Organization Sub User"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        responses={
            200: OpenApiResponse(description="Paginated trashed user list"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def trash(self, request, org_id, *args, **kwargs):
        try:
            # Get filters from query params and add organization filter
            filters = request.query_params.dict()
            filters['profile__organization'] = org_id
            # Apply dynamic filters and search
            search_query = request.query_params.get('search')
            sort = request.query_params.get("sort")
            data = dynamic_filter(self.model, search_fields=["first_name", "last_name", "username", "email"],
                                  search_query=search_query, sort_by=sort, is_trash=True, **filters)

            if not data.exists():
                return True_Response_200("No data found", [])

            paginator = CustomPageNumberPagination()
            paginated_result = paginator.paginate_queryset(data, request)
            serializer = self.user_serializer_class(paginated_result, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_user_restore",
        summary="Restore organization users",
        description="Restore multiple soft-deleted users by IDs in an organization.",
        tags=["Organization Sub User"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        request=OrganizationUserRequestSerializer,
        responses={
            200: OpenApiResponse(response=UpdateResponseSerializer, description="Users restored"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def restore(self, request, org_id, *args, **kwargs):
        try:
            # Get list of IDs from request data
            ids = request.data.get('ids', [])
            if not ids:
                return Exception_Response_400('No user IDs provided for restoration.')

            # Check user limit before restoring
            # limit_check = check_users_limit(org_id)
            # if limit_check is not True:
            #     return Exception_Response_400("Error getting organization subscription plan")

            # Get users from the organization
            users = self.get_queryset(org_id).filter(id__in=ids, is_deleted=True)
            
            if not users.exists():
                return Exception_Response_400('No valid users found for restoration.')

            # Restore all users
            for user in users:
                user.restore()
                user.is_active = True
                user.save()

            return True_Response_200('Users restored successfully', [])
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        operation_id="organization_user_status_update",
        summary="Update users status",
        description="Bulk update status for multiple users in an organization.",
        tags=["Organization Sub User"],
        request=UserStatusUpdateRequestSerializer,
        responses={
            200: OpenApiResponse(description="Users status updated"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def status_update(self, request, org_id, *args, **kwargs):
        try:
            # Get status and IDs from request data
            status = request.data.get('status')
            ids = request.data.get('ids', [])
            
            if status is None:
                return Exception_Response_400('Status is required.')
            
            if not ids:
                return Exception_Response_400('No user IDs provided for status update.')

            # Get users from the organization
            users = self.get_queryset(org_id).filter(id__in=ids, is_deleted=False)
            
            if not users.exists():
                return Exception_Response_400('No valid users found for status update.')

            # Update both status and is_active for all users
            users.update(status=status, is_active=status)

            return True_Response_200('Users status updated successfully', [])
        except Exception as e:
            return Except_Exception_Response_400(e)



