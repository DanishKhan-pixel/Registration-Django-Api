from django.contrib import admin
from .models import Role, Permission

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'status', 'is_deleted', 
                    'created_at', 'updated_at')
    list_filter = ('status', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    filter_horizontal = ('permissions',)
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Permissions', {'fields': ('permissions',)}),
        ('Status', {'fields': ('status', 'is_deleted', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'codename', 'model', 'status', 'is_deleted', 'created_at', 
                    'updated_at')
    list_filter = ('model', 'status', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('name', 'codename', 'model')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    fieldsets = (
        (None, {'fields': ('name', 'codename', 'model')}),
        ('Status', {'fields': ('status', 'is_deleted', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
