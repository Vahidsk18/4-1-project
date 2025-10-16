# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile

# Register your custom User model and StudentProfile if django.contrib.admin is enabled
# If django.contrib.admin is REMOVED, this file will effectively do nothing.
try:
    if 'django.contrib.admin' in __import__('django.conf').settings.INSTALLED_APPS:
        class CustomUserAdmin(UserAdmin):
            fieldsets = UserAdmin.fieldsets + (
                (None, {'fields': ('user_type',)}),
            )
            add_fieldsets = UserAdmin.add_fieldsets + (
                (None, {'fields': ('user_type',)}),
            )

        admin.site.register(User, CustomUserAdmin)
        admin.site.register(StudentProfile)
except Exception:
    # Handle cases where django.contrib.admin might not be available or fully loaded
    pass