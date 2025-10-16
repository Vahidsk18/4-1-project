# placement/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from core.views import is_admin, is_student, calculate_readiness_score 
from core.models import StudentProfile, User
from .models import Job, Application
from .forms import JobForm, ApplicationStatusForm
from django.db.models import Q # For complex queries
import re 
from django.utils import timezone
from datetime import date
from placement.ml_service import get_job_specific_prediction 


# --- HELPER FUNCTION: Score Application for Admin Shortlisting (MODIFIED) ---
def score_application(application):
    job = application.job
    student_profile = application.student
    
    match_score = 0
    max_possible_match_score = 0 
    job_eligibility_lower = job.eligibility_criteria.lower()
    student_branch_lower = student_profile.branch.lower()

    # A. Branch Check
    branch_criteria_explicit = False
    if not ("all branches" in job_eligibility_lower or "any branch" in job_eligibility_lower):
        for b in ["cse", "it", "ece", "eee", "mech", "civil"]:
            if b in job_eligibility_lower:
                branch_criteria_explicit = True
                break
    
    if branch_criteria_explicit:
        max_possible_match_score += 1
        if student_branch_lower in job_eligibility_lower:
            match_score += 1

    # B. CGPA Check
    cgpa_match_regex = re.search(r'(?:min(?:imum)?\s*)?cgpa\s*(\d+\.?\d*)', job_eligibility_lower)
    if cgpa_match_regex and student_profile.cgpa is not None:
        max_possible_match_score += 1
        try:
            required_cgpa = float(cgpa_match_regex.group(1)) 
            student_cgpa_value = float(student_profile.cgpa) 
            if student_cgpa_value >= required_cgpa:
                match_score += 1
        except ValueError:
            max_possible_match_score -= 1 

    # C. Backlogs Check
    backlogs_criteria_found = re.search(r'(no\s+backlogs|max(?:imum)?\s+backlogs\s+(\d+))', job_eligibility_lower)
    if backlogs_criteria_found and student_profile.backlogs is not None:
        max_possible_match_score += 1
        is_backlog_match = True
        
        if re.search(r'no\s+backlogs', job_eligibility_lower):
            if student_profile.backlogs > 0:
                is_backlog_match = False
        elif re.search(r'max(?:imum)?\s+backlogs\s+(\d+)', job_eligibility_lower):
            try:
                allowed_backlogs = int(re.search(r'max(?:imum)?\s+backlogs\s+(\d+)', job_eligibility_lower).group(1))
                if student_profile.backlogs > allowed_backlogs:
                    is_backlog_match = False
            except ValueError:
                max_possible_match_score -= 1
                is_backlog_match = True 
        
        if is_backlog_match:
            match_score += 1

    # D. Calculate Percentage and Tag (FIXED LOGIC HERE)
    if max_possible_match_score == 0:
        match_percentage = 0
        recommendation = "No Criteria" # <--- CLEAR TAG FOR ADMINS
    else:
        match_percentage = round((match_score / max_possible_match_score) * 100, 0)
        
        # Assign Recommendation Tag
        if match_percentage >= 90:
            recommendation = "Strong Fit"
        elif match_percentage >= 60:
            recommendation = "Average Match"
        else:
            recommendation = "Low Match"

    # Attach properties to the application object dynamically
    application.match_percentage = match_percentage
    application.recommendation = recommendation
    return application
# -----------------------------------------------------------------------------


# --- Admin Job Management (unchanged) ---
@login_required
@user_passes_test(is_admin)
def job_list_admin(request):
    jobs = Job.objects.all().order_by('-posted_at')
    today = timezone.now().date()
    
    # Tag jobs as expired or upcoming (Feature B Flagging)
    for job in jobs:
        job.is_expired = job.application_deadline < today
        # Upcoming warning if deadline is <= 7 days away and not expired yet
        job.is_upcoming = (job.application_deadline - today).days <= 7 and not job.is_expired
        
    return render(request, 'placement/admin_job_list.html', {'jobs': jobs, 'today': today})

