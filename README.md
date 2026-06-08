# SudPix

SudPix is a Django-powered website and client portal for a Nairobi creative studio offering photography, videography, branding, and graphic design. The public site presents services, portfolio work, booking, and a premium client workspace demo. The authenticated portal helps clients manage briefs, milestones, feedback, approvals, revisions, payments, file selection, and final delivery downloads.

## Features

- Premium public landing pages for home, services, portfolio, about, contact, FAQ, and client workspace demo.
- Service booking flow with client onboarding and notification support.
- Client dashboard for projects, project briefs, milestones, feedback, approvals, revision requests, payments, files, cart, checkout, and downloads.
- Staff dashboard for studio activity, uploads, payments, selections, bookings, and delivery readiness.
- Portfolio and services pages backed by Django views and reusable templates.
- M-PESA configuration hooks for payment status and checkout workflows.
- Demo portal seeding command for local previews and testing.

## Tech Stack

- Python and Django 6
- SQLite for local development
- Django templates with Tailwind CDN and custom SudPix CSS
- Pillow for media handling
- Gunicorn and WhiteNoise for deployment

## Project Structure

```text
sudpix/
  apps/
    accounts/          Account login, registration, profile, password reset
    bookings/          Service booking request flow
    clients/           Client portal dashboard, projects, files, payments
    core/              Public pages, homepage, workspace demo, demo seed command
    dashboard/         Staff/studio dashboard
    media_management/  Media assets and previews
    payments/          Payment records and M-PESA integration points
    portfolio/         Portfolio listing and detail pages
    projects/          Briefs, milestones, feedback, approvals, revisions
    services/          Service listings and packages
  static/              Static assets
  templates/           Shared and app templates
  sudpix/              Django settings, URLs, WSGI/ASGI
```

## Local Setup

From the project root:

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Open the site at:

```text
http://127.0.0.1:8000/
```

## Demo Client Portal

Seed repeatable demo data for a realistic client workspace:

```bash
python manage.py seed_portal_demo --reset
```

Default demo credentials:

```text
Username: mary_wanjiku
Password: SudpixDemo123!
```

Then visit:

```text
http://127.0.0.1:8000/accounts/client-login/
http://127.0.0.1:8000/client/dashboard/
```

## Useful Routes

- `/` - homepage
- `/services/` - service landing page
- `/services/<slug>/` - service detail view
- `/portfolio/` - portfolio landing page
- `/portfolio/<slug>/` - portfolio project detail
- `/client-workspace-demo/` - public client workspace demo
- `/bookings/create/` - booking request form
- `/accounts/login/` - login choice page
- `/accounts/client-login/` - client login
- `/client/dashboard/` - authenticated client dashboard
- `/studio/` - staff dashboard
- `/admin/` - Django admin

## Environment Variables

Use `.env.example` as the starting point:

```bash
cp .env.example .env
```

Important settings:

- `DEBUG` - use `True` locally and `False` in production.
- `ALLOWED_HOSTS` - comma-separated hostnames allowed by Django.
- `CSRF_TRUSTED_ORIGINS` - trusted HTTPS origins for production forms.
- `EMAIL_*` - SMTP settings for booking, onboarding, and notification email.
- `BOOKING_NOTIFICATION_EMAIL` - recipient for booking notifications.
- `DEFAULT_FROM_EMAIL` - sender address for system email.
- `MPESA_*` - Daraja/M-PESA credentials, callback URL, shortcode, and timeout.
- `SUDPIX_SITE_URL` - canonical public site URL used in portal links.

Do not commit real SMTP, M-PESA, or production credentials.

## Testing

Run the Django checks and test suite:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Deployment Notes

Before deploying:

```bash
python manage.py collectstatic --noinput
gunicorn sudpix.wsgi:application
```

Production checklist:

- Set `DEBUG=False`.
- Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Use real email credentials or a production email provider.
- Configure valid M-PESA credentials and callback base URL.
- Replace the development fallback `SECRET_KEY` in `sudpix/settings.py` before production use.
- Keep private client media protected. The local debug media routes intentionally block direct access to `project_assets` and `previews`.

## Development Workflow

Recommended before pushing changes:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Keep edits scoped, avoid committing generated media, and leave local `.env` files untracked.
