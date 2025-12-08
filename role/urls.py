from django.urls import path
from .views import PermissionView, RoleView


urlpatterns = [
    path('/permissions', PermissionView.as_view({'get': 'list'})),
    path('/permissions/organizations', PermissionView.as_view({'get': 'list'})),
    path('', RoleView.as_view({
        'get': 'list', 
        'post': 'create',
        'delete': 'destroy',
        'patch': 'status_update'
    })),
    path('/<int:id>', RoleView.as_view({'get': 'retrieve', 'patch': 'update'})),
    path('/trash', RoleView.as_view({'get': 'trash'})),
    path('/restore', RoleView.as_view({'patch': 'restore'})),
]