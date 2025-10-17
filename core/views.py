# core/views.py

import os
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import StudentSignUpForm, AdminSignUpForm, LoginForm, StudentProfileForm
from .models import StudentProfile, User
from placement.models import Job, Application # Ensure Job model is imported
from django.db.models import Q # For complex queries
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.messages import get_messages 
from placement.models import Job, Application # Ensure Job model is imported
from django.db.models import Q, Count 
import spacy
from docx import Document
import PyPDF2
# --- NEW IMPORTS FOR EXCEL/CSV EXPORT ---
from django.http import HttpResponse
import csv
# ----------------------------------------
# --- NEW IMPORT FOR ML SERVICE ---
from placement.ml_service import get_overall_placement_prediction
# ---------------------------------


# --- Helper Functions (unchanged) ---
def is_student(user):
    return user.is_authenticated and user.user_type == 'student'

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

# --- READINESS SCORING LOGIC (Cleaned) ---
def calculate_readiness_score(student_profile):
    """Calculates a simple readiness score (0-100) based on profile completeness and metrics."""
    score = 0
    max_score = 100
    
    # Weights for different factors
    weights = {
        'cgpa': 30,
        'backlogs': 30,
        'skills': 20,
        'resume_file': 10,
        'experience': 10
    }
    
    # 1. CGPA Score (Max 30)
    if student_profile.cgpa is not None:
        # Assuming max CGPA is 10.0, scale to 30. Example: CGPA 9.0 -> 27/30
        cgpa_score = min(float(student_profile.cgpa) / 10.0 * weights['cgpa'], weights['cgpa'])
        score += cgpa_score

    # 2. Backlogs Score (Max 30) - Inverse correlation
    if student_profile.backlogs is not None:
        if student_profile.backlogs == 0:
            score += weights['backlogs']  # Perfect score for 0 backlogs
        elif student_profile.backlogs == 1:
            score += weights['backlogs'] * 0.5  # 50% penalty for 1 backlog
        else:
            score += weights['backlogs'] * 0.1  # Heavy penalty for >1 backlog

    # 3. Skills (Max 20) - Simple check for presence
    if student_profile.skills:
        # Award full points if skills were auto-parsed or manually added
        score += weights['skills']

    # 4. Resume File (Max 10)
    if student_profile.resume_file:
        score += weights['resume_file']
        
    # 5. Experience/Projects (Max 10)
    if student_profile.experience:
        score += weights['experience']
        
    # Cap score at 100 just in case
    final_score = round(min(score, max_score), 2)
    student_profile.placement_readiness_score = final_score
    
    # The cluster_id field is explicitly excluded from being saved here
    student_profile.save(update_fields=['placement_readiness_score'])
    
    return final_score
# --- END CLEANED SCORING LOGIC ---


# --- Authentication Views (unchanged) ---
def student_signup(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Student account created successfully!")
            return redirect('student_dashboard')
        else:
            messages.error(request, "Error creating student account.")
    else:
        form = StudentSignUpForm()
    return render(request, 'core/student_signup.html', {'form': form})

def admin_signup(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Admin account created successfully! You are now logged in.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Error creating admin account.")
    else:
        form = AdminSignUpForm()
    return render(request, 'core/admin_signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # --- MODIFIED LOGIC: Only show login message for students ---
                if user.user_type == 'admin':
                    # No message for admin on login (as requested)
                    return redirect('admin_dashboard')
                elif user.user_type == 'student':
                    messages.info(request, f"You are now logged in as {username}.") # Keep message for student
                    return redirect('student_dashboard')
                # -----------------------------------------------------------
                else:
                    messages.error(request, "Unknown user type. Please contact support.")
                    logout(request)
                    return redirect('login')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def user_logout(request):
    # Clear all previous messages
    storage = get_messages(request)
    for _ in storage:
        pass  # consume and clear old messages

    # Now log out
    logout(request)

    # Add only logout message
    messages.success(request, "You have been logged out.")
    return redirect("login")

# --- Dashboards (CLEANED) ---
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    
    # --- ENSURE READINESS SCORE IS CALCULATED/UPDATED HERE ---
    if student_profile.cgpa is not None and student_profile.backlogs is not None:
         calculate_readiness_score(student_profile)
    # ---------------------------------------------------

    applications = student_profile.applications.all().order_by('-applied_at')

    # Fetch recent jobs (e.g., last 5, similar to admin dashboard)
    recent_jobs = Job.objects.all().order_by('-posted_at')[:5]

    # --- NEW: OVERALL PLACEMENT PREDICTION ---
    placement_chance = get_overall_placement_prediction(student_profile)
    # ----------------------------------------

    context = {
        'student_profile': student_profile,
        'applications': applications,
        'recent_jobs': recent_jobs,
        'placement_chance': placement_chance,
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_students = StudentProfile.objects.count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    
    total_coordinators = User.objects.filter(user_type='admin').count()
    pending_coordinators_approval = 0 # Placeholder for future expansion
    pending_students_confirmation = StudentProfile.objects.filter(
        Q(applications__isnull=True) | Q(cgpa__isnull=True) | Q(skills__isnull=True)
    ).distinct().count()

    # New code to get top job application trends
    top_job_trends = Job.objects.annotate(application_count=Count('applications')).order_by('-application_count')[:5]

    recent_applications = Application.objects.filter(status='applied').order_by('-applied_at')[:10]

    context = {
        'total_students': total_students,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'total_coordinators': total_coordinators,
        'pending_coordinators_approval': pending_coordinators_approval,
        'pending_students_confirmation': pending_students_confirmation,
        'top_job_trends': top_job_trends, # <--- ADDED: Pass top job trends to context
        'recent_applications': recent_applications,
    }
    return render(request, 'core/admin_dashboard.html', context)

# --- Admin Student List View (CLEANED) ---
@login_required
@user_passes_test(is_admin)
def student_list_admin(request):
    
    # 1. Force update/classification for any student missing a score/cluster but has data
    # Logic is simplified here to only ensure score is calculated (cluster logic removed)
    students_to_process = StudentProfile.objects.filter(
        Q(placement_readiness_score=0.0) | Q(placement_readiness_score__isnull=True), 
        cgpa__isnull=False, backlogs__isnull=False
    )
    for student in students_to_process:
        # Call the full readiness calculation
        calculate_readiness_score(student)
        
    all_students = StudentProfile.objects.all().order_by('roll_number')

    search_query = request.GET.get('q')
    branch_filter = request.GET.get('branch')
    min_cgpa = request.GET.get('min_cgpa')
    max_backlogs = request.GET.get('max_backlogs')
    
    filtered_students = all_students

    if search_query:
        filtered_students = filtered_students.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(roll_number__icontains=search_query)
        )
    if branch_filter:
        filtered_students = filtered_students.filter(branch__icontains=branch_filter)
    if min_cgpa:
        filtered_students = filtered_students.filter(cgpa__gte=min_cgpa)
    if max_backlogs:
        filtered_students = filtered_students.filter(backlogs__lte=max_backlogs)

    available_branches = StudentProfile.objects.values_list('branch', flat=True).distinct().order_by('branch')

    context = {
        'students': filtered_students,
        'available_branches': available_branches,
        'all_students_count': all_students.count(),
        'current_search_query': search_query,
        'current_branch_filter': branch_filter,
        'current_min_cgpa': min_cgpa,
        'current_max_backlogs': max_backlogs,
    }
    return render(request, 'core/student_list_admin.html', context)

# --- NEW: EXPORT VIEW (unchanged) ---
@login_required
@user_passes_test(is_admin)
def export_students_xls(request):
    # 1. Replicate filtering logic from student_list_admin
    all_students = StudentProfile.objects.all().order_by('roll_number')

    search_query = request.GET.get('q')
    branch_filter = request.GET.get('branch')
    min_cgpa = request.GET.get('min_cgpa')
    max_backlogs = request.GET.get('max_backlogs')
    
    # Use select_related and prefetch_related for efficient querying
    filtered_students = all_students.select_related('user').prefetch_related('applications')

    if search_query:
        filtered_students = filtered_students.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(roll_number__icontains=search_query)
        )
    if branch_filter:
        filtered_students = filtered_students.filter(branch__icontains=branch_filter)
    if min_cgpa:
        filtered_students = filtered_students.filter(cgpa__gte=min_cgpa)
    if max_backlogs:
        filtered_students = filtered_students.filter(backlogs__lte=max_backlogs)

    # 2. Excel Generation Logic
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_list_summary.csv"'

    writer = csv.writer(response)

    # --- Write only the requested headers ---
    writer.writerow([
        'Username', 
        'Branch', 
        'CGPA', 
        'Skills', 
        'Phone Number'
    ])

    # 3. Write data rows
    for student in filtered_students:
        # Sanitize multi-line/complex fields for CSV
        skills = student.skills.replace('\n', ' | ').replace('\r', '') if student.skills else ''
        
        writer.writerow([
            student.user.username,
            student.branch,
            student.cgpa,
            skills,
            student.phone_number,
        ])

    return response
# ----------------------------------------


# --- Student Profile Management (CLEANED) ---
@login_required
@user_passes_test(is_student)
def student_profile_view(request):
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student_profile)
        if form.is_valid():
            form.save()
            if 'resume_file' in request.FILES:
                parse_resume_for_student(student_profile)
            
            # --- CALCULATE READINESS SCORE ---
            calculate_readiness_score(student_profile)
            # ---------------------------------
            
            messages.success(request, "Profile updated successfully!")
            return redirect('student_profile_view')
        else:
            messages.error(request, "Error updating profile.")
    else:
        # --- CALCULATE SCORE ON INITIAL VIEW ---
        if created or student_profile.placement_readiness_score == 0.0:
            calculate_readiness_score(student_profile)
        # ---------------------------------------
        form = StudentProfileForm(instance=student_profile)
    return render(request, 'core/student_profile.html', {'form': form, 'student_profile': student_profile})

# --- ML/NLP (Resume Parsing) Integration (unchanged functions) ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
    nlp = None


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def extract_text_from_docx(docx_path):
    text = ""
    try:
        doc = Document(docx_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
    return text

def parse_resume_text(text):
    if not nlp:
        return {'skills': '', 'education': '', 'experience': '', 'phone_number': '', 'cgpa': None, 'backlogs': None}

    doc = nlp(text)
    
    skills = []
    education = []
    experience = []
    phone_number = ""
    cgpa = None
    backlogs = None
    
    # --- CGPA Extraction ---
    # Looks for 'CGPA' or 'GPA' followed by a number format X.X or X.XX
    # Use a broad search and extract the first match
    cgpa_match = re.search(r'(cgpa|gpa|score|percentage)\D*(\d\.\d{1,2}|\d{2,3})', text, re.IGNORECASE)
    if cgpa_match:
        try:
            # Clean and convert the matched number to a float
            cgpa_str = cgpa_match.group(2).replace(',', '.')
            if '.' not in cgpa_str and len(cgpa_str) > 2: # Handle 85 (for 8.5/10 or 85%)
                cgpa_value = float(cgpa_str) / 10.0 # Arbitrary guess for 85 -> 8.5
            else:
                cgpa_value = float(cgpa_str)
            
            # Simple validation: CGPA should be between 0.00 and 10.00
            if 0.0 <= cgpa_value <= 10.0:
                cgpa = round(cgpa_value, 2)
        except ValueError:
            pass
            
    # --- Backlogs Extraction ---
    # Looks for 'backlog' or 'arrear' followed by a number (0, 1, 2, etc.)
    backlogs_match = re.search(r'(backlogs|arrears|backlog|arrear)\D*(\d+)', text, re.IGNORECASE)
    if backlogs_match:
        try:
            backlogs = int(backlogs_match.group(2))
        except ValueError:
            pass

    # --- ENHANCED SKILL LIST ---
    common_skills = [
        "python", "java", "django", "react", "sql", "data analysis", "machine learning", 
        "web development", "javascript", "html", "css", "c++", "aws", "git", 
        "full stack", "node js", "mongodb", "azure", "docker", "kubernetes",
        "tableau", "power bi", "spring boot", "rest api", "api", "testing", "ai/ml",
        "neural networks", "devops", "cloud computing", "r programming", "linux", "typescript"
    ]
    text_lower = text.lower()
    for skill in common_skills:
        if skill in text_lower:
            skills.append(skill.capitalize())
    # --------------------------

    for ent in doc.ents:
        if ent.label_ == "ORG" and ("university" in ent.text.lower() or "college" in ent.text.lower()):
            education.append(ent.text)
        elif ent.label_ == "ORG" and re.search(r'\b(b\.?tech|m\.?tech|bachelor|master|ph\.?d)\b', ent.text, re.IGNORECASE):
             education.append(ent.text)

    for sent in doc.sents:
        if "experience" in sent.text.lower() or "worked at" in sent.text.lower() or "software engineer" in sent.text.lower() or "project" in sent.text.lower():
            experience.append(sent.text)

    phone_match = re.search(r'\b(?:\+91[\s-]?)?[6789]\d{9}\b', text)
    if not phone_match:
        phone_match = re.search(r'\b(?:\+?\d{1,3}[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b', text)

    if phone_match:
        phone_number = phone_match.group(0)


    parsed_data = {
        'skills': ", ".join(list(set(skills))),
        'education': "\n".join(list(set(education))),
        'experience': "\n".join(list(set(experience))),
        'phone_number': phone_number,
        'cgpa': cgpa,      # NEW FIELD
        'backlogs': backlogs # NEW FIELD
    }
    return parsed_data

def parse_resume_for_student(student_profile):
    if student_profile.resume_file:
        file_path = student_profile.resume_file.path
        file_extension = os.path.splitext(file_path)[1].lower()
        
        extracted_text = ""
        if file_extension == '.pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            extracted_text = extract_text_from_docx(file_path)
        else:
            messages.error(f"Unsupported file type: {file_extension}. Only PDF and DOCX are supported.")
            return

        parsed_data = parse_resume_text(extracted_text)
        
        student_profile.skills = parsed_data.get('skills', student_profile.skills)
        student_profile.education = parsed_data.get('education', student_profile.education)
        student_profile.experience = parsed_data.get('experience', student_profile.experience)
        student_profile.phone_number = parsed_data.get('phone_number', student_profile.phone_number)
        
        # --- UPDATE CGPA/BACKLOGS ONLY IF A VALID VALUE WAS FOUND ---
        if parsed_data.get('cgpa') is not None:
            student_profile.cgpa = parsed_data.get('cgpa')
        if parsed_data.get('backlogs') is not None:
            student_profile.backlogs = parsed_data.get('backlogs')
        # -----------------------------------------------------------
        
        student_profile.save()
        print(f"Resume parsed and profile updated for {student_profile.user.username}")
    else:
        print(f"No resume file found for {student_profile.user.username}")


# //////////////
@login_required
@user_passes_test(is_admin)
def all_applications_admin(request):
    """
    View to list all student applications, with optional job filter.
    """
    jobs = Job.objects.all().order_by('-posted_at')  # for filter dropdown
    job_id = request.GET.get('job_id')

    applications = Application.objects.select_related('student__user', 'job').order_by('-applied_at')

    # Apply filter if job_id is provided
    selected_job = None
    if job_id:
        selected_job = get_object_or_404(Job, id=job_id)
        applications = applications.filter(job=selected_job)

    context = {
        'applications': applications,
        'all_applications_count': applications.count(),
        'jobs': jobs,
        'selected_job': selected_job,
    }
    return render(request, 'core/all_applications_admin.html', context)