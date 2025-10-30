from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, F
from .models import Notice, Employee, TimeEntry, TimeSession, LeaveRequest, Department, Team, Notification
from .forms import TimeEntryForm, StartSessionForm, LeaveRequestForm
from django.contrib import messages

# root redirect to dashboard
def home_redirect(request):
    return redirect("personnel:dashboard_home")

@login_required
def dashboard_home(request):
    now = timezone.now()
    # latest notices: reuse Notice model stored in DB (we keep Notice in admin with model in models.py below)
    notices = Notice.objects.filter(
        Q(visible_from__lte=now) | Q(visible_from__isnull=True),
        Q(visible_until__gte=now) | Q(visible_until__isnull=True),
    ).order_by("-published_at")[:5]
    time_form = TimeEntryForm()
    start_form = StartSessionForm()
    # upcoming approved leaves as calendar snippet
    upcoming_leaves = LeaveRequest.objects.filter(status=LeaveRequest.STATUS_MANAGER_APPROVED, end_date__gte=timezone.localdate()).order_by("start_date")[:10]
    return render(request, "dashboard/home.html", {"notices": notices, "time_form": time_form, "start_form": start_form, "upcoming_leaves": upcoming_leaves})

@login_required
def directory_list(request):
    q = request.GET.get("q", "")
    employees = Employee.objects.filter(is_active=True)
    if q:
        employees = employees.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(job_title__icontains=q) |
            Q(department__name__icontains=q)
        )
    employees = employees.select_related("department").only("first_name","last_name","job_title","department__name","office_line_number","profile_picture")[:200]
    return render(request, "directory/list.html", {"employees": employees, "q": q})

@login_required
def submit_time(request):
    if request.method == "POST":
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            messages.success(request, "Time entry submitted")
            return redirect("personnel:dashboard_home")
    return redirect("personnel:dashboard_home")

@login_required
def sessions_list(request):
    sessions = request.user.time_sessions.all().order_by("-start_time")[:200]
    return render(request, "timesheets/sessions_list.html", {"sessions": sessions})

@login_required
def start_session(request):
    if request.method == "POST":
        # idempotent: only one open session per user
        open_exists = request.user.time_sessions.filter(end_time__isnull=True).exists()
        if not open_exists:
            loc = request.POST.get("location","")
            session = TimeSession.objects.create(user=request.user, start_time=timezone.now(), location=loc)
            # notifications
            from .signals import notify_presence_change
            notify_presence_change(request.user, "started", session)
            messages.success(request, "Session started")
        else:
            messages.info(request, "Open session already exists")
    return redirect("personnel:dashboard_home")

@login_required
def stop_session(request):
    if request.method == "POST":
        session = request.user.time_sessions.filter(end_time__isnull=True).order_by("-start_time").first()
        if session:
            session.end_time = timezone.now()
            session.save()
            from .signals import notify_presence_change
            notify_presence_change(request.user, "stopped", session)
            messages.success(request, "Session stopped")
        else:
            messages.info(request, "No open session found")
    return redirect("personnel:dashboard_home")

@login_required
def leave_list(request):
    leaves = request.user.leave_requests.all().order_by("-created_at")
    return render(request, "leaves/list.html", {"leaves": leaves})

@login_required
def leave_create(request):
    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            lr = form.save(commit=False)
            lr.applicant = request.user
            # resolve leader and manager
            if lr.team and lr.team.team_leader:
                lr.leader = lr.team.team_leader
            if request.user.department and request.user.department.manager:
                lr.manager = request.user.department.manager
            lr.save()
            from .signals import notify_leave_created
            notify_leave_created(lr)
            messages.success(request, "Leave request submitted")
            return redirect("personnel:leave_list")
    else:
        form = LeaveRequestForm(initial={"team": request.user.teams.first()})
    return render(request, "leaves/create.html", {"form": form})

@login_required
def leave_review_list(request):
    # show leave requests awaiting this user's decision
    as_leader = LeaveRequest.objects.filter(leader=request.user, status=LeaveRequest.STATUS_PENDING).order_by("-created_at")
    as_manager = LeaveRequest.objects.filter(manager=request.user, status=LeaveRequest.STATUS_LEADER_APPROVED).order_by("-created_at")
    return render(request, "leaves/review_list.html", {"as_leader": as_leader, "as_manager": as_manager})

@login_required
def notifications_list(request):
    notes = request.user.notifications.all().order_by("-created_at")[:200]
    return render(request, "notifications/list.html", {"notifications": notes})
