# 🏋️ GymX — Complete Gym Management Ecosystem

<div align="center">

**A full-scale, production-style Django 5 platform for running a modern fitness business —
from the front desk to the boardroom, from the treadmill to the terms & conditions page.**

*22 Sprints · 22 Django Apps · 370 Templates · 5 Roles · 1 Codebase*

</div>

---

## 📖 What is GymX?

GymX started as a simple gym management system and grew — sprint by sprint — into a
complete digital operating system for a fitness business. It covers **everything**:
member check-ins, payroll, point-of-sale, multi-branch operations, a public marketing
website, an AI-powered insights engine, and even its own maintenance mode and error pages.

Every module was built the same way: real Django models, real relationships, real
permission checks, real seed data — and tested by actually logging in as each role and
confirming what breaks and what doesn't.

---

## 🧭 Table of Contents

- [Quick Start](#-quick-start)
- [Who Can Do What — Role-Based Access](#-who-can-do-what--role-based-access)
- [The Full Sprint Map](#-the-full-sprint-map)
- [Architecture Notes](#-architecture-notes)
- [Project Structure](#-project-structure)
- [Demo Accounts](#-demo-accounts)
- [Seeding Data](#-seeding-data)
- [Deployment Checklist](#-deployment-checklist)
- [Known Limitations](#-known-limitations--honest-notes)

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install django pillow python-dateutil python-decouple qrcode python-barcode twilio --break-system-packages

# 2. Set up the database
python manage.py migrate

# 3. Seed everything (run in this order — later apps depend on earlier data)
python manage.py seed_demo
python manage.py seed_members
python manage.py seed_memberships
python manage.py seed_attendance
python manage.py seed_payments
python manage.py seed_coaches
python manage.py seed_workouts
python manage.py seed_nutrition
python manage.py seed_classes
python manage.py seed_hr
python manage.py seed_inventory
python manage.py seed_pos
python manage.py seed_branches
python manage.py seed_crm
python manage.py seed_reports
python manage.py seed_notifications
python manage.py seed_finance
python manage.py seed_settings
python manage.py seed_portal
python manage.py seed_website
python manage.py seed_aifeatures
python manage.py seed_system

# 4. Link the demo Coach/Member accounts to real profiles (do this last)
python manage.py link_demo_accounts

# 5. Run it
python manage.py runserver
```

Then open **http://127.0.0.1:8000** and sign in with any account from the
[Demo Accounts](#-demo-accounts) table below.

---

## 🔐 Who Can Do What — Role-Based Access

This isn't a system where everyone sees everything. Every page is gated by role, and the
sidebar itself only shows links a person can actually open — no dead ends, no "Access
Denied" surprises after clicking.

| Role | Sees in Sidebar | Can't Access |
|---|---|---|
| **Super Admin** | Everything | — |
| **Gym Manager** | Everything except a few super-admin-only system internals | System-level backups/restores in edge cases |
| **Receptionist** | Members, Memberships, Coaches, Attendance, Classes, Workouts, Nutrition, CRM, Payments, POS, Notifications, Help Center | HR, Branches, Inventory, Reports, Finance, AI, Settings, System |
| **Coach** | Their own coaching tools: Coaches, Classes, Workouts, Nutrition, Help Center | Everything front-desk/admin-only, including CRM |
| **Member** | Just "My Portal" — a single hub linking to their membership, payments, attendance, workouts, nutrition, classes, coach, QR code, membership card, and support tickets | Literally everything else — the portal is self-contained |

**How it's enforced (not just hidden):**
```python
# apps/accounts/permissions.py
@role_required(*ADMIN_ROLES)
def some_admin_view(request):
    ...
```
Every sensitive view is wrapped in a `role_required` decorator backed by five reusable
role groups (`ADMIN_ROLES`, `FRONT_DESK_ROLES`, `STAFF_ROLES`, `COACH_ROLES`, `ALL_ROLES`).
If someone bypasses the sidebar and types a restricted URL directly, they're redirected
straight back to their own dashboard — the hidden link was never the only line of defense.

The dashboard itself is also role-aware: four completely different homepages
(`index_admin.html`, `index_receptionist.html`, `index_coach.html`, `index_member.html`)
pulling live data relevant to that person, not a generic one-size-fits-all screen.

---

## 🗺️ The Full Sprint Map

| # | Sprint | Highlights |
|---|---|---|
| 1–6 | **Foundations** | Auth, Members, Memberships, Attendance, Payments, Coaches |
| 7–8 | **Wellness** | Workout plans & exercise library, Nutrition plans & calculators |
| 9–10 | **Operations** | Class scheduling & waitlists, HR/Employees/Payroll |
| 11–12 | **Commerce** | Inventory & equipment tracking, full POS with discounts & gift cards |
| 13 | **Branch Management** | Multi-branch support, member/employee transfers |
| 14 | **CRM** | Leads, follow-ups, call logs, loyalty & referral programs, campaigns |
| 15 | **Reports & Analytics** | Revenue, membership, attendance, P&L, KPI dashboards |
| 16 | **Notifications** | Email/SMS templates, announcements, birthday & expiry alerts |
| 17 | **Finance** | Double-entry-style chart of accounts, journal entries, general ledger |
| 18 | **Settings & Security** | System settings, business hours, password policy, audit logs |
| 19 | **Member Portal** | Full self-service hub for members — membership, QR code, tickets |
| 20 | **Public Website** | Standalone marketing site — home, blog, careers, contact, legal pages |
| 21 | **AI & Smart Features** | Churn prediction, revenue/attendance forecasting, AI workout & nutrition generators, chat assistant |
| 22 | **Final Release & System** | Custom error pages, maintenance mode, system status, docs, changelog |

Every sprint shipped with: real models and migrations, a seed command, full CRUD views,
and — from Sprint 13 onward — a live permission test confirming the right roles get in
and the wrong ones get redirected.

---

## 🏗️ Architecture Notes

- **One Django app per business domain.** No god-app. `apps/payments`, `apps/coaches`,
  `apps/finance`, etc. each own their models, views, urls, templates, and seed command.
- **Existing models are reused, never duplicated.** When a later sprint needed something
  an earlier sprint already built (`Notification`, `LoginHistory`, `Role`/`Permission`,
  Branch Settings), it imports and extends that model instead of creating a shadow copy.
- **A single source of truth for role groups** (`apps/accounts/permissions.py`) — every
  app imports from here rather than re-defining its own role logic.
- **The sidebar and the view permissions are driven by the same role flags**
  (`is_admin_role`, `is_front_desk_role`, `is_coach_role`, `is_member_role`), injected
  globally via `config/context_processors.py` and registered in `TEMPLATES` — so what a
  person sees in navigation always matches what they're actually allowed to open.
- **AI features are genuinely rule-based, not fake.** Churn scores are computed from real
  attendance gaps, subscription expiry, and pending payments. Revenue/attendance forecasts
  use real historical trend extrapolation. The nutrition advisor uses the actual
  Mifflin-St Jeor formula. Nothing is a hard-coded placeholder number.

---

## 📁 Project Structure

```
GymX/
├── apps/
│   ├── accounts/        # Auth, User model, roles, permissions.py (the RBAC core)
│   ├── dashboard/       # Role-aware dashboard router
│   ├── members/ … pos/  # Sprints 1–12 (core gym operations)
│   ├── branches/        # Sprint 13
│   ├── crm/             # Sprint 14
│   ├── reports/         # Sprint 15
│   ├── notifications/   # Sprint 16
│   ├── finance/         # Sprint 17
│   ├── settings/        # Sprint 18 (app label: gymsettings)
│   ├── portal/          # Sprint 19 (member self-service)
│   ├── website/         # Sprint 20 (public marketing site, app_name: website)
│   ├── aifeatures/      # Sprint 21
│   └── system/          # Sprint 22 (app label: coresystem)
├── config/
│   ├── settings.py
│   ├── urls.py          # includes handler403/404/500 wiring
│   └── context_processors.py
├── templates/
│   ├── base.html                # admin/dashboard shell (with sidebar)
│   ├── includes/sidebar.html    # the role-aware navigation — single source of truth
│   └── <app_name>/*.html        # one folder per app, mirroring apps/
└── static/
    └── css/, js/
```

---

## 👤 Demo Accounts

All passwords: `GymX@2024`

| Email | Role | Notes |
|---|---|---|
| `superadmin@gymx.com` | Super Admin | Full access |
| `manager@gymx.com` | Gym Manager | Full operational access |
| `reception@gymx.com` | Receptionist | Front-desk scope |
| `ahmed.coach@gymx.com` | Coach | Linked to a real Coach profile with assigned members |
| `john@gymx.com` | Member | Linked to a real Member profile with an active subscription |

> Run `python manage.py link_demo_accounts` after seeding — it's what connects
> `ahmed.coach@gymx.com` and `john@gymx.com` to actual Coach/Member records and gives
> them realistic data (attendance history, an active subscription, assigned members,
> a PT session) so their dashboards aren't empty on first login.

---

## 🌱 Seeding Data

Every app ships its own `seed_<app_name>` management command, and every one is
idempotent (`get_or_create` everywhere) — safe to re-run without duplicating data.
See [Quick Start](#-quick-start) for the full recommended order.

---

## 📦 Deployment Checklist

This project runs with `DEBUG=True` and demo-friendly settings out of the box. Before
putting it anywhere public, `python manage.py check --deploy` will flag the following —
all fixable from **Settings → System** (Sprint 18) or `config/settings.py`:

- [ ] Replace `SECRET_KEY` with a long, random, production value
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS` for your real domain
- [ ] Enable `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`
- [ ] Point `EMAIL_*` / SMS provider settings at real credentials (Sprint 18 → Email/SMS Settings)
- [ ] Swap SQLite for Postgres/MySQL for anything beyond a demo

---

## ⚠️ Known Limitations — Honest Notes

- **The AI Chat Assistant is rule-based (keyword matching), not an LLM.** This is a
  Django backend, not a Claude Artifact — there's no live model call. It's a genuinely
  useful FAQ router, just not generative.
- **A handful of apps (Workouts, Nutrition, Classes, Attendance, Memberships) are
  `login_required` only, not role-restricted at the view level** — any authenticated
  user can technically reach them by URL, even though the sidebar only surfaces them to
  the appropriate roles. Front-desk staff and coaches are meant to use them; members are
  steered to the equivalent Portal pages instead.
- **Payment gateway, SMTP, and SMS settings are configuration placeholders** — the
  Settings pages let you store provider credentials, but no live Stripe/Twilio/SMTP call
  is wired up.
- **The 401 Unauthorized page has no real Django hook** (Django doesn't have a native
  `handler401`); it exists as a styled preview page only, reachable at
  `/system/errors/401/` for design QA.

---

<div align="center">

Built sprint by sprint. Tested role by role. 🏋️‍♂️

</div>
