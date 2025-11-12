# Quick Start: Deploy to Render

## 5-Minute Deployment Guide

### Step 1: Prepare Your Repository (2 minutes)

1. **Commit all changes:**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Verify files are in repository:**
   - `agent_backend/build.sh`
   - `agent_backend/render.yaml`
   - `agent_backend/requirements.txt`
   - `agent_backend/runtime.txt`

### Step 2: Create Render Account (1 minute)

1. Go to [render.com](https://render.com)
2. Sign up (free tier available)
3. Verify your email

### Step 3: Deploy Database (1 minute)

1. In Render dashboard, click "New +" → "PostgreSQL"
2. Name: `lead-nurturing-db`
3. Region: Choose closest to you
4. Plan: Free (or upgrade as needed)
5. Click "Create Database"
6. **Save the Internal Database URL** (you'll need it)

### Step 4: Deploy Web Service (1 minute)

1. In Render dashboard, click "New +" → "Blueprint"
2. Connect your repository
3. Select your repository: `Lead-nurturing-workflow-with-AI-agent`
4. Render will detect `render.yaml` automatically
5. Click "Apply"

### Step 5: Configure Environment Variables

Go to your web service → Environment tab and add:

```bash
# Required
SECRET_KEY=<generate-or-use-render-auto-generated>
DEBUG=False
RENDER=true
GEMINI_API_KEY=your-gemini-api-key

# Email (use Gmail App Password)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Database (automatically set if using Internal Database URL)
DATABASE_URL=<from-database-settings>

# ChromaDB Paths
CHROMA_DB_PATH=/opt/render/project/src/ragImplementation/chroma_db
RAG_PDFS_PATH=/opt/render/project/src/ragImplementation/pdfs
```

### Step 6: Deploy and Verify

1. **Wait for build to complete** (5-10 minutes)
2. **Check build logs** for any errors
3. **Visit your app URL**: `https://your-app.onrender.com`
4. **Test API**: `https://your-app.onrender.com/api/hello`

### Step 7: Run Migrations

1. Go to your web service → Shell
2. Run: `python manage.py migrate`
3. (Optional) Create superuser: `python manage.py createsuperuser`

### Step 8: Initialize ChromaDB (Optional)

1. Go to your web service → Shell
2. Run:
   ```bash
   cd ../ragImplementation
   python rag_main.py
   ```

---

## Common Issues & Quick Fixes

### Build Fails
- **Check**: `requirements.txt` includes all dependencies
- **Fix**: Add missing packages to `requirements.txt`

### Database Connection Error
- **Check**: `DATABASE_URL` is set correctly
- **Fix**: Use Internal Database URL from database settings

### Static Files Not Loading
- **Check**: `collectstatic` ran successfully
- **Fix**: Verify `build.sh` includes `collectstatic` command

### Application Crashes
- **Check**: Logs in Render dashboard
- **Fix**: Verify all environment variables are set

---

## Next Steps

1. ✅ Set up monitoring
2. ✅ Configure custom domain (optional)
3. ✅ Set up backups
4. ✅ Test all features
5. ✅ Monitor logs

---

## Need Help?

- 📚 **Full Guide**: See `RENDER_DEPLOYMENT_GUIDE.md`
- 📋 **Checklist**: See `DEPLOYMENT_CHECKLIST.md`
- 🌐 **Render Docs**: https://render.com/docs
- 💬 **Render Community**: https://community.render.com

---

**That's it! Your app should be live on Render! 🚀**

