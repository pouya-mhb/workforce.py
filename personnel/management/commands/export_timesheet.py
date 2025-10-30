from django.core.management.base import BaseCommand
from django.utils import timezone
from personnel.models import TimeSession, TimeEntry
from django.contrib.auth import get_user_model
import csv
from datetime import date
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
    help = "Export monthly aggregated timesheet for a user or all users. Usage: --month YYYY-MM [--user username] --out path.csv"

    def add_arguments(self, parser):
        parser.add_argument("--month", required=True, help="YYYY-MM")
        parser.add_argument("--user", required=False, help="username")
        parser.add_argument("--out", required=True, help="output CSV path")

    def handle(self, *args, **options):
        month = options["month"]
        out = options["out"]
        username = options.get("user")
        year, mon = [int(x) for x in month.split("-")]
        start = date(year, mon, 1)
        if mon == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, mon + 1, 1)
        qs = TimeSession.objects.filter(start_time__date__gte=start, start_time__date__lt=end, end_time__isnull=False)
        if username:
            user = User.objects.get(username=username)
            qs = qs.filter(user=user)
        # aggregate per user per day
        rows = {}
        for s in qs:
            key = (s.user.username, s.start_time.date())
            rows.setdefault(key, 0)
            dur = (s.end_time - s.start_time).total_seconds()
            rows[key] += dur
        # write CSV
        with open(out, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["username","date","hours"])
            for (username, d), secs in sorted(rows.items()):
                hours = round(secs/3600, 2)
                writer.writerow([username, d.isoformat(), hours])
        self.stdout.write(self.style.SUCCESS(f"Wrote {len(rows)} rows to {out}"))
