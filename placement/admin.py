# placement/admin.py
from django.contrib import admin
from .models import Job, Application

# If django.contrib.admin is REMOVED, this file will effectively do nothing.
try:
    if 'django.contrib.admin' in __import__('django.conf').settings.INSTALLED_APPS:
        admin.site.register(Job)
        admin.site.register(Application)
except Exception:
    pass

# placement/admin.py

from django.contrib import admin
from .models import Job, Application


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("company_name", "job_role", "application_deadline", "posted_by", "posted_at")
    search_fields = ("company_name", "job_role")
    list_filter = ("company_name", "application_deadline")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("student", "job", "status", "applied_at", "admin_comments")
    list_filter = ("status", "job__company_name")
    search_fields = ("student__user__username", "job__job_role")

    # Optional: make status and comments editable directly from list view
    list_editable = ("status", "admin_comments")
