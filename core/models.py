# core/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    # You can add more fields specific to a general user if needed

    def __str__(self):
        return self.username

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True) # This MUST be unique=True here (model field)
    branch = models.CharField(max_length=50)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    backlogs = models.IntegerField(default=0)
    # Store parsed resume data here or a reference to it
    skills = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    # Add other fields from resume as needed

    # Field to store the actual resume file
    resume_file = models.FileField(upload_to='resumes/', blank=True, null=True)

    # --- NEW FIELD FOR ML/READINESS SCORE ---
    placement_readiness_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, verbose_name='Readiness Score')
    # ----------------------------------------

    def __str__(self):
        return f"{self.user.username} - {self.roll_number}"

# Admin doesn't need a separate profile model unless you have specific admin-only fields
# that are not covered by the default AbstractUser.