# placement_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from core import views as core_views
from placement import views as placement_views
from django.contrib.auth.decorators import login_required

# View for newsletter subscription
def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Placeholder: Add logic to save email or send to a newsletter service
        messages.success(request, 'Thank you for subscribing!')
        return redirect('home')
    return redirect('home')

urlpatterns = [
    # path('admin/', admin.site.urls),
    # Landing page
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    # Custom Admin Dashboard
    path('admin/dashboard/', login_required(core_views.admin_dashboard), name='admin_dashboard'),
    
    

    # Authentication URLs
    path('signup/student/', core_views.student_signup, name='student_signup'),
    path('signup/admin/', core_views.admin_signup, name='admin_signup'),
    path('login/', core_views.user_login, name='login'),
    path('logout/', core_views.user_logout, name='logout'),

    # User Dashboards
    path('student/dashboard/', login_required(core_views.student_dashboard), name='student_dashboard'),

    # Student Profile URLs
    path('student/profile/', login_required(core_views.student_profile_view), name='student_profile_view'),
    path('admin/students/', login_required(core_views.student_list_admin), name='student_list_admin'),
    
    # --- NEW: EXPORT URL ---
    path('admin/students/export/', login_required(core_views.export_students_xls), name='export_students_xls'),

    # Admin Job Management URLs
    path('admin/jobs/', login_required(placement_views.job_list_admin), name='admin_job_list'),
    path('admin/jobs/create/', login_required(placement_views.job_create), name='job_create'),
    path('admin/jobs/<int:pk>/update/', login_required(placement_views.job_update), name='job_update'),
    path('admin/jobs/<int:pk>/delete/', login_required(placement_views.job_delete), name='job_delete'),

    # Admin Application Management URLs
    path('admin/jobs/<int:job_id>/applications/', login_required(placement_views.applications_for_job), name='applications_for_job'),
    path('admin/applications/<int:application_id>/update_status/', login_required(placement_views.update_application_status), name='update_application_status'),
    path('admin/applications/all/', login_required(placement_views.all_applications_list), name='all_applications_list'),
    # from . import views

    # Student Job & Application URLs
    path('student/jobs/', login_required(placement_views.student_job_list), name='student_job_list'),
    path('student/jobs/<int:job_id>/apply/', login_required(placement_views.apply_for_job), name='apply_for_job'),

    # --- NEW: IOT/PLACED STUDENTS URLS (ADDED FOR YOUR REQUEST) ---
    # 1. JSON Feed for IoT devices (NO login_required)
    path('api/iot/placed_feed/json/', placement_views.placed_students_json_feed, name='placed_students_json_feed'),
    # 2. Web View for easy testing/simple displays (NO login_required)
    path('api/iot/placed_feed/web/', placement_views.placed_students_web_feed, name='placed_students_web_feed'),
    
    # Newsletter subscription
    path('subscribe/', subscribe_newsletter, name='subscribe_newsletter'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)