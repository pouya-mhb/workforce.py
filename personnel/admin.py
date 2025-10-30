from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Employee, Department, Team, TeamMembership,
    TimeSession, TimeEntry, LeaveRequest, Notification
)
from simple_history.admin import SimpleHistoryAdmin

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "manager")
    search_fields = ("name", "code", "manager__username")

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "team_leader")
    search_fields = ("name", "department__name", "team_leader__username")
    list_filter = ("department",)

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("employee", "team", "is_leader", "joined_at")
    search_fields = ("employee__username", "team__name")
    list_filter = ("team", "is_leader")

@admin.register(Employee)
class EmployeeAdmin(UserAdmin, SimpleHistoryAdmin):
    model = Employee
    list_display = ("username","first_name","last_name","email","department","job_title","is_staff")
    list_filter = ("department","is_staff","is_superuser","is_active")
    search_fields = ("username","first_name","last_name","email","national_id")
    fieldsets = (
        (None, {"fields": ("username","password")}),
        ("Personal", {"fields": ("first_name","last_name","father_name","email","phone_number","profile_picture")}),
        ("Work", {"fields": ("national_id","department","job_title","office_line_number","employment_date","date_of_birth")}),
        ("Permissions", {"fields": ("is_active","is_staff","is_superuser","groups","user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username","password1","password2")}),
    )

@admin.register(TimeSession)
class TimeSessionAdmin(admin.ModelAdmin):
    list_display = ("user","start_time","end_time","location","created_at")
    list_filter = ("start_time", "location")
    search_fields = ("user__username", "user__first_name", "user__last_name")

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("user","date","hours","project","approved")
    list_filter = ("date","approved")
    search_fields = ("user__username","project")

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("applicant","start_date","end_date","status")
    list_filter = ("status","start_date")
    search_fields = ("applicant__username","applicant__first_name","applicant__last_name")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient","verb","actor","created_at","unread")
    list_filter = ("unread","created_at")
    search_fields = ("recipient__username","verb")
