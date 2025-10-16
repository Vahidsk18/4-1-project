# core/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, StudentProfile

class StudentSignUpForm(UserCreationForm):
    roll_number = forms.CharField(max_length=20, required=True)
    branch = forms.CharField(max_length=50, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")  # Removed user_type

    def clean_roll_number(self):
        roll_number = self.cleaned_data['roll_number']
        if StudentProfile.objects.filter(roll_number=roll_number).exists():
            raise forms.ValidationError("This roll number is already registered.")
        return roll_number

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'   # always student
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                roll_number=self.cleaned_data['roll_number'],
                branch=self.cleaned_data['branch']
            )
        return user


class AdminSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")  # Removed user_type

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'admin'   # always admin
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    pass


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['cgpa', 'backlogs', 'skills', 'education', 'experience', 'phone_number', 'resume_file']
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 4}),
            'education': forms.Textarea(attrs={'rows': 4}),
            'experience': forms.Textarea(attrs={'rows': 4}),
        }
