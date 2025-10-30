from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Department
class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=50, blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_departments")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Team
class Team(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="teams")
    team_leader = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="leading_teams")
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("name", "department")

    def __str__(self):
        return f"{self.department.code or self.department.name} / {self.name}"

# Employee (custom user)
class Employee(AbstractUser):
    father_name = models.CharField(max_length=150, blank=True)
    national_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    address = models.JSONField(blank=True, default=dict)
    phone_number = PhoneNumberField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    employment_date = models.DateField(blank=True, null=True)
    job_title = models.CharField(max_length=150, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees")
    office_line_number = models.CharField(max_length=50, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    is_admin = models.BooleanField(default=False)

    history = HistoricalRecords()

    teams = models.ManyToManyField(Team, through="TeamMembership", related_name="members")

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.get_full_name() or self.username

# explicit through model for membership
class TeamMembership(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    joined_at = models.DateField(null=True, blank=True)
    is_leader = models.BooleanField(default=False)
    role = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("employee", "team")

    def __str__(self):
        return f"{self.employee} in {self.team} ({'leader' if self.is_leader else 'member'})"

# TimeSession: start/stop presence
class TimeSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="time_sessions")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [models.Index(fields=["user", "start_time"])]

    def duration_seconds(self):
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return None

    def duration_hours(self):
        secs = self.duration_seconds()
        if secs is None:
            return None
        return round(secs / 3600, 2)

    def __str__(self):
        return f"{self.user.username} {self.start_time} → {self.end_time or 'open'}"

# TimeEntry: aggregated / manual timesheet rows
class TimeEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="time_entries")
    date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2)
    project = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=50, default="manual")
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["user", "date"])]

    def __str__(self):
        return f"{self.user.username} {self.date} {self.hours}"

# LeaveRequest workflow
class LeaveRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_LEADER_APPROVED = "leader_approved"
    STATUS_MANAGER_APPROVED = "manager_approved"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_LEADER_APPROVED, "Leader Approved"),
        (STATUS_MANAGER_APPROVED, "Manager Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leave_requests")
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    leader = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="leave_requests_to_review_as_leader")
    leader_decision = models.CharField(max_length=20, choices=[("approved", "approved"), ("rejected", "rejected")], null=True, blank=True)
    leader_decision_at = models.DateTimeField(null=True, blank=True)

    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="leave_requests_to_review_as_manager")
    manager_decision = models.CharField(max_length=20, choices=[("approved", "approved"), ("rejected", "rejected")], null=True, blank=True)
    manager_decision_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notified_groups = models.ManyToManyField("auth.Group", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.applicant} {self.start_date}→{self.end_date} ({self.status})"

# Notification model (generic target)
class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    verb = models.CharField(max_length=255)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications_sent")
    target_content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("target_content_type", "target_object_id")
    data = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    unread = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notif to {self.recipient} - {self.verb}"

class Notice(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)
    visible_from = models.DateTimeField(null=True, blank=True)
    visible_until = models.DateTimeField(null=True, blank=True)
    visible_to_groups = models.ManyToManyField("auth.Group", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        ordering = ["-published_at"]
    def __str__(self):
        return self.title
