# Google Cloud Run Deployment Guide

This guide will help you deploy the Website Feature Finder application to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**: Sign up at https://cloud.google.com/
2. **Google Cloud SDK**: Install from https://cloud.google.com/sdk/docs/install
3. **Docker** (optional, for local testing): https://www.docker.com/

## Step 1: Set Up Google Cloud Project

1. Create a new project in Google Cloud Console:
   ```bash
   gcloud projects create YOUR_PROJECT_ID --name="Website Feature Finder"
   ```

2. Enable required APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   ```

3. Set your project:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

4. Authenticate:
   ```bash
   gcloud auth login
   ```

## Step 2: Set Up Secrets (Recommended)

Store sensitive information in Google Secret Manager:

```bash
# Create secrets
echo -n "your_openai_api_key_here" | gcloud secrets create openai-api-key --data-file=-
echo -n "your_django_secret_key_here" | gcloud secrets create django-secret-key --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding django-secret-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

To get your project number:
```bash
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
```

## Step 3: Deploy

### Option A: Using the Deployment Script (Recommended)

**Windows (PowerShell):**
```powershell
cd website_feature_finder
.\deploy.ps1 YOUR_PROJECT_ID website-feature-finder us-central1
```

**Linux/Mac:**
```bash
cd website_feature_finder
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID website-feature-finder us-central1
```

### Option B: Manual Deployment

1. Build the container:
   ```bash
   cd website_feature_finder
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/website-feature-finder
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy website-feature-finder \
     --image gcr.io/YOUR_PROJECT_ID/website-feature-finder \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 512Mi \
     --cpu 1 \
     --timeout 300 \
     --set-env-vars "DEBUG=0" \
     --set-secrets "OPENAI_API_KEY=openai-api-key:latest,SECRET_KEY=django-secret-key:latest"
   ```

   If you haven't set up secrets, use environment variables instead:
   ```bash
   gcloud run deploy website-feature-finder \
     --image gcr.io/YOUR_PROJECT_ID/website-feature-finder \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 512Mi \
     --cpu 1 \
     --timeout 300 \
     --set-env-vars "DEBUG=0,OPENAI_API_KEY=your_key,SECRET_KEY=your_secret"
   ```

## Step 4: Access Your Application

After deployment, Cloud Run will provide a URL like:
```
https://website-feature-finder-xxxxx-uc.a.run.app
```

You can get the URL with:
```bash
gcloud run services describe website-feature-finder --region us-central1 --format 'value(status.url)'
```

## Step 5: Update Environment Variables (if needed)

To update environment variables after deployment:

```bash
gcloud run services update website-feature-finder \
  --region us-central1 \
  --set-env-vars "DEBUG=0,ALLOWED_HOSTS=your-domain.com"
```

## Important Notes

### Database
- The app currently uses SQLite, which is **ephemeral** on Cloud Run
- Data will be lost when the container restarts
- For production, consider using **Cloud SQL (PostgreSQL)**:
  ```bash
  # Create Cloud SQL instance
  gcloud sql instances create website-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1
  ```

### Static Files
- Static files are collected during build
- For production, consider using Cloud Storage or a CDN

### Scaling
- Cloud Run automatically scales based on traffic
- Default: 0-10 instances (configurable)
- Billing is per request and compute time

### Monitoring
- View logs: `gcloud run services logs read website-feature-finder --region us-central1`
- Monitor in Cloud Console: https://console.cloud.google.com/run

## Troubleshooting

### Build Fails
- Check that all dependencies are in `requirements.txt`
- Verify Dockerfile syntax
- Check Cloud Build logs in the console

### Deployment Fails
- Ensure APIs are enabled
- Check IAM permissions
- Verify secrets exist and are accessible

### App Doesn't Start
- Check logs: `gcloud run services logs read website-feature-finder --region us-central1`
- Verify environment variables are set correctly
- Check that PORT environment variable is used (handled automatically by Cloud Run)

### Database Issues
- SQLite files are ephemeral - data resets on container restart
- Consider migrating to Cloud SQL for persistent storage

## Cost Estimation

Google Cloud Run pricing (as of 2024):
- **Free tier**: 2 million requests/month, 360,000 GB-seconds of memory
- **After free tier**: ~$0.40 per million requests, ~$0.0000025 per GB-second

For a small application, you'll likely stay within the free tier.

## Next Steps

1. Set up a custom domain (optional)
2. Configure Cloud SQL for persistent database
3. Set up Cloud Storage for static files
4. Configure monitoring and alerts
5. Set up CI/CD pipeline