@login_required
@user_passes_test(is_admin)
def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect('admin_job_list')
        else:
            messages.error(request, "Error posting job.")
    else:
        form = JobForm()
    return render(request, 'placement/job_form.html', {'form': form, 'title': 'Create New Job'})

@login_required
@user_passes_test(is_admin)
def job_update(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully!")
            return redirect('admin_job_list')
        else:
            messages.error(request, "Error updating job.")
    else:
        form = JobForm(instance=job)
    return render(request, 'placement/job_form.html', {'form': form, 'title': 'Update Job'})

@login_required
@user_passes_test(is_admin)
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted successfully!")
        return redirect('admin_job_list')
    return render(request, 'placement/job_confirm_delete.html', {'job': job})

# --- Admin Application Management & Filtering (MODIFIED for Feature A) ---
@login_required
@user_passes_test(is_admin)
def applications_for_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    applications = Application.objects.filter(job=job).order_by('-applied_at')

    # Filtering Logic (unchanged)
    min_cgpa = request.GET.get('min_cgpa')
    branch = request.GET.get('branch')
    max_backlogs = request.GET.get('max_backlogs')
    skills = request.GET.get('skills')
    status = request.GET.get('status')

    # Prefetch student data for scoring efficiency
    applications = applications.select_related('student__user')
    
    filtered_applications = applications # Start with filtered set

    if min_cgpa:
        filtered_applications = filtered_applications.filter(student__cgpa__gte=min_cgpa)
    if branch:
        filtered_applications = filtered_applications.filter(student__branch__icontains=branch)
    if max_backlogs:
        filtered_applications = filtered_applications.filter(student__backlogs__lte=max_backlogs)
    if skills:
        for skill_item in skills.split(','):
            filtered_applications = filtered_applications.filter(student__skills__icontains=skill_item.strip())
    if status:
        filtered_applications = filtered_applications.filter(status=status)
    
    # --- NEW: Apply Scoring and Sorting (Feature A) ---
    scored_applications = []
    for app in filtered_applications:
        scored_applications.append(score_application(app))
    
    # Sort by descending match percentage (best candidates first)
    scored_applications.sort(key=lambda x: x.match_percentage, reverse=True)
    # -----------------------------------------------------

    available_branches = StudentProfile.objects.values_list('branch', flat=True).distinct().order_by('branch')
    application_statuses = Application.APPLICATION_STATUS_CHOICES


    context = {
        'job': job,
        'applications': scored_applications, # Pass the scored, sorted list
        'all_applications_count': applications.count(),
        'available_branches': available_branches,
        'application_statuses': application_statuses,
        'current_min_cgpa': min_cgpa,
        'current_branch': branch,
        'current_max_backlogs': max_backlogs,
        'current_skills': skills,
        'current_status': status,
    }
    return render(request, 'placement/admin_job_applications.html', context)

@login_required
@user_passes_test(is_admin)
def update_application_status(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, "Application status updated successfully!")
            return redirect('applications_for_job', job_id=application.job.id)
        else:
            print(f"Form validation errors for application {application_id}: {form.errors}")
            messages.error(request, "Error updating application status. Please check inputs and try again.")
    return redirect('applications_for_job', job_id=application.job.id)

# --- All Applications List (MODIFIED to include scoring) ---
@login_required
@user_passes_test(is_admin)
def all_applications_list(request):
    # Retrieve all applications, and prefetch related data needed for scoring
    applications = Application.objects.select_related('student__user', 'job').order_by('-applied_at')
    
    # --- FIX: Apply Scoring to ALL applications ---
    scored_applications = []
    for app in applications:
        # Check if the job object exists before scoring (handles potential data inconsistencies)
        if app.job and app.student:
             scored_applications.append(score_application(app))
        else:
            # Handle cases where related job/student might be missing
            app.match_percentage = 0
            app.recommendation = "Data Missing"
            scored_applications.append(app)

    # Sort by descending match percentage (best candidates first)
    scored_applications.sort(key=lambda x: x.match_percentage, reverse=True)
    # ---------------------------------------------------------

    context = {
        'applications': scored_applications,
        'job': None, # Keep job as None as this view is for 'All Jobs'
        'all_applications_count': applications.count(),
    }
    return render(request, 'placement/admin_job_applications.html', context)

# --- Student Job Listing (unchanged) ---
@login_required
@user_passes_test(is_student)
def student_job_list(request):
    # --- Feature B Hiding: Filter out expired jobs ---
    today = timezone.now().date()
    jobs = Job.objects.filter(application_deadline__gte=today).order_by('-posted_at')
    # -----------------------------------------------
    
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    
    # ... (rest of the student_job_list logic remains the same) ...

    # Ensure readiness score is calculated before proceeding
    if student_profile.placement_readiness_score == 0.0:
        from core.views import parse_resume_for_student
        parse_resume_for_student(student_profile)
        calculate_readiness_score(student_profile) 

    applied_job_ids = student_profile.applications.values_list('job_id', flat=True)

    filtered_jobs_with_scores = []
    
    student_cgpa = student_profile.cgpa
    student_backlogs = student_profile.backlogs
    student_branch_lower = student_profile.branch.lower()
    
    for job in jobs:
        job_is_hard_eligible = True 
        match_score = 0     
        max_possible_match_score = 0 

        job_eligibility_lower = job.eligibility_criteria.lower()

        # --- A. Check and Score Branch Eligibility (Hard Filter & Scoring) ---
        branch_criteria_explicit = False
        if not ("all branches" in job_eligibility_lower or "any branch" in job_eligibility_lower):
            for b in ["cse", "it", "ece", "eee", "mech", "civil"]:
                if b in job_eligibility_lower:
                    branch_criteria_explicit = True
                    break
        
        if branch_criteria_explicit:
            max_possible_match_score += 1
            if student_branch_lower in job_eligibility_lower:
                match_score += 1
            else:
                job_is_hard_eligible = False # Hard fail

        # --- B. Check and Score CGPA Eligibility (Hard Filter & Scoring) ---
        cgpa_match_regex = re.search(r'(?:min(?:imum)?\s*)?cgpa\s*(\d+\.?\d*)', job_eligibility_lower)

        if cgpa_match_regex:
            max_possible_match_score += 1
            if student_cgpa is None:
                job_is_hard_eligible = False # Hard fail if required but missing
            else:
                try:
                    required_cgpa = float(cgpa_match_regex.group(1)) 
                    student_cgpa_value = float(student_cgpa) 
                    
                    if student_cgpa_value >= required_cgpa:
                        match_score += 1
                    else:
                        job_is_hard_eligible = False # Hard fail
                except ValueError:
                    max_possible_match_score -= 1 # Ignore corrupt criteria


        # --- C. Check and Score Backlogs Eligibility (Hard Filter & Scoring) ---
        backlogs_criteria_found = re.search(r'(no\s+backlogs|max(?:imum)?\s+backlogs\s+(\d+))', job_eligibility_lower)
        
        if backlogs_criteria_found:
            max_possible_match_score += 1
            
            if student_backlogs is None:
                job_is_hard_eligible = False # Hard fail if required but missing
            else:
                is_backlog_match = True
                
                if re.search(r'no\s+backlogs', job_eligibility_lower):
                    if student_backlogs > 0:
                        is_backlog_match = False
                elif re.search(r'max(?:imum)?\s+backlogs\s+(\d+)', job_eligibility_lower):
                    try:
                        allowed_backlogs = int(re.search(r'max(?:imum)?\s+backlogs\s+(\d+)', job_eligibility_lower).group(1))
                        if student_backlogs > allowed_backlogs:
                            is_backlog_match = False
                    except ValueError:
                        max_possible_match_score -= 1
                        is_backlog_match = True 
                
                if is_backlog_match:
                    match_score += 1
                else:
                    job_is_hard_eligible = False # Hard fail
        
        
        # --- D. Final Scoring & Tagging ---
        job_match_percentage = round((match_score / max_possible_match_score) * 100, 0) if max_possible_match_score > 0 else 0
        
        job.match_percentage = job_match_percentage
        job.is_hard_eligible = job_is_hard_eligible 
        
        filtered_jobs_with_scores.append(job)

    # 2. Apply Eligibility Filter Logic based on query parameter
    job_filter = request.GET.get('filter', 'all') 
    search_query = request.GET.get('q') 

    if search_query:
        # Re-apply text filter post-scoring/hiding
        q_filter = Q(company_name__icontains=search_query) | Q(job_role__icontains=search_query) | Q(description__icontains=search_query) | Q(eligibility_criteria__icontains=search_query)
        jobs_to_score = [job for job in filtered_jobs_with_scores if q_filter.check(job)]
    else:
        jobs_to_score = filtered_jobs_with_scores

    if job_filter == 'eligible':
        final_jobs = [job for job in jobs_to_score if job.is_hard_eligible]
    else: 
        final_jobs = jobs_to_score

    # 3. Sort by match percentage (descending)
    final_jobs.sort(key=lambda x: x.match_percentage, reverse=True)

    context = {
        'jobs': final_jobs,
        'student_profile': student_profile,
        'applied_job_ids': list(applied_job_ids),
        'current_filter': job_filter, 
        'current_search_query': search_query, 
    }
    return render(request, 'placement/student_job_list.html', context)

@login_required
@user_passes_test(is_student)
def apply_for_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    if Application.objects.filter(student=student_profile, job=job).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('student_dashboard')

    job_eligible = True 
    job_eligibility_lower = job.eligibility_criteria.lower()
    student_branch_lower = student_profile.branch.lower()

    if not ("all branches" in job_eligibility_lower or "any branch" in job_eligibility_lower):
        branch_criteria_found = False
        for b in ["cse", "it", "ece", "eee", "mech", "civil"]: 
            if b in job_eligibility_lower:
                branch_criteria_found = True
                break
        
        if branch_criteria_found:
            if student_branch_lower not in job_eligibility_lower:
                job_eligible = False

    # Check CGPA eligibility (hard filter)
    cgpa_match = re.search(r'(?:min(?:imum)?\s*)?cgpa\s*(\d+\.?\d*)', job_eligibility_lower)
    if cgpa_match:
        if student_profile.cgpa is None:
            job_eligible = False
        else:
            try:
                required_cgpa = float(cgpa_match.group(1))
                if float(student_profile.cgpa) < required_cgpa:
                    job_eligible = False
            except ValueError:
                pass

    # Check Backlogs eligibility (hard filter)
    backlogs_required = re.search(r'(no\s+backlogs|max(?:imum)?\s+backlogs\s+(\d+))', job_eligibility_lower)
    if backlogs_required:
        if student_profile.backlogs is None:
            job_eligible = False
        else:
            no_backlogs_match = re.search(r'no\s+backlogs', job_eligibility_lower)
            max_backlogs_match = re.search(r'max(?:imum)?\s+backlogs\s+(\d+)', job_eligibility_lower)
            
            if no_backlogs_match:
                if student_profile.backlogs > 0:
                    job_eligible = False
            elif max_backlogs_match:
                try:
                    allowed_backlogs = int(max_backlogs_match.group(1))
                    if student_profile.backlogs > allowed_backlogs:
                        job_eligible = False
                except ValueError:
                    pass

    if not job_eligible:
        messages.error(request, "You do not meet the eligibility criteria for this job.")
        return redirect('student_job_list')

    Application.objects.create(student=student_profile, job=job)
    messages.success(request, f"Successfully applied for {job.job_role} at {job.company_name}!")
    return redirect('student_dashboard')