# 🚀 Deploying Your Attendance System to Dokploy — Complete Beginner Guide

This guide walks you through deploying your Django Attendance System to **Dokploy** using Dokploy's **auto-generated domain** (no custom domain needed).

---

## What You Already Have (✅ Ready)

Your project is already well-prepared for deployment:

| Item | Status | File |
|------|--------|------|
| Dockerfile | ✅ Ready | [Dockerfile](file:///c:/Users/adupo/DjangoLearning/Attendance_sys/Dockerfile) |
| Gunicorn | ✅ In requirements | [requirements.txt](file:///c:/Users/adupo/DjangoLearning/Attendance_sys/requirements.txt) |
| WhiteNoise (static files) | ✅ Configured | [settings.py](file:///c:/Users/adupo/DjangoLearning/Attendance_sys/core/settings.py) |
| dj-database-url | ✅ Configured | [settings.py](file:///c:/Users/adupo/DjangoLearning/Attendance_sys/core/settings.py) |
| .dockerignore | ✅ Ready | [.dockerignore](file:///c:/Users/adupo/DjangoLearning/Attendance_sys/.dockerignore) |
| GitHub Repo | ✅ Connected | `AduOseiPoku/Attendance_sys` |

---

## What You Need to Fix Before Deploying

> [!IMPORTANT]
> There is **one small code change** you must make before deploying. Your `settings.py` currently has the CSRF trusted origins defaulting to Railway. We need to update it so Dokploy's auto-generated domain works properly.

### Fix: Update CSRF Trusted Origins in settings.py

Open [settings.py](file:///c:/Users/adupo/DjangoLearning/Attendance_sys/core/settings.py) and **replace lines 150–159** (the CSRF section at the bottom) with:

```python
# CSRF Trusted Origins for production security
CSRF_TRUSTED_ORIGINS_ENV = config('CSRF_TRUSTED_ORIGINS', default='')
if CSRF_TRUSTED_ORIGINS_ENV:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS_ENV.split(',')]
else:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]
```

> [!NOTE]
> We removed `'https://*.up.railway.app'` (that was for Railway, not Dokploy). You'll set the correct Dokploy domain via the `CSRF_TRUSTED_ORIGINS` environment variable inside Dokploy later — I'll tell you exactly what to type.

---

## Step-by-Step Deployment

### STEP 1: Push Your Code to GitHub

Before deploying, you need to make sure all your latest files (including the Dockerfile and the settings fix above) are pushed to GitHub.

**Open your terminal (PowerShell or CMD) and run these commands one by one:**

```bash
cd c:\Users\adupo\DjangoLearning\Attendance_sys
```

```bash
git add .
```

```bash
git commit -m "prepare for dokploy deployment"
```

```bash
git push origin main
```

> [!TIP]
> If `git push origin main` gives an error, try `git push origin master` instead. Your default branch might be called `master`.

**How to check if it worked:** Go to `https://github.com/AduOseiPoku/Attendance_sys` in your browser. You should see your Dockerfile and updated settings.py there.

---

### STEP 2: Log Into Dokploy

1. Open your browser
2. Go to your Dokploy dashboard URL (this is the URL your Dokploy server is running on, for example: `https://your-server-ip:3000` or wherever you installed Dokploy)
3. Log in with your Dokploy username and password

> [!NOTE]
> If you haven't installed Dokploy yet, you need a VPS (Virtual Private Server) first. You can get one from providers like Hetzner, DigitalOcean, or Vultr. Then install Dokploy by SSHing into your server and running:
> ```bash
> curl -sSL https://dokploy.com/install.sh | sh
> ```
> After installation, Dokploy will give you a URL to access the dashboard.

---

### STEP 3: Create a New Project

1. Once logged in, click the **"Projects"** button in the left sidebar
2. Click the **"+ Create Project"** button
3. Give it a name — type: `Attendance System`
4. Click **"Create"**
5. Click on the project you just created to open it

---

### STEP 4: Create a PostgreSQL Database

Your app uses PostgreSQL, so we need to create a database first.

1. Inside your project, click **"+ Create Service"**
2. Select **"Database"**
3. Select **"PostgreSQL"**
4. Give it a name — type: `attendance-db`
5. Click **"Create"**
6. Click on the `attendance-db` service to open its settings

**Now configure the database:**

7. You'll see fields for the database. Set the following:
   - **Database Name:** `attendance_db`
   - **Database User:** `attendance_admin`
   - **Database Password:** Click "Generate" or type a strong password (write this down! You'll need it soon)

8. Click **"Deploy"** to start the database

9. **Get the Internal Connection URL:**
   - After the database deploys, look for a section called **"Internal Connection URL"** or **"Connection String"**
   - It will look something like: `postgresql://attendance_admin:YOUR_PASSWORD@attendance-db:5432/attendance_db`
   - **Copy this entire URL** — you'll need it in the next steps

> [!IMPORTANT]
> Use the **Internal** connection URL (not the external one). The internal one uses the container name (like `attendance-db`) instead of an IP address. This lets your Django app talk to the database inside Dokploy's internal network, which is faster and more secure.

---

### STEP 5: Create the Django Application Service

1. Go back to your project (click the project name at the top)
2. Click **"+ Create Service"**
3. Select **"Application"**
4. Give it a name — type: `attendance-app`
5. Click **"Create"**
6. Click on `attendance-app` to open its settings

---

### STEP 6: Connect Your GitHub Repository

1. Inside the `attendance-app` service, go to the **"General"** tab
2. Under **"Source"**, select **"GitHub"**
3. If this is your first time, Dokploy will ask you to connect your GitHub account:
   - Click **"Connect GitHub"**
   - A GitHub popup will appear — authorize Dokploy to access your repositories
   - Select your account
4. Once connected, search for and select: **`AduOseiPoku/Attendance_sys`**
5. For **Branch**, select: `main` (or `master` — whichever your repo uses)
6. For **Build Type**, select: **"Dockerfile"**
   - Dokploy will automatically find and use your `Dockerfile` in the root of the repo
7. Click **"Save"**

---

### STEP 7: Set Environment Variables

This is a crucial step. Your Django app needs these variables to run properly.

1. In the `attendance-app` service, click the **"Environment"** tab
2. You'll see a text area where you can add environment variables
3. Paste the following (replace the values in `< >` with your actual values):

```env
DATABASE_URL=<paste the Internal Connection URL from Step 4 here>
SECRET_KEY=<generate a random secret key — see below>
DEBUG=False
ALLOWED_HOSTS=*
```

**How to generate a SECRET_KEY:**

You can use any random string generator. Here's a quick way — go to this website in your browser: `https://djecrety.ir/` and click "Generate". Copy the result and paste it as the value for `SECRET_KEY`.

Or type any long random string like: `my-super-secret-key-a8f3k2j5h6g7d8s9a0`

> [!WARNING]
> Do NOT add `CSRF_TRUSTED_ORIGINS` yet — we'll add it after we get the auto-generated domain in the next step.

4. Click **"Save"**

---

### STEP 8: Deploy the Application (First Deploy)

1. Go to the **"Deployments"** tab
2. Click **"Deploy"**
3. Wait for the build to complete — you'll see build logs appear in real-time
4. This first deploy might take 2-5 minutes as it downloads Python packages

**What happens during the deploy:**
- Dokploy builds your Docker image using your Dockerfile
- It runs `collectstatic` (gathers all CSS/JS files)
- It runs `migrate` (creates all database tables)
- It starts Gunicorn (your web server)

> [!TIP]
> If the build fails, check the **build logs** for error messages. Common issues:
> - **"Connection refused" for database:** Make sure the DATABASE_URL uses the internal connection URL and the database service is running
> - **"Module not found":** A package might be missing from requirements.txt

---

### STEP 9: Get Your Auto-Generated Domain

After the deploy succeeds:

1. Go to the **"Domains"** tab of your `attendance-app` service
2. Click **"Generate Domain"** (this button creates a free auto-generated domain for you)
3. Dokploy will create a domain that looks something like:
   ```
   attendance-app-xxxx-xxxx.traefik.me
   ```
   or
   ```
   attendance-app-xxxxx.dokploy.com
   ```
   (The exact format depends on your Dokploy server configuration)

4. **Copy the full generated domain** (including `https://`)

> [!IMPORTANT]
> The generated domain format depends on your Dokploy version and server setup. It will be shown clearly in the Domains tab. Whatever domain Dokploy shows you, that's your app's URL.

---

### STEP 10: Add CSRF_TRUSTED_ORIGINS (Critical!)

Now that you have your domain, you need to tell Django to trust it.

1. Go back to the **"Environment"** tab
2. **Add this new line** to your environment variables:

```env
CSRF_TRUSTED_ORIGINS=https://your-generated-domain-here
```

**Example** (replace with YOUR actual domain):
```env
CSRF_TRUSTED_ORIGINS=https://attendance-app-abc123.traefik.me
```

3. Click **"Save"**

> [!CAUTION]
> If you skip this step, you'll get **403 Forbidden** errors whenever you try to log in or submit any form on your site.

---

### STEP 11: Redeploy

After adding `CSRF_TRUSTED_ORIGINS`, you need to redeploy for the change to take effect:

1. Go to the **"Deployments"** tab
2. Click **"Deploy"** again
3. Wait for it to finish (this time it's usually faster because the Docker layers are cached)

---

### STEP 12: Visit Your Live Site! 🎉

1. Open your browser
2. Go to: `https://your-generated-domain-here` (the domain from Step 9)
3. You should see your Attendance System live!

---

### STEP 13: Create Your Admin/Superuser Account

You need a superuser to access the Django admin panel and manage data.

1. In Dokploy, go to your `attendance-app` service
2. Go to the **"Advanced"** tab → **"Terminal"** (some Dokploy versions have it under "Logs" → "Terminal", or "Console")
3. If Dokploy has a terminal/console feature, run:

```bash
python manage.py createsuperuser
```

4. Enter a username, email, and password when prompted

**If Dokploy doesn't have a built-in terminal**, you can SSH into your server and run:

```bash
docker exec -it <container-name> python manage.py createsuperuser
```

To find the container name, run:
```bash
docker ps
```

Look for the container with `attendance-app` in the name.

5. After creating the superuser, go to: `https://your-generated-domain/admin/` to access the admin panel

---

## Summary of All Environment Variables

Here's the complete list of environment variables you should have in Dokploy:

| Variable | Value | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | `postgresql://attendance_admin:PASSWORD@attendance-db:5432/attendance_db` | Connects to your PostgreSQL database |
| `SECRET_KEY` | A long random string | Django's cryptographic signing key |
| `DEBUG` | `False` | Turns off debug mode for production |
| `ALLOWED_HOSTS` | `*` | Allows all hostnames (your settings.py already has this) |
| `CSRF_TRUSTED_ORIGINS` | `https://your-generated-domain` | Tells Django to trust your Dokploy domain |

---

## Troubleshooting Common Issues

### ❌ "502 Bad Gateway" after deploy
- **Cause:** The app crashed during startup
- **Fix:** Check the deployment logs for errors. Most likely the `DATABASE_URL` is wrong or the database isn't running

### ❌ "403 Forbidden" on login/forms
- **Cause:** `CSRF_TRUSTED_ORIGINS` is missing or wrong
- **Fix:** Make sure the value in `CSRF_TRUSTED_ORIGINS` exactly matches your generated domain, including `https://`

### ❌ "Static files not loading" (CSS looks broken)
- **Cause:** WhiteNoise might not be collecting static files
- **Fix:** You already have WhiteNoise configured correctly. Make sure the deploy logs show `collectstatic` running successfully

### ❌ "Connection refused" for database
- **Cause:** Using external URL instead of internal, or database service not running
- **Fix:** Use the **Internal Connection URL** and make sure the PostgreSQL service shows as "Running" in Dokploy

### ❌ Build fails with "no matching manifest for linux/amd64"
- **Cause:** Your Dokploy server might be ARM-based
- **Fix:** Change the first line of your Dockerfile from `FROM python:3.11-slim` to `FROM --platform=linux/arm64 python:3.11-slim`

---

## Setting Up Auto-Deploy (Optional but Recommended)

To make Dokploy automatically redeploy every time you push code to GitHub:

1. In your `attendance-app` service, go to **"General"** tab
2. Look for **"Auto Deploy"** or **"Webhook"** option
3. Toggle it **ON**
4. Now every `git push` to your main branch will trigger a new deployment automatically!

---

## Quick Reference: Your Key URLs

| What | URL |
|------|-----|
| Your live site | `https://your-generated-domain` |
| Django admin panel | `https://your-generated-domain/admin/` |
| Church owner login | `https://your-generated-domain/owner/login/` |
| Dokploy dashboard | `https://your-server-ip:3000` |
