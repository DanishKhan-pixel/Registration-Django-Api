from authentication.models import User, Profile
from organization.models import Organization
from rest_framework.views import APIView
from .helpers import get_calculated_data
from utils.custom_response import True_Response_200, Except_Exception_Response_400, Exception_Response_400
from django.db.models import Q, Count
from role.models import Role
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from datetime import datetime, timedelta
import logging
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
)
from utils.serializers import ValidationErrorSerializer, InternalServerErrorSerializer
from .serializers import (
    ActiveUsersOverviewResponseSerializer,
    TotalsResponseSerializer,
    RoleDistributionResponseSerializer,
    OrganizationSignupsResponseSerializer,
)

logger = logging.getLogger(__name__)


class ActiveUsersOverview(APIView):
    @extend_schema(
        operation_id="dashboard_active_users_overview",
        summary="Active users overview",
        description="Return active user count and percentage difference for an organization.",
        tags=["Dashboard"], 
        parameters=[ 
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        responses={
            200: OpenApiResponse(response=ActiveUsersOverviewResponseSerializer, description="Active users overview returned"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def get(self, request, org_id, *args, **kwargs):
        try:
            # Get organization ID from query params
            if not org_id:
                return Exception_Response_400("Organization ID is required.")

            # Get filtered users using get_calculated_data
            users_queryset = get_calculated_data(User, request)
            
            # Filter active users for the organization
            active_users = users_queryset.filter(
                profile__organization_id=org_id,
                is_active=True,
                status=True,
                is_deleted=False
            ).count()

            # Get percentage difference from request object (set by get_calculated_data)
            percentage_difference = getattr(request, 'user_percentage', None)

            response_data = {
                'active_users': active_users,
                'percentage_difference': percentage_difference
            }

            return True_Response_200("Active users overview retrieved successfully", response_data)
        except Exception as e:
            logger.error(f"Error retrieving active users overview: {str(e)}", exc_info=True)
            return Except_Exception_Response_400(e)


class TotalOrganizationsView(APIView):
    @extend_schema(
        operation_id="dashboard_totals",
        summary="Totals for organizations and users",
        description="Return registered organizations, total users, and percentage deltas.",
        tags=["Dashboard"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, required=False, description="Filter totals for a specific organization"),
            OpenApiParameter(name="from_date", type=OpenApiTypes.DATE, required=False, description="Start date filter"),
            OpenApiParameter(name="to_date", type=OpenApiTypes.DATE, required=False, description="End date filter"),
        ],
        responses={
            200: OpenApiResponse(response=TotalsResponseSerializer, description="Totals returned"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            # Get query parameters
            query_params = request.query_params
            org_id = query_params.get('org_id')

            # Get filtered organizations using get_calculated_data
            organizations = get_calculated_data(Organization, request)
            registered_organizations = organizations.count()

            if org_id:
                # If org_id is provided, get filtered users from Profile table
                users = get_calculated_data(User, request)
                total_users = users.filter(profile__organization_id=org_id).count()
                registered_organizations = organizations.filter(id=org_id).count()
            else:
                # If no org_id, use get_calculated_data for users
                users = get_calculated_data(User, request)
                total_users = users.count()

            response = {
                'registered_organizations': registered_organizations,
                'total_users': total_users,
                'organization_percentage_difference': getattr(request, 'organization_percentage', None),
                'user_percentage_difference': getattr(request, 'user_percentage', None)
            }
            return True_Response_200("Total Organizations", response)
        except Exception as e:
            return Except_Exception_Response_400(e)


class RoleWiseUsersDistributionView(APIView):
    @extend_schema(
        operation_id="dashboard_role_distribution",
        summary="Role-wise user distribution",
        description="Return counts and percentages of users by role.",
        tags=["Dashboard"],
        responses={
            200: OpenApiResponse(response=RoleDistributionResponseSerializer, description="Distribution returned"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def get(self, request, *args, **kwargs):
        try:

            # Get filtered users using get_calculated_data
            users_queryset = get_calculated_data(User, request)

            # Get total number of users
            total_users = users_queryset.count()

            # Get role-wise user counts
            role_counts = users_queryset.values('role__name').annotate(
                count=Count('id')
            ).order_by('-count')

            # Calculate percentages
            distribution = []
            for role in role_counts:
                if role['role__name']:  # Only include users with roles
                    percentage = (role['count'] / total_users) * 100 if total_users > 0 else 0
                    distribution.append({
                        'role_name': role['role__name'],
                        'user_count': role['count'],
                        'percentage': round(percentage, 2)
                    })

            # Add "No Role" count if there are users without roles
            no_role_count = users_queryset.filter(role__isnull=True).count()
            if no_role_count > 0:
                no_role_percentage = (no_role_count / total_users) * 100 if total_users > 0 else 0
                distribution.append({
                    'role_name': 'No Role',
                    'user_count': no_role_count,
                    'percentage': round(no_role_percentage, 2)
                })

            response = {
                'total_users': total_users,
                'distribution': distribution
            }
            return True_Response_200("Role-wise user distribution", response)
        except Exception as e:
            return Except_Exception_Response_400(e)


class OrganizationSignupsView(APIView):
    @extend_schema(
        operation_id="dashboard_organization_signups",
        summary="Organization signups by month",
        description="Return monthly active/inactive organization signups for current year.",
        tags=["Dashboard"],
        responses={
            200: OpenApiResponse(response=OrganizationSignupsResponseSerializer, description="Signup chart data returned"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            # Get current year and month
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month
            
            # Base queryset for organizations in current year
            organizations = Organization.objects.filter(
                is_deleted=False,
                created_at__year=current_year
            )

            # Group by month and get counts
            monthly_data = organizations.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                total=Count('id'),
                active=Count('id', filter=Q(status=True)),
                inactive=Count('id', filter=Q(status=False))
            ).order_by('month')

            # Create a dictionary of month data for easy lookup
            data_dict = {
                data['month'].month: {
                    'active': data['active'],
                    'inactive': data['inactive']
                } for data in monthly_data
            }

            # Prepare response data
            labels = []
            active_data = []
            inactive_data = []

            # Generate data for all months up to current month
            for month in range(1, current_month + 1):
                # Format month as short name (Jan, Feb, etc.)
                month_name = datetime(current_year, month, 1).strftime('%b')
                labels.append(month_name)
                
                # Get data for the month or use zeros if no data
                month_data = data_dict.get(month, {'active': 0, 'inactive': 0})
                active_data.append(month_data['active'])
                inactive_data.append(month_data['inactive'])

            response = {
                'labels': labels,
                'data': {
                    'active': active_data,
                    'inactive': inactive_data
                }
            }
            return True_Response_200("Organization signups by month", response)
        except Exception as e:
            return Except_Exception_Response_400(e)


class RoleWiseOrgUsersDistributionView(APIView):
    @extend_schema(
        operation_id="dashboard_role_distribution_by_org",
        summary="Role-wise user distribution for organization",
        description="Return counts and percentages of users by role for a given organization.",
        tags=["Dashboard"],
        parameters=[
            OpenApiParameter(name="org_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, required=True, description="Organization ID"),
        ],
        responses={
            200: OpenApiResponse(response=RoleDistributionResponseSerializer, description="Distribution returned"),
            400: OpenApiResponse(response=ValidationErrorSerializer, description="Validation error"),
            500: OpenApiResponse(response=InternalServerErrorSerializer, description="Internal server error"),
        },
    )
    def get(self, request, org_id, *args, **kwargs):
        try:

            # Get filtered users using get_calculated_data
            users_queryset = get_calculated_data(User, request)
            users_queryset = users_queryset.filter(role__organization__id=org_id)

            # Get total number of users
            total_users = users_queryset.count()

            # Get role-wise user counts
            role_counts = users_queryset.values('role__name').annotate(
                count=Count('id')
            ).order_by('-count')

            # Calculate percentages
            distribution = []
            for role in role_counts:
                if role['role__name']:  # Only include users with roles
                    percentage = (role['count'] / total_users) * 100 if total_users > 0 else 0
                    distribution.append({
                        'role_name': role['role__name'],
                        'user_count': role['count'],
                        'percentage': round(percentage, 2)
                    })

            # Add "No Role" count if there are users without roles
            no_role_count = users_queryset.filter(role__isnull=True).count()
            if no_role_count > 0:
                no_role_percentage = (no_role_count / total_users) * 100 if total_users > 0 else 0
                distribution.append({
                    'role_name': 'No Role',
                    'user_count': no_role_count,
                    'percentage': round(no_role_percentage, 2)
                })

            response = {
                'total_users': total_users,
                'distribution': distribution
            }
            return True_Response_200("Role-wise user distribution", response)
        except Exception as e:
            return Except_Exception_Response_400(e)
