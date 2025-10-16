# placement/forms.py

from django import forms
from .models import Job, Application

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['company_name', 'job_role', 'description', 'salary_package', 'eligibility_criteria', 'application_deadline']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'eligibility_criteria': forms.Textarea(attrs={'rows': 5}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
        }

class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status', 'admin_comments']
        widgets = {
            'admin_comments': forms.Textarea(attrs={'rows': 3}),
        }