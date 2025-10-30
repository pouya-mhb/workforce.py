1. Create virtualenv and install requirements:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Update DATABASES in personnel_project/settings.py (defaults to sqlite for quick start).
   For PostgreSQL, set ENGINE to postgresql and provide credentials.

3. Make migrations, migrate, create superuser:
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser

4. (Optional) load sample fixture:
   python manage.py loaddata fixtures/sample_data.json

5. Run server:
   python manage.py runserver

6. Admin: http://127.0.0.1:8000/admin/
   Login/logout handled by /accounts/login/ and logout redirect.
