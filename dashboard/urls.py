from django.urls import path
from .views import (
    TotalOrganizationsView,
    RoleWiseUsersDistributionView,
    OrganizationSignupsView,
    RoleWiseOrgUsersDistributionView,
    ActiveUsersOverview
    )

urlpatterns = [
    path('total-organizations', TotalOrganizationsView.as_view(), name='total-organizations'),
    path('role-distribution', RoleWiseUsersDistributionView.as_view(), name='role-distribution'),
    path('organization-signups', OrganizationSignupsView.as_view(), name='organization-signups'),
    path('<int:org_id>/users-summary', RoleWiseOrgUsersDistributionView.as_view(), name='organization-users-summary'),
    path('<int:org_id>/active-users', ActiveUsersOverview.as_view(), name='active-users-overview'),
]
