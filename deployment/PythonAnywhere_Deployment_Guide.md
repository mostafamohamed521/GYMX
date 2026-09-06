# Deploying GymX to PythonAnywhere

Step-by-step guide, in order. Follow it from start to finish.

---

## Before you start

- **Rotate the Gmail App Password immediately** at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) — the old value was exposed to a third-party AI tool during development and must be changed before any real deployment.
- Create an account at [pythonanywhere.com](https://www.pythonanywhere.com) — the free plan is fine to try things out; you'll want a paid plan ($5+/month, "Hacker") if you need a custom domain or better performance.

---

## Step 1: Upload the code

1. From the PythonAnywhere dashboard, open the **Files** tab.
2. Upload the zipped project (`gymx_project_full.zip`) into `/home/YOURUSERNAME/`.
3. Open the **Consoles** tab → start a new **Bash console**.
4. Unzip it:
   ```bash
   cd ~
   unzip gymx_project_full.zip -d gymx
   cd gymx
   ```

---

## Step 2: Set up the virtualenv

In the same Bash console:

```bash
mkvirtualenv --python=/usr/bin/python3.12 gymx-venv
pip install -r requirements.txt
```

> Note: `requirements.txt` is UTF-16 encoded — `pip install -r` handles that correctly on its own, no extra steps needed.

If any package fails to install, try:
```bash
pip install -r requirements.txt --no-cache-dir
```

---

## Step 3: Set up the database (MySQL)

1. From the **Databases** tab, set a password for your MySQL server (first time only).
2. Under "Create a database", type `gymx` and click Create.
   - The full database name will look like `YOURUSERNAME$gymx`.
3. Note the host shown (looks like `YOURUSERNAME.mysql.pythonanywhere-services.com`).

---

## Step 4: Set up the `.env` file

In the Bash console:
```bash
cd ~/gymx
nano .env
```

Paste the contents of the included `.env.production.template` file, and fill in:
- Every `YOURUSERNAME` placeholder → your actual PythonAnywhere username
- `DB_PASSWORD` → the MySQL password you set in step 3
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` → your email and the **new** App Password (after rotating it)
- Twilio credentials if you have them, otherwise leave them blank (the site works fine without them — SMS just won't send)

Save with `Ctrl+O` then `Enter`, exit with `Ctrl+X`.

---

## Step 5: Run migrations

```bash
workon gymx-venv
cd ~/gymx
python manage.py migrate
python manage.py createsuperuser
```
(you'll be asked for a username/email/password for your first admin account)

---

## Step 6: Collect static files

```bash
python manage.py collectstatic --noinput
```
This gathers all CSS/JS/image files into one `staticfiles/` folder, ready to be served quickly.

---

## Step 7: Create the Web App

1. From the **Web** tab, click **Add a new web app**.
2. Choose **Manual configuration** (not the ready-made "Django" option — this project has a custom structure).
3. Choose **Python 3.12**.

---

## Step 8: Set the virtualenv

On the same Web tab page, under **Virtualenv**, enter:
```
/home/YOURUSERNAME/.virtualenvs/gymx-venv
```

---

## Step 9: Set up the WSGI file

1. Under the **Code** section, click the **WSGI configuration file** link.
2. Delete everything there, and paste the contents of the included `pythonanywhere_wsgi.py` file (after replacing `YOURUSERNAME` with your real username).
3. Save.

---

## Step 10: Set up Static/Media file mappings

On the same Web tab, under **Static files**, add these two entries:

| URL | Directory |
|---|---|
| `/static/` | `/home/YOURUSERNAME/gymx/staticfiles` |
| `/media/` | `/home/YOURUSERNAME/gymx/media` |

---

## Step 11: Launch the site

Click the green **Reload** button at the top of the Web tab.

Open `https://YOURUSERNAME.pythonanywhere.com` — the site should load and work.

---

## Important notes about the free tier

Researched these specifically to confirm the project will actually work correctly even on the free plan:

- **HTTPS redirect loop (already fixed for you):** the project's security settings force HTTPS redirects once `DEBUG=False`. Behind PythonAnywhere's proxy (or any reverse proxy that terminates SSL), Django can't tell a request was HTTPS unless it's told — without `SECURE_PROXY_SSL_HEADER` set correctly, this causes every single request to redirect to itself forever, taking the whole site down. This is already fixed in `config/settings.py` in the files you have — nothing you need to do, just worth knowing why it's there.
- **Email (Gmail SMTP):** the free tier blocks regular SMTP connections, but PythonAnywhere has a specific firewall exception for Gmail's servers — so `EMAIL_HOST=smtp.gmail.com` should work even on the free plan. The exception is IP-based and can lag if Google changes IPs, so occasional email delivery hiccups are possible; if it becomes a persistent problem, upgrading to a paid plan removes the restriction entirely.
- **SMS (Twilio):** `api.twilio.com` is explicitly on the free-tier allowlist, so the SMS feature should work without any upgrade needed.
- **Database (MySQL):** PythonAnywhere's own MySQL service isn't subject to the internet restrictions at all (it's internal), so no concerns there.
- **No Celery or background workers in this project** — everything runs synchronously within the request itself, which is exactly what a standard web app supports without needing the paid "Always-on tasks" feature.
- **Project size is only 44 MB** — comfortably under the free 512 MB quota.

---

## If something goes wrong

- Open the **Error log** from the Web tab (under the Logs section) — this is the most useful place to find out what's wrong.
- Common issues:
  - Forgot to replace `YOURUSERNAME` somewhere (the WSGI file or `.env`)
  - Wrong virtualenv path
  - Forgot `collectstatic` — the site loads but with no styling (CSS)

---

## After it's live

- Try registering a new member, log in as admin, and click through the main pages yourself.
- Every time you update the code and re-upload it:
  ```bash
  workon gymx-venv
  cd ~/gymx
  python manage.py migrate                    # if there's a new migration
  python manage.py collectstatic --noinput     # if you changed CSS/JS
  ```
  then hit **Reload** on the Web tab again.
