from django.urls import path
from . import views

app_name = "personnel"

urlpatterns = [
    path("", views.home_redirect, name="root"),
    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("directory/", views.directory_list, name="directory_list"),
    path("timesheets/submit/", views.submit_time, name="timesheet_submit"),
    path("timesheets/sessions/", views.sessions_list, name="sessions_list"),
    path("timesheets/start/", views.start_session, name="session_start"),
    path("timesheets/stop/", views.stop_session, name="session_stop"),
    path("leaves/", views.leave_list, name="leave_list"),
    path("leaves/create/", views.leave_create, name="leave_create"),
    path("leaves/review/", views.leave_review_list, name="leave_review_list"),
    path("notifications/", views.notifications_list, name="notifications"),
]
