# Quick Deploy Instructions for webglazer Project

## Step 1: Authenticate (One-time setup)

Open PowerShell and run:
```powershell
gcloud auth login matvei.medvedev@startschool.org
```
Complete the browser authentication when prompted.

## Step 2: Run the Deployment Script

After authentication completes, run:
```powershell
cd C:\Users\matth\Documents\startscool\app_prototype\website_feature_finder
.\deploy-webglazer.ps1
```

That's it! The script will:
- ✅ Set project to `webglazer`
- ✅ Enable required APIs
- ✅ Build your Docker container
- ✅ Deploy to Cloud Run
- ✅ Give you the live URL

## Step 3: Set Environment Variables (After deployment)

Once deployed, set your API keys:
```powershell
gcloud run services update website-feature-finder `
  --region us-central1 `
  --set-env-vars "OPENAI_API_KEY=your_actual_key,SECRET_KEY=your_actual_secret"
```

## Alternative: Manual Commands

If the script doesn't work, run these commands one by one:

```powershell
# Set project
gcloud config set project webglazer

# Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# Build
gcloud builds submit --tag gcr.io/webglazer/website-feature-finder

# Deploy
gcloud run deploy website-feature-finder `
  --image gcr.io/webglazer/website-feature-finder `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 512Mi `
  --set-env-vars "DEBUG=0"
```

