from django.urls import path
from .views import OrganizationUserView, OrganizationView


urlpatterns = [
    path('', OrganizationView.as_view({
        'post': 'create', 
        'get': 'list', 
        'delete': 'destroy',
        'patch': 'status_update'
    }), name='organization-list-create'),
    path('/<int:id>', OrganizationView.as_view({'get': 'retrieve', 'patch': 'update'}), name='organization-detail'),
    path('/trash', OrganizationView.as_view({'get': 'trash'}), name='organization-trash'),
    path('/restore', OrganizationView.as_view({'patch': 'restore'}), name='organization-restore'),
    path('/<int:org_id>/sub-user', OrganizationUserView.as_view({
        'post': 'create', 
        'get': 'list', 
        'delete': 'destroy',
        'patch': 'status_update'
    }), name='organization-user-list-create'),
    path('/<int:org_id>/all-users', OrganizationUserView.as_view({'get': 'all_users'}), name='organization-all-users'),
    path('/<int:org_id>/sub-user/<int:id>', OrganizationUserView.as_view({'get': 'retrieve', 'patch': 'update'}), name='organization-user-detail'),
    path('/<int:org_id>/sub-user/trash', OrganizationUserView.as_view({'get': 'trash'}), name='organization-user-trash'),
    path('/<int:org_id>/sub-user/restore', OrganizationUserView.as_view({'patch': 'restore'}), name='organization-user-restore'),
]
