from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Media, Profile, Token, LoginHistory

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'gender', 
                    'country_code', 'contact', 'is_active', 'is_staff', 'is_superuser', 'status', 'is_deleted', 
                    'created_at', 'updated_at', 'deleted_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'status', 'is_deleted', 
                  'gender', 'role', 'created_at', 'updated_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'contact', 'country_code')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'gender', 'country_code', 'contact')}),
        ('Role', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Status', {'fields': ('status', 'is_deleted', 'deleted_at')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'gender', 'country_code', 'contact'),
        }),
    )

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id', 'media_type', 'file', 'status', 
                   'is_deleted', 'created_at', 'updated_at')
    list_filter = ('media_type', 'content_type', 'status', 'is_deleted', 'created_at')
    search_fields = ('id', 'object_id', 'media_type')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'organization', 'status', 'is_deleted', 'created_at', 
                   'updated_at')
    list_filter = ('organization', 'status', 'is_deleted', 'created_at')
    search_fields = ('user__username', 'user__email', 'organization__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'organization', 'type', 'code', 'expires', 'status', 
                   'is_deleted', 'created_at', 'updated_at')
    list_filter = ('type', 'status', 'is_deleted', 'created_at', 'expires')
    search_fields = ('user__username', 'user__email', 'organization__name', 'code', 'type')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'login_time', 'logout_time', 'type', 'status', 
                   'is_deleted', 'created_at', 'updated_at')
    list_filter = ('login_time', 'logout_time', 'type', 'status', 'is_deleted')
    search_fields = ('user__username', 'user__email', 'type')
    date_hierarchy = 'login_time'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
