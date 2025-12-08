from rest_framework.viewsets import ViewSet
from .models import Permission, Role
from utils.custom_response import True_Response_200, Except_Exception_Response_400, Exception_Response_400
from utils.custom_pagination import CustomPageNumberPagination
from utils.helpers import dynamic_filter
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample,
)
from utils.serializers import ValidationErrorSerializer, InternalServerErrorSerializer
from .serializers import (
    PermissionSerializer,
    RoleSerializer,
    PermissionListResponseSerializer,
    RoleResponseSerializer,
    RoleListResponseSerializer,
    RoleRequestSerializer,
    RoleStatusUpdateRequestSerializer,
    DeleteResponseSerializer,
    StatusUpdateResponseSerializer,
    RestoreResponseSerializer,
)

@extend_schema_view(
    list=extend_schema(
        tags=["Permissions"],
        summary="List permissions",
        description="List all permissions. If the URL contains 'organizations', only permissions for ['camera', 'site', 'user'] are returned.",
    ),
)
class PermissionView(ViewSet):
    serializer_class = PermissionSerializer
    queryset = Permission.objects.all()

    @extend_schema(
        summary="List permissions",
        description="List all permissions. If the URL contains 'organizations', only permissions for ['camera', 'site', 'user'] are returned.",
        tags=["Permissions"],
        responses={
            200: OpenApiResponse(response=PermissionListResponseSerializer, description="Permissions retrieved successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def list(self, request, *args, **kwargs):
        try:
            # Check if URL contains 'organizations'
            url_path = request.path
            is_organization_path = 'organizations' in url_path
            
            # Define allowed models for organization-specific permissions
            allowed_models = ['camera', 'site', 'user']
            
            if is_organization_path:
                # Filter permissions for specific models when URL contains 'organizations'
                permissions = self.queryset.filter(
                    model__in=allowed_models
                )
            else:
                # Return all permissions if URL doesn't contain 'organizations'
                permissions = self.queryset

            serializer = self.serializer_class(permissions, many=True)
            return True_Response_200("Permissions retrieved successfully", serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)


@extend_schema_view(
    create=extend_schema(
        tags=["Roles"],
        summary="Create role",
        description="Create a new role.",
    ),
    list=extend_schema(
        tags=["Roles"],
        summary="List roles",
        description="List roles with optional search, sort, and organization filters. Returns only global roles when organization is not provided.",
    ),
    retrieve=extend_schema(
        tags=["Roles"],
        summary="Retrieve role",
        description="Retrieve a single role by ID.",
    ),
    update=extend_schema(
        tags=["Roles"],
        summary="Update role",
        description="Update a role by ID (partial updates supported).",
    ),
    destroy=extend_schema(
        tags=["Roles"],
        summary="Delete roles",
        description="Soft delete multiple roles by IDs.",
    ),
    trash=extend_schema(
        tags=["Roles"],
        summary="List trashed roles",
        description="List soft-deleted roles with pagination and filters.",
    ),
    restore=extend_schema(
        tags=["Roles"],
        summary="Restore roles",
        description="Restore multiple soft-deleted roles by IDs.",
    ),
    status_update=extend_schema(
        tags=["Roles"],
        summary="Update roles status",
        description="Bulk update status for multiple roles by IDs.",
    ),
)
class RoleView(ViewSet):
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    pagination_class = CustomPageNumberPagination
    model = Role

    @extend_schema(
        request=serializer_class,
        summary="Create role",
        description="Create a new role",
        tags=["Roles"],
        responses={
            200: OpenApiResponse(response=RoleResponseSerializer, description="Role created successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return True_Response_200("Role created successfully", serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e, serializer.errors)

    @extend_schema(
        summary="List roles",
        description="List roles with optional search, sort, and organization filters. Returns only global roles when organization is not provided.",
        tags=["Roles"],
        parameters=[
            OpenApiParameter(name="organization", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description="Organization ID"),
            OpenApiParameter(name="search", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Search by name"),
            OpenApiParameter(name="sort", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Sort by name"),
        ],
        responses={
            200: OpenApiResponse(response=RoleListResponseSerializer, description="Paginated roles list"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def list(self, request, *args, **kwargs):
        try:
            filters = request.query_params.dict()
            search = request.query_params.get("search")
            sort = request.query_params.get("sort") 
            
            organization = request.query_params.get("organization")
            data = dynamic_filter(self.model, search_fields=["name"], search_query=search, sort_by=sort, **filters)
            if not organization:
                data = data.filter(organization=None)
            if not data.exists():
                return True_Response_200("No data found", [])

            paginator = self.pagination_class()
            paginated_result = paginator.paginate_queryset(data, request)
            serializer = self.serializer_class(paginated_result, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        summary="Retrieve role",
        description="Retrieve role by ID",
        tags=["Roles"],
        responses={
            200: OpenApiResponse(response=RoleResponseSerializer, description="Role retrieved successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        if self.kwargs.get('id'):
            try:
                role_id = self.kwargs.get('id')
                role = self.queryset.filter(id=role_id, is_deleted=False).first()
                serializer = self.serializer_class(role)
                return True_Response_200("Role retrieved successfully", serializer.data)
            except Exception as e:
                return Except_Exception_Response_400(e)
        else:
            return Exception_Response_400("Role ID required")

    @extend_schema(
        request=serializer_class,
        summary="Update role",
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Role ID"),
        ],
        tags=["Roles"],
        responses={
            200: OpenApiResponse(response=RoleResponseSerializer, description="Role updated successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def update(self, request, *args, **kwargs):
        if self.kwargs.get("id"):
            try:
                role_id = int(self.kwargs.get("id"))
                role = self.queryset.filter(id=role_id, is_deleted=False).first()
                serializer = self.serializer_class(role, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return True_Response_200("Role updated successfully", serializer.data)
            except Exception as e:
                return Except_Exception_Response_400(e, serializer.errors)
        else:
            return Exception_Response_400("Role ID Required")

    @extend_schema(
        summary="Delete roles",
        description="Soft delete multiple roles by IDs",
        request=RoleRequestSerializer,
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
        tags=["Roles"],
        responses={
            200: OpenApiResponse(response=DeleteResponseSerializer, description="Roles deleted successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        }
    )
    def destroy(self, request, *args, **kwargs):
        try:
            # Get list of IDs from request data or query params
            ids = request.data.get('ids')
            if not ids:
                ids = request.query_params.getlist('ids')
            if not ids:
                return Exception_Response_400('No role IDs provided for deletion.')

            # Get roles
            roles = self.queryset.filter(id__in=ids, is_deleted=False)
            
            if not roles.exists():
                return Exception_Response_400('No valid roles found for deletion.')

            # Soft delete all roles
            for role in roles:
                role.soft_delete()

            return True_Response_200('Roles deleted successfully', [])
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        summary="List trashed roles",
        description="List soft-deleted roles",
        tags=["Roles"],
        responses={
            200: OpenApiResponse(response=RoleListResponseSerializer, description="Paginated trashed roles list"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def trash(self, request, *args, **kwargs):
        try:
            filters = request.query_params.dict()
            search = request.query_params.get("search")
            sort = request.query_params.get("sort")
            organization = request.query_params.get("organization")
            data = dynamic_filter(self.model, search_fields=["name"], search_query=search,
                                  sort_by=sort, is_trash=True, **filters)
            if not organization:
                data = data.filter(organization=None)

            if not data.exists():
                return True_Response_200("No data found", [])

            paginator = self.pagination_class()
            paginated_result = paginator.paginate_queryset(data, request)
            serializer = self.serializer_class(paginated_result, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        summary="Restore roles",
        description="Restore multiple roles by IDs. Accepts IDs in body or as repeated query params.",
        request=RoleRequestSerializer,
        tags=["Roles"],
        responses={
            200: OpenApiResponse(response=RestoreResponseSerializer, description="Roles restored successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        }
    )
    def restore(self, request, *args, **kwargs):
        try:
            # Get list of IDs from request data
            ids = request.data.get('ids', [])
            if not ids:
                return Exception_Response_400('No role IDs provided for restoration.')

            # Get roles
            roles = self.queryset.filter(id__in=ids, is_deleted=True)

            if not roles.exists():
                return Exception_Response_400('No valid roles found for restoration.')

            # Restore all roles
            for role in roles:
                role.restore()

            return True_Response_200('Roles restored successfully', [])
        except Exception as e:
            return Except_Exception_Response_400(e)

    @extend_schema(
        summary="Update roles status",
        description="Update status for multiple roles",
        request=RoleStatusUpdateRequestSerializer,
        tags=["Roles"],
        responses={
            200: OpenApiResponse(response=StatusUpdateResponseSerializer, description="Roles status updated successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        }
    )
    def status_update(self, request, *args, **kwargs):
        try:
            # Get status and IDs from request data
            status = request.data.get('status')
            ids = request.data.get('ids', [])

            if status is None:
                return Exception_Response_400('Status is required.')

            if not ids:
                return Exception_Response_400('No role IDs provided for status update.')

            # Get roles
            roles = self.queryset.filter(id__in=ids, is_deleted=False)

            if not roles.exists():
                return Exception_Response_400('No valid roles found for status update.')

            # Update status for all roles
            roles.update(status=status)

            return True_Response_200('Roles status updated successfully', [])
        except Exception as e:
            return Except_Exception_Response_400(e)

