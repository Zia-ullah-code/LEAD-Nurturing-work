# Render Deployment Guide

## Comprehensive Guide to Deploy Lead Nurturing Workflow with AI Agent on Render

This guide will walk you through deploying your Django application to Render step by step.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Preparation](#preparation)
3. [Render Account Setup](#render-account-setup)
4. [Database Setup](#database-setup)
5. [Web Service Setup](#web-service-setup)
6. [Environment Variables](#environment-variables)
7. [Deployment Steps](#deployment-steps)
8. [Post-Deployment](#post-deployment)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## Prerequisites

### 1. Required Accounts
- **Render Account**: Sign up at [render.com](https://render.com) (free tier available)
- **GitHub Account**: For version control (or GitLab/Bitbucket)
- **Gmail Account**: For email functionality (or use another SMTP service)
- **Google Cloud Account**: For Gemini API key (optional, if using Gemini AI)

### 2. Required Information
- Gmail App Password (for email sending)
- Gemini API Key (for AI agent functionality)
- Project repository (GitHub/GitLab/Bitbucket)

---

## Preparation

### Step 1: Update Your Repository

Ensure all files are committed and pushed to your repository:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Verify Project Structure

Your project should have the following structure:

```
Lead-nurturing-workflow-with-AI-agent/
├── agent_backend/
│   ├── agent_backend/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── agent_app/
│   ├── manage.py
│   ├── requirements.txt
│   ├── build.sh
│   └── render.yaml
├── ragImplementation/
│   ├── pdfs/
│   └── chroma_db/
└── README.md
```

### Step 3: Prepare Gmail App Password

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Under "App passwords", create a new app password
4. Save this password (you'll need it for EMAIL_HOST_PASSWORD)

---

## Render Account Setup

### Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up for a free account (or log in if you already have one)
3. Verify your email address

### Step 2: Connect Your Repository

1. In Render dashboard, click "New +" → "Web Service"
2. Connect your GitHub/GitLab/Bitbucket account
3. Select your repository: `Lead-nurturing-workflow-with-AI-agent`
4. Choose the branch (usually `main` or `master`)

---

## Database Setup

### Step 1: Create PostgreSQL Database

1. In Render dashboard, click "New +" → "PostgreSQL"
2. Configure the database:
   - **Name**: `lead-nurturing-db` (or your preferred name)
   - **Database**: `lead_nurturing_db`
   - **User**: `lead_nurturing_user`
   - **Region**: Choose closest to your users (e.g., Oregon, Frankfurt)
   - **Plan**: Start with Free tier (upgrade as needed)
3. Click "Create Database"
4. **Important**: Save the **Internal Database URL** (you'll need it later)

### Step 2: Get Database Connection String

1. Click on your database in Render dashboard
2. Under "Connections", copy the **Internal Database URL**
3. It should look like: `postgresql://user:password@host:port/database`

---

## Web Service Setup

### Option A: Using render.yaml (Recommended)

1. In Render dashboard, click "New +" → "Blueprint"
2. Connect your repository
3. Render will automatically detect `render.yaml`
4. Review the configuration and click "Apply"

### Option B: Manual Setup

1. In Render dashboard, click "New +" → "Web Service"
2. Connect your repository
3. Configure the service:
   - **Name**: `lead-nurturing-agent`
   - **Environment**: `Python 3`
   - **Region**: Same as your database
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: `agent_backend`
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn agent_backend.wsgi:application --bind 0.0.0.0:$PORT`

---

## Environment Variables

### Step 1: Set Environment Variables in Render

Go to your web service → Environment tab and add the following variables:

#### Required Variables

```bash
# Django Settings
SECRET_KEY=your-secret-key-here  # Generate a strong secret key
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com  # Replace with your actual Render URL
DJANGO_SETTINGS_MODULE=agent_backend.settings
RENDER=true

# Database (Automatically set by Render if using Internal Database URL)
DATABASE_URL=postgresql://user:password@host:port/database  # Use Internal Database URL

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password  # Use Gmail App Password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Gemini API (for AI agent)
GEMINI_API_KEY=your-gemini-api-key-here

# ChromaDB Paths (for RAG)
CHROMA_DB_PATH=/opt/render/project/src/ragImplementation/chroma_db
RAG_PDFS_PATH=/opt/render/project/src/ragImplementation/pdfs
```

#### Optional Variables

```bash
# Vanna API (for T2SQL, if using)
VANNA_API_KEY=your-vanna-api-key-here
VANNA_MODEL=your-vanna-model-name

# Logging
DJANGO_LOG_LEVEL=INFO
```

### Step 2: Generate Secret Key

Generate a secure secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and use it as your `SECRET_KEY`.

---

## Deployment Steps

### Step 1: Initial Deployment

1. After configuring your web service, click "Create Web Service"
2. Render will start building your application
3. Monitor the build logs for any errors
4. Once build completes, your app will be deployed

### Step 2: Run Migrations

After first deployment, run migrations:

1. Go to your web service → Shell
2. Run: `python manage.py migrate`
3. (Optional) Create superuser: `python manage.py createsuperuser`

### Step 3: Initialize ChromaDB

1. Go to your web service → Shell
2. Navigate to ragImplementation directory:
   ```bash
   cd ../ragImplementation
   python rag_main.py
   ```
3. This will build the ChromaDB from PDFs in the `pdfs` folder

### Step 4: Verify Deployment

1. Visit your app URL: `https://your-app.onrender.com`
2. Test the API: `https://your-app.onrender.com/api/hello`
3. Check admin panel: `https://your-app.onrender.com/admin`

---

## Post-Deployment

### Step 1: Set Up Static Files

Static files should be automatically collected during build. Verify:

1. Check build logs for "Collecting static files"
2. Verify static files are accessible at `/static/`

### Step 2: Set Up Media Files

For user uploads (PDFs), you may need to:

1. Use Render's persistent disk (for small files)
2. Or use cloud storage (S3, Cloudinary) for larger files

### Step 3: Configure Custom Domain (Optional)

1. Go to your web service → Settings
2. Under "Custom Domain", add your domain
3. Follow Render's instructions to configure DNS

### Step 4: Set Up Background Jobs (Optional)

For periodic tasks (like fetching email replies):

1. Create a Cron Job in Render
2. Set schedule: `0 * * * *` (every hour)
3. Command: `cd /opt/render/project/src/agent_backend && python manage.py shell -c "from agent_app.fetch_replies import fetch_lead_replies; fetch_lead_replies()"`

---

## Troubleshooting

### Common Issues

#### 1. Build Fails

**Error**: `ModuleNotFoundError` or `ImportError`

**Solution**:
- Check `requirements.txt` includes all dependencies
- Verify Python version matches (3.11.0)
- Check build logs for specific missing packages

#### 2. Database Connection Error

**Error**: `could not connect to server`

**Solution**:
- Verify `DATABASE_URL` is set correctly
- Use **Internal Database URL** (not external)
- Check database is running and accessible

#### 3. Static Files Not Loading

**Error**: `404 Not Found` for static files

**Solution**:
- Verify `STATIC_ROOT` is set correctly
- Check `build.sh` includes `collectstatic`
- Verify WhiteNoise is installed and configured

#### 4. ChromaDB Path Issues

**Error**: `Permission denied` or `Path not found`

**Solution**:
- Verify `CHROMA_DB_PATH` environment variable
- Check directories are created in `build.sh`
- Use absolute paths on Render

#### 5. Email Not Sending

**Error**: `SMTP Authentication Error`

**Solution**:
- Verify Gmail App Password is correct
- Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
- Ensure 2-Step Verification is enabled on Gmail

#### 6. Application Crashes on Startup

**Error**: Application fails to start

**Solution**:
- Check logs in Render dashboard
- Verify all environment variables are set
- Check `startCommand` is correct
- Verify port is set to `$PORT`

### Debugging Tips

1. **Check Logs**: Go to your web service → Logs tab
2. **Use Shell**: Go to your web service → Shell for debugging
3. **Test Locally**: Test with production settings locally first
4. **Check Environment**: Verify all environment variables are set

---

## Maintenance

### Regular Tasks

1. **Update Dependencies**: Regularly update `requirements.txt`
2. **Database Backups**: Render provides automatic backups for paid plans
3. **Monitor Logs**: Check logs regularly for errors
4. **Update Secrets**: Rotate API keys and passwords periodically

### Scaling

1. **Upgrade Plan**: Upgrade to Standard or Pro plan for more resources
2. **Add Workers**: Increase number of workers for Gunicorn
3. **Database Upgrade**: Upgrade database plan for more storage/connections
4. **CDN**: Use CDN for static files (included in Render)

### Backup Strategy

1. **Database Backups**: Render provides automatic backups
2. **ChromaDB Backups**: Backup ChromaDB directory regularly
3. **PDF Backups**: Backup PDF files in `ragImplementation/pdfs`
4. **Environment Variables**: Document all environment variables

---

## Important Notes

### 1. Free Tier Limitations

- Services spin down after 15 minutes of inactivity
- Limited resources (512MB RAM, 0.5 CPU)
- Limited database storage (1GB)
- Consider upgrading for production use

### 2. ChromaDB Persistence

- ChromaDB data is stored on disk
- Use Render's persistent disk for data persistence
- Consider backing up ChromaDB regularly

### 3. Email Limitations

- Gmail has daily sending limits
- Consider using dedicated email service for production
- Monitor email sending quotas

### 4. Security

- Never commit secrets to repository
- Use environment variables for all secrets
- Enable HTTPS (automatically provided by Render)
- Regularly update dependencies

---

## Quick Reference

### Render Dashboard URLs

- **Web Service**: `https://dashboard.render.com/web/[service-id]`
- **Database**: `https://dashboard.render.com/databases/[database-id]`
- **Logs**: Available in web service dashboard

### Useful Commands

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --no-input

# Shell access
python manage.py shell

# Check deployment
curl https://your-app.onrender.com/api/hello
```

### Support Resources

- **Render Documentation**: https://render.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **Render Community**: https://community.render.com

---

## Conclusion

Your application should now be successfully deployed on Render! 

If you encounter any issues, refer to the troubleshooting section or check Render's documentation.

For additional help, contact Render support or check the Render community forum.

---

## Next Steps

1. ✅ Verify deployment is working
2. ✅ Set up monitoring and alerts
3. ✅ Configure custom domain (optional)
4. ✅ Set up automated backups
5. ✅ Monitor performance and scale as needed

Good luck with your deployment! 🚀

