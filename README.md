![Tutor Track screenshot](./tutoring/static/images/tutorTrack_screenshot.png?raw=true)

# Tutor Track

Tutor Track is a Django app for managing private tutoring assignments, lesson tracking, monthly reporting, and tutor payments.

The app is built for a Hebrew, right-to-left workflow. Admin users create students and assignments, while tutors log in to view their own assignments, record lessons or attendance adjustments, and add progress updates.

## Features

- Login-based access for tutors and administrators
- Assignment management for students, tutors, goals, sponsors, schedules, and billing
- Two billing modes:
  - per-session billing, based on recorded lesson duration
  - monthly billing, with late/absent adjustments deducted from the monthly rate
- Monthly dashboard with totals grouped by sponsor:
  - parents
  - yeshiva
  - fund/other
- Assignment detail pages grouped by month
- Progress updates for each assignment, including multiple updates in the same month
- Sorting by student or tutor
- Hebrew date, month, time, and duration inputs
- Heroku-ready deployment configuration with Gunicorn and WhiteNoise

## Tech Stack

- Python 3.11
- Django
- PostgreSQL for local development and production
- SQLite test settings
- Pipenv
- HTML, CSS, and JavaScript
- Flatpickr for Hebrew-friendly date and time pickers
- Gunicorn and WhiteNoise for deployment

## Getting Started

Clone the project and install dependencies:

```bash
pipenv install
```

Activate the virtual environment:

```bash
pipenv shell
```

Create a local PostgreSQL database named `tutortrack`:

```bash
createdb tutortrack
```

Create a `.env` file in the project root:

```bash
SECRET_KEY=your-local-secret-key
```

Run migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

## Running Tests

The project includes a separate SQLite-based test settings file:

```bash
SECRET_KEY=test-secret DJANGO_SETTINGS_MODULE=tutortrack.settings_test python manage.py test
```

## How The App Works

Superusers can create students, create assignments, edit assignments, delete assignments, and access the Django admin.

Regular tutor users only see assignments connected to their own account. They can open an assignment, add lesson records for per-session assignments, add late/absent reports for monthly assignments, and write progress updates.

The dashboard summarizes the selected month, calculates payment totals, and groups the results by the assignment sponsor.

## Deployment Notes

The app is configured for Heroku-style deployment:

- `Procfile` runs `gunicorn tutortrack.wsgi`
- `DATABASE_URL` is used when `ON_HEROKU` is present
- static files are served with WhiteNoise
- `SECRET_KEY` must be provided through environment variables
