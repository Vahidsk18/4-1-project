# placement/models.py

from django.db import models
from core.models import User, StudentProfile  # Import your custom User and StudentProfile
from django.core.mail import send_mail

class Job(models.Model):
    company_name = models.CharField(max_length=100)
    job_role = models.CharField(max_length=100)
    description = models.TextField()
    salary_package = models.CharField(max_length=50, blank=True, null=True)
    eligibility_criteria = models.TextField(
        help_text="e.g., Min CGPA 7.0, CSE/IT branches, No backlogs"
    )
    application_deadline = models.DateField()
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_jobs",
    )
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_role} at {self.company_name}"


class Application(models.Model):
    APPLICATION_STATUS_CHOICES = (
        ("applied", "Applied"),
        ("shortlisted", "Shortlisted"),
        ("rejected", "Rejected"),
        ("interview_scheduled", "Interview Scheduled"),
        ("accepted", "Accepted"),
    )
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="applications"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=APPLICATION_STATUS_CHOICES, default="applied"
    )
    admin_comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (
            "student",
            "job",
        )  # A student can apply for a job only once

    def __str__(self):
        return f"{self.student.user.username} applied for {self.job.job_role} at {self.job.company_name} - Status: {self.status}"

    def save(self, *args, **kwargs):
        # Check if status or admin_comments changed
        if self.pk:  # only if this is an update, not a new record
            old = Application.objects.get(pk=self.pk)
            if old.status != self.status or old.admin_comments != self.admin_comments:
                self.send_status_email()
        super().save(*args, **kwargs)

    def send_status_email(self):
        """Send email notification to student when status changes or comments added"""
        subject = f"Update on your Application for {self.job.job_role} at {self.job.company_name}"
        message = ""

        if self.status == "shortlisted":
            message = f"Good news! 🎉 You have been shortlisted for {self.job.job_role} at {self.job.company_name}."
        elif self.status == "rejected":
            message = f"Unfortunately, your application for {self.job.job_role} at {self.job.company_name} has been rejected."
        elif self.status == "interview_scheduled":
            message = f"Your interview for {self.job.job_role} at {self.job.company_name} has been scheduled. Please check the portal for details."
        elif self.status == "accepted":
            message = f"Congratulations! 🎉 You have been accepted for {self.job.job_role} at {self.job.company_name}."

        # Append admin comments (reason)
        if self.admin_comments:
            message += f"\n\nReason/Comments from Admin: {self.admin_comments}"

        # Send email
        if message:
            send_mail(
                subject,
                message,
                "no-reply@smartrecruitment.com",  # From email
                [self.student.user.email],       # To student's registered email
                fail_silently=False,
            )
