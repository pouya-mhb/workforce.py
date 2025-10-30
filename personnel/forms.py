from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Employee, TimeEntry, TimeSession, LeaveRequest

class EmployeeCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Employee
        fields = ("username","first_name","last_name","email","national_id","phone_number","department","job_title")

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ("date","hours","project","notes")
        widgets = {"date": forms.DateInput(attrs={"type":"date"})}

class StartSessionForm(forms.ModelForm):
    class Meta:
        model = TimeSession
        fields = ("location",)

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ("team","start_date","end_date","reason")
        widgets = {
            "start_date": forms.DateInput(attrs={"type":"date"}),
            "end_date": forms.DateInput(attrs={"type":"date"}),
            "reason": forms.Textarea(attrs={"rows":4}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("End date must be >= start date")
        return cleaned
