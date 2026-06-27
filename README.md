# 🏋️ GymX — Gym Management System

> **Sprint 1 — Project Foundation & Authentication**  
> A modern, dark-luxury gym management platform built with Django 5 + PostgreSQL.

---

## ✅ Sprint 1 Deliverables

| Feature | Status |
|---|---|
| Django Project Configuration | ✅ Done |
| PostgreSQL / SQLite Setup | ✅ Done |
| Environment Variables (.env) | ✅ Done |
| Custom User Model | ✅ Done |
| 5 User Roles (RBAC) | ✅ Done |
| Login Page | ✅ Done |
| Logout Functionality | ✅ Done |
| Forgot Password Page | ✅ Done |
| Reset Password Page | ✅ Done |
| Remember Me | ✅ Done |
| User Profile View | ✅ Done |
| Profile Edit | ✅ Done |
| Change Password | ✅ Done |
| Dashboard Layout | ✅ Done |
| Sidebar (collapsible) | ✅ Done |
| Navbar + Dropdowns | ✅ Done |
| Footer | ✅ Done |
| Protected Routes | ✅ Done |
| Base Template | ✅ Done |
| Static & Media Files | ✅ Done |
| Chart.js Visualizations | ✅ Done |
| Demo Seed Command | ✅ Done |
| Django Admin | ✅ Done |
| CSRF Protection | ✅ Done |

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd GymX
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env .env.local
# Edit .env — fill in your DB credentials
```

### 3. Database

```bash
# SQLite (default — no config needed)
python manage.py migrate

# PostgreSQL — uncomment DATABASES block in config/settings.py first
# then: python manage.py migrate
```

### 4. Seed Demo Users

```bash
python manage.py seed_demo
```

### 5. Run Server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 🔐 Demo Credentials

| Username | Password | Role |
|---|---|---|
| `superadmin` | `GymX@2024` | Super Admin |
| `manager` | `GymX@2024` | Gym Manager |
| `receptionist` | `GymX@2024` | Receptionist |
| `coach_ahmed` | `GymX@2024` | Coach |
| `member_john` | `GymX@2024` | Member |

---

## 🏗️ Project Structure

```
GymX/
├── config/
│   ├── settings.py          # Django settings
│   ├── urls.py              # Root URL configuration
│   ├── wsgi.py
│   └── context_processors.py
├── apps/
│   ├── accounts/            # Authentication & User model
│   │   ├── models.py        # Custom User model (5 roles)
│   │   ├── views.py         # Login, logout, profile, password
│   │   ├── forms.py         # All auth forms
│   │   ├── admin.py         # User admin panel
│   │   ├── urls.py
│   │   └── management/
│   │       └── commands/
│   │           └── seed_demo.py
│   └── dashboard/
│       ├── views.py         # Dashboard index
│       └── urls.py
├── templates/
│   ├── base.html            # Master layout
│   ├── includes/
│   │   ├── sidebar.html
│   │   ├── navbar.html
│   │   └── footer.html
│   ├── authentication/
│   │   ├── login.html
│   │   ├── forgot_password.html
│   │   ├── reset_password.html
│   │   ├── profile.html
│   │   ├── profile_edit.html
│   │   └── change_password.html
│   └── dashboard/
│       └── index.html
├── static/
│   ├── css/
│   │   ├── style.css         # Design system
│   │   ├── authentication.css
│   │   └── dashboard.css
│   └── js/
│       └── main.js
├── media/                   # User uploads
├── requirements.txt
├── .env
└── manage.py
```

---

## 🎨 Design System

| Token | Value |
|---|---|
| Background | `#0A0A0F` |
| Surface | `#16161F` |
| Primary Purple | `#6C63FF` |
| Accent Teal | `#00D4AA` |
| Accent Pink | `#FF6B9D` |
| Font Display | Rajdhani |
| Font Body | Inter |

---

## 🔒 User Roles

| Role | Access |
|---|---|
| Super Admin | Full system access |
| Gym Manager | Members, coaches, memberships, reports |
| Receptionist | Register members, payments, attendance |
| Coach | Assigned members, workout plans |
| Member | Profile, membership, attendance, workouts |

---

## 🛠️ Tech Stack

- **Backend:** Django 5.0, Python 3.12
- **Database:** PostgreSQL (SQLite for dev)
- **ORM:** Django ORM
- **Auth:** Custom `AbstractBaseUser`
- **Frontend:** Django Templates, Bootstrap 5, Chart.js, Font Awesome 6
- **Fonts:** Inter + Rajdhani (Google Fonts)
- **Config:** python-decouple

---

*Sprint 1 of GymX — Built with precision 💜*
