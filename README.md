# Mauritius Explore

Django website. **One project, one database, six apps.** Everything shown on the
site (events, places, guides, packages) comes from the database and is added
through the admin. Nothing is hardcoded.

## Step 0: ONE person only, before the first push

The migration files have not been created yet. The person who creates the new
repo runs this once, then commits the `migrations/` folders:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations core users destinations experiences bookings
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver        # click through the site to check it works
git init
git add .
git commit -m "Clean project skeleton: 6 apps, one database, all models"
git branch -M main
git remote add origin <new-repo-url>
git push -u origin main
```

Nobody else runs `makemigrations` until the models are agreed (see Team rules).

## First-time setup (everyone else)

```powershell
git clone <repo-url>
cd Mauritius-Explore
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # optional sample data
python manage.py createsuperuser    # your own admin account
python manage.py runserver
```

- Website: http://127.0.0.1:8000/
- Admin (add/edit content): http://127.0.0.1:8000/admin/
- Custom dashboard: http://127.0.0.1:8000/dashboard/

## Project structure

```
mauritius_explore/   settings.py, urls.py (one of each for the whole site)
apps/
  core/              Homepage (Discover Mauritius), Contact
  users/             Create Account, Login, Profile   | model: Profile (role)
  destinations/      Explore the Island, North/South/East/West/Central, Explore Board,
                     Guides & Packages, guide profiles | models: Region, Destination, Guide, Package
  experiences/       All Events & Activities, Island Calendar, event detail, My Experiences
                     | models: Category, Event
  bookings/          Reserve Your Experience, Secure Checkout, Confirmation
                     | models: Booking, Payment
  admin_dashboard/   Staff dashboard (no models, reads the others)
templates/           base.html (navbar + footer) and partials/ (shared cards)
static/              css/, images/ (design images that are part of the code)
media/               photos uploaded through the admin (NOT in git)
```

Each app keeps its templates in `apps/<app>/templates/<app>/`.

## How the apps talk to each other

They all use the same database, so one app just imports another app's model:

```python
from apps.experiences.models import Event          # in a view
event = models.ForeignKey('experiences.Event', ...) # in a model
```

## The pattern for every dynamic page

1. **Model** (`models.py`): what the data looks like
2. **Admin** (`admin.py`): register it so it can be added at /admin/
3. **View** (`views.py`): fetch it, e.g. `Event.objects.filter(...)`
4. **URL** (`urls.py`): give the page a name
5. **Template**: ONE card inside `{% for %}` instead of many hardcoded cards

Links always use URL names, never typed paths:
`{% url 'experiences:island_calendar' %}`, `{% url 'bookings:reserve' event.slug %}`

## Team rules

1. **Never commit `db.sqlite3` or `media/`** (already in .gitignore).
2. **Do commit migration files.**
3. **Models are frozen.** Need a new field? Post in the group first. Only the
   person who owns that app runs `makemigrations`, then pushes right away.
4. After pulling main, always run: `python manage.py migrate`
5. One branch per page, created from the latest main:
   `git checkout main` -> `git pull` -> `git checkout -b page/island-calendar`
6. Merge into main at least once a day. Small merges = small conflicts.
7. Shared files (`base.html`, `settings.py`, `mauritius_explore/urls.py`):
   change only after telling the group.

## Sharing content (so everyone sees the same data)

One person enters the real content in the admin, then:

```powershell
python manage.py dumpdata destinations experiences --indent 2 -o fixtures/seed.json
```

Commit `fixtures/seed.json`, and share the `media/` folder (Drive/zip). Everyone else runs:

```powershell
python manage.py loaddata fixtures/seed.json
```

## Admin accounts

The 6 team members and the lecturer each get an account with **Staff status**
(or **Superuser**) ticked in /admin/ -> Users. Their Profile role is set to Admin
automatically. Customers sign up normally. Set a user's role to Viewer to allow
browsing only (no bookings).

## Porting your old page into this repo

1. Copy your HTML into the right app's template, change it to
   `{% extends 'base.html' %}` and put the page inside `{% block content %}`.
2. Copy your CSS into `static/css/` and add it with `{% block extra_css %}`.
3. Find repeated hardcoded blocks (cards, rows) and replace them with one
   `{% for %}` loop using the fields listed in the model.
4. Replace every `href="..."` with `{% url '...' %}`.
5. Add real content in /admin/ and check the page.
