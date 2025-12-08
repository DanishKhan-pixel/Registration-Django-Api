from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from .models import Organization
from .serializers import (
    ExternalOrganizationSerializer,
    ExternalOrganizationsListResponseSerializer,
    ExternalOrganizationsNamesResponseSerializer,
)
from utils.custom_response import True_Response_200, Exception_Response_400, Except_Exception_Response_400
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample,
)
from utils.serializers import ValidationErrorSerializer, InternalServerErrorSerializer


@extend_schema_view(
    get_names=extend_schema(
        operation_id="external_organization_get_names",
        summary="Get organization names by IDs",
        description="Returns a minimal list of organizations (id, name) for the provided comma-separated IDs.",
        parameters=[
            OpenApiParameter(name="org_ids", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True, description="Organization IDs, e.g. 1,2,3"),
        ],
        responses={
            200: OpenApiResponse(response=ExternalOrganizationsNamesResponseSerializer, description="Organizations retrieved successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
)
@extend_schema(tags=["External"])  # 
class ExternalOrganizationView(ViewSet):
    model = Organization
    serializer_class = ExternalOrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(is_deleted=False)

    @action(detail=False, methods=['get'])
    def get_names(self, request, *args, **kwargs):
        try:
            # Get organization IDs from query params
            org_ids_str = request.query_params.get('org_ids', '')
            if not org_ids_str:
                return Exception_Response_400("Organization IDs are required")

            # Convert comma-separated string to list of integers
            try:
                org_ids = [int(id.strip()) for id in org_ids_str.split(',')]
            except ValueError:
                return Exception_Response_400("Invalid organization IDs format")

            # Get organizations
            organizations = self.get_queryset().filter(id__in=org_ids)
            if not organizations.exists():
                return Exception_Response_400("No organizations found with the provided IDs")

            # Serialize and return the data
            serializer = self.serializer_class(organizations, many=True)
            return True_Response_200("Organizations retrieved successfully", serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)


@extend_schema(tags=["External"])  
class ActiveOrganizationsList(ViewSet):
    serializer_class = ExternalOrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(is_deleted=False, status=True)

    @extend_schema(
        operation_id="external_active_organizations_list",
        summary="List active organizations (minimal)",
        description="Returns id and name for all active organizations.",
        
        responses={
            200: OpenApiResponse(response=ExternalOrganizationsListResponseSerializer, description="Active organizations list successfully"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def list(self, request, *args, **kwargs):
        try:
            data = self.get_queryset()
            serializer = self.serializer_class(data, many=True)
            return True_Response_200('Active organizations list successfully', serializer.data)
        except Exception as e:
            return Except_Exception_Response_400(e)