from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import TimeSession, Notification, LeaveRequest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

def _create_notification(recipient, verb, actor=None, target=None, data=None):
    Notification.objects.create(
        recipient=recipient,
        verb=verb,
        actor=actor,
        target_content_type=ContentType.objects.get_for_model(target) if target else None,
        target_object_id=getattr(target, "id", None) if target else None,
        data=data or {},
    )

def notify_presence_change(user, action, session):
    # recipients: team leaders and department manager
    recipients = set()
    for team in user.teams.all():
        if team.team_leader:
            recipients.add(team.team_leader)
    if user.department and user.department.manager:
        recipients.add(user.department.manager)
    # optionally notify team members (not by default)
    for r in recipients:
        _create_notification(recipient=r, verb=f"{user.get_full_name() or user.username} {action} working", actor=user, target=session, data={"action": action, "session_id": session.id})

def notify_leave_created(leave):
    # notify leader (if exists) to review; otherwise notify manager
    if leave.leader:
        _create_notification(recipient=leave.leader, verb=f"Leave request from {leave.applicant.get_full_name() or leave.applicant.username}", actor=leave.applicant, target=leave, data={"stage": "leader"})
    elif leave.manager:
        _create_notification(recipient=leave.manager, verb=f"Leave request from {leave.applicant.get_full_name() or leave.applicant.username}", actor=leave.applicant, target=leave, data={"stage": "manager"})
    # notify applicant as confirmation
    _create_notification(recipient=leave.applicant, verb="Your leave request was submitted", actor=None, target=leave, data={})
