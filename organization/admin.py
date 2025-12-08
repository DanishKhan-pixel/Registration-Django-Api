from django.contrib import admin
from .models import Organization, Country

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'contact', 'country', 'address', 'status', 
                   'ip', 'validation_frequency', 'is_deleted', 'created_at', 'updated_at')
    list_filter = ('status', 'is_deleted', 'country', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username', 'user__email', 'contact', 'country', 'address', 'ip')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    fieldsets = (
        (None, {'fields': ('user', 'name', 'contact')}),
        ('Location', {'fields': ('country', 'address')}),
        ('Network', {'fields': ('ip', 'ssh_key', 'validation_frequency')}),
        ('Status', {'fields': ('status', 'is_deleted', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


