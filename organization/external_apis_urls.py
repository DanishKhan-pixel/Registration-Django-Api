from django.urls import path
from .external_apis import ExternalOrganizationView, ActiveOrganizationsList


urlpatterns = [
    path('/get-names', ExternalOrganizationView.as_view({'get': 'get_names'}), name='organization-get-names'),
    path('/active-list', ActiveOrganizationsList.as_view({'get': 'list'}), name='active-organizations-list'),
]
