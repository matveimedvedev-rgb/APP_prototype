# Quick Deployment Guide

## Prerequisites ✅
- Google Cloud SDK is installed
- All deployment files are ready

## Step 1: Authenticate (Run in PowerShell)

```powershell
# Refresh PATH
$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Login (will open browser)
gcloud auth login matvei.medvedev@startschool.org
```

## Step 2: Create or Select Project

```powershell
# List existing projects
gcloud projects list

# OR create a new project (replace with your desired project ID)
gcloud projects create website-feature-finder --name="Website Feature Finder"

# Set the project
gcloud config set project YOUR_PROJECT_ID
```

## Step 3: Enable Required APIs

```powershell
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## Step 4: Set Up Secrets (Optional but Recommended)

```powershell
# Create secrets (replace with your actual values)
echo -n "your_openai_api_key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your_django_secret_key" | gcloud secrets create django-secret-key --data-file=-

# Get project number for IAM binding
$projectNumber = gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)"

# Grant access
gcloud secrets add-iam-policy-binding openai-api-key --member="serviceAccount:$projectNumber-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding django-secret-key --member="serviceAccount:$projectNumber-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

## Step 5: Deploy

```powershell
cd website_feature_finder
.\deploy.ps1 YOUR_PROJECT_ID website-feature-finder us-central1
```

## Alternative: Manual Deployment

If the script doesn't work, deploy manually:

```powershell
cd website_feature_finder

# Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/website-feature-finder

# Deploy (with secrets)
gcloud run deploy website-feature-finder `
  --image gcr.io/YOUR_PROJECT_ID/website-feature-finder `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --set-env-vars "DEBUG=0" `
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest,SECRET_KEY=django-secret-key:latest"

# OR deploy without secrets (set env vars manually later)
gcloud run deploy website-feature-finder `
  --image gcr.io/YOUR_PROJECT_ID/website-feature-finder `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --set-env-vars "DEBUG=0,OPENAI_API_KEY=your_key,SECRET_KEY=your_secret"
```

## Get Your App URL

```powershell
gcloud run services describe website-feature-finder --region us-central1 --format 'value(status.url)'
```

