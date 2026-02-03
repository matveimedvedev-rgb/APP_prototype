# Manual Deployment Guide for WebglazerPrototype

Follow these steps to deploy your application to Google Cloud Run manually.

## Prerequisites
- You're authenticated: `gcloud auth list` should show `matvei.medvedev@startschool.org`
- Project is set: `gcloud config set project clever-abbey-486313-u8`

## Step 1: Navigate to Project Directory

```powershell
cd website_feature_finder
```

## Step 2: Build and Push Docker Image

Build the container image and push it to Artifact Registry:

```powershell
gcloud builds submit --tag us-central1-docker.pkg.dev/clever-abbey-486313-u8/webglazer-prototype/webglazer-prototype --timeout=20m
```

**Expected output:** 
- Build will take 5-10 minutes
- You should see "Successfully built" and "Successfully tagged"
- Image should push successfully

**If you get permission errors:**
- Wait 2-3 minutes for permissions to propagate
- Or run: `gcloud projects add-iam-policy-binding clever-abbey-486313-u8 --member="serviceAccount:187765262916-compute@developer.gserviceaccount.com" --role="roles/artifactregistry.writer"`

## Step 3: Deploy to Cloud Run

Once the image is built and pushed, deploy it:

```powershell
gcloud run deploy webglazer-prototype `
  --image us-central1-docker.pkg.dev/clever-abbey-486313-u8/webglazer-prototype/webglazer-prototype `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars "DEBUG=0"
```

**Expected output:**
- Service will be deployed
- You'll get a URL like: `https://webglazer-prototype-xxxxx-uc.a.run.app`

## Step 4: Get Your Service URL

After deployment, get your service URL:

```powershell
gcloud run services describe webglazer-prototype --region us-central1 --format "value(status.url)"
```

## Step 5: Set Environment Variables (Required)

Your app needs `OPENAI_API_KEY` and `SECRET_KEY`. Set them:

```powershell
gcloud run services update webglazer-prototype `
  --region us-central1 `
  --set-env-vars "OPENAI_API_KEY=your_actual_openai_key_here,SECRET_KEY=your_actual_secret_key_here"
```

**Important:** Replace `your_actual_openai_key_here` and `your_actual_secret_key_here` with your real values.

## Step 6: Verify Deployment

1. Visit the URL from Step 4 in your browser
2. Check logs if there are issues:
   ```powershell
   gcloud run services logs read webglazer-prototype --region us-central1
   ```

## Troubleshooting

### Build Fails
- Check that you're in the `website_feature_finder` directory
- Verify Dockerfile exists: `ls Dockerfile`
- Check requirements.txt exists: `ls requirements.txt`

### Push Fails with Permission Error
- Wait 2-3 minutes and try again (permissions need time to propagate)
- Verify you're authenticated: `gcloud auth list`
- Verify project is set: `gcloud config get-value project`

### Deployment Fails
- Check the image exists: `gcloud artifacts docker images list us-central1-docker.pkg.dev/clever-abbey-486313-u8/webglazer-prototype`
- Verify Cloud Run API is enabled: `gcloud services enable run.googleapis.com`

### App Doesn't Start
- Check logs: `gcloud run services logs read webglazer-prototype --region us-central1`
- Verify environment variables are set: `gcloud run services describe webglazer-prototype --region us-central1 --format="value(spec.template.spec.containers[0].env)"`

## Alternative: Using Secret Manager (More Secure)

Instead of setting environment variables directly, use Secret Manager:

1. Create secrets:
   ```powershell
   echo -n "your_openai_api_key" | gcloud secrets create openai-api-key --data-file=-
   echo -n "your_django_secret_key" | gcloud secrets create django-secret-key --data-file=-
   ```

2. Grant Cloud Run access:
   ```powershell
   $projectNumber = gcloud projects describe clever-abbey-486313-u8 --format="value(projectNumber)"
   gcloud secrets add-iam-policy-binding openai-api-key --member="serviceAccount:$projectNumber-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
   gcloud secrets add-iam-policy-binding django-secret-key --member="serviceAccount:$projectNumber-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
   ```

3. Deploy with secrets:
   ```powershell
   gcloud run deploy webglazer-prototype `
     --image us-central1-docker.pkg.dev/clever-abbey-486313-u8/webglazer-prototype/webglazer-prototype `
     --platform managed `
     --region us-central1 `
     --allow-unauthenticated `
     --memory 512Mi `
     --cpu 1 `
     --timeout 300 `
     --max-instances 10 `
     --set-env-vars "DEBUG=0" `
     --set-secrets "OPENAI_API_KEY=openai-api-key:latest,SECRET_KEY=django-secret-key:latest"
   ```

## Quick Reference Commands

```powershell
# Check authentication
gcloud auth list

# Set project
gcloud config set project clever-abbey-486313-u8

# Build and push
gcloud builds submit --tag us-central1-docker.pkg.dev/clever-abbey-486313-u8/webglazer-prototype/webglazer-prototype

# Deploy
gcloud run deploy webglazer-prototype --image us-central1-docker.pkg.dev/clever-abbey-486313-u8/webglazer-prototype/webglazer-prototype --platform managed --region us-central1 --allow-unauthenticated

# Get URL
gcloud run services describe webglazer-prototype --region us-central1 --format "value(status.url)"

# View logs
gcloud run services logs read webglazer-prototype --region us-central1
```

