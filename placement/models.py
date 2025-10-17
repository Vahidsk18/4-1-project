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
        ("selected", "Selected"), # CHANGED: "accepted" is now "selected"
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
        """Send email notification to student when status changes or comments added with HTML formatting."""
        
        job_role = self.job.job_role
        company_name = self.job.company_name
        
        # --- 1. Define Content based on Status ---
        if self.status == "shortlisted":
            emoji = "🎉"
            color = "#28a745" # Green
            greeting = f"Good News! {emoji} You've been Shortlisted!"
            body = f"Your application for the **{job_role}** role at **{company_name}** has been **SHORTLISTED**."
            subject = f"🎉 Shortlisted: {job_role} at {company_name}"

        elif self.status == "rejected":
            emoji = "😔"
            color = "#dc3545" # Red
            greeting = f"Important Update {emoji} on Your Application"
            body = f"Unfortunately, your application for the **{job_role}** role at **{company_name}** has been **REJECTED**."
            subject = f"😔 Rejected: {job_role} at {company_name}"

        elif self.status == "interview_scheduled":
            emoji = "🗓️"
            color = "#007bff" # Blue
            greeting = f"Interview Scheduled! {emoji} Get Ready!"
            body = f"**Heads up!** Your interview for the **{job_role}** role at **{company_name}** has been **SCHEDULED**. Please prepare well!"
            subject = f"🗓️ Interview Scheduled: {job_role} at {company_name}"

        elif self.status == "selected": # CONDITION IS NOW "selected"
            emoji = "🥳"
            color = "#ffc107" # Orange
            greeting = f"CONGRATULATIONS! YOU'VE BEEN SELECTED! {emoji}" # TEXT is changed
            body = f"We are thrilled to inform you that you have been **SELECTED** for the **{job_role}** role at **{company_name}**! This is fantastic news. View your offer details on the portal." # TEXT is changed
            subject = f"🥳 Selected: {job_role} at {company_name}" # SUBJECT is changed
        else:
            return # Don't send email for 'applied' status

        # --- 2. Construct HTML Message ---
        comments_html = ""
        if self.admin_comments:
            comments_html = f"""
            <div style="background-color: #f8f9fa; border-left: 4px solid {color}; padding: 15px; border-radius: 6px; margin-top: 20px;">
                <p style="margin: 0; font-weight: 600; font-size: 16px; color: #333;">Admin Comments / Reason:</p>
                <p style="margin: 5px 0 0; font-size: 15px; color: #555;">{self.admin_comments}</p>
            </div>
            """
            
        html_message = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; font-size: 18px; color: #343a40; line-height: 1.6; max-width: 600px; margin: auto; padding: 25px; border: 1px solid #eee; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h2 style="color: {color}; margin-bottom: 25px; font-size: 28px; font-weight: 700;">{greeting}</h2>

            <p style="font-size: 18px; margin-bottom: 20px;">
                Dear {self.student.user.first_name} {self.student.user.last_name},
            </p>

            <p style="font-size: 20px; margin-bottom: 20px;">
                {body}
            </p>

            {comments_html}

            <p style="font-size: 16px; color: #777; margin-top: 30px; padding-top: 15px; border-top: 1px solid #f0f0f0;">
                Please log into the CampusRecruit portal for complete details regarding your application status, interview schedules, or final offers.
            </p>
            <p style="font-size: 16px; color: #777; margin: 5px 0 0;">
                Best regards,<br>
                The CampusRecruit Team
            </p>
        </div>
        """
        
        # --- 3. Send Email ---
        send_mail(
            subject,
            # Fallback plain text version (required for send_mail if html_message is provided)
            f"Update on your Application for {job_role} at {company_name}. Status: {self.status}. \n\n{body}\n\nReason/Comments: {self.admin_comments or 'N/A'}",
            "no-reply@smartrecruitment.com",  # From email
            [self.student.user.email],       # To student's registered email
            fail_silently=False,
            html_message=html_message, # Pass the HTML version
        )