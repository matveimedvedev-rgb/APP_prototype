# CSRF Fix for Cloud Run

## Problem
Getting "CSRF verification failed" error when submitting forms on Cloud Run.

## Solution

After your app is deployed, you need to set the `CSRF_TRUSTED_ORIGINS` environment variable in Cloud Run.

### Step 1: Get Your Cloud Run URL

```powershell
gcloud run services describe webglazer-prototype --region us-central1 --format "value(status.url)"
```

This will output something like: `https://webglazer-prototype-xxxxx-uc.a.run.app`

### Step 2: Set CSRF_TRUSTED_ORIGINS

Update your Cloud Run service with the CSRF trusted origin:

```powershell
gcloud run services update webglazer-prototype `
  --region us-central1 `
  --set-env-vars "CSRF_TRUSTED_ORIGINS=https://webglazer-prototype-xxxxx-uc.a.run.app"
```

Replace `https://webglazer-prototype-xxxxx-uc.a.run.app` with your actual URL from Step 1.

### Step 3: Verify

1. Wait a few seconds for the service to update
2. Refresh your Cloud Run app
3. Try the "Website Analysis" form again

## Alternative: Set via Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service: `webglazer-prototype`
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Add environment variable:
   - **Name**: `CSRF_TRUSTED_ORIGINS`
   - **Value**: `https://your-service-url-uc.a.run.app`
6. Click "Deploy"

## Note

The custom middleware (`config/csrf_middleware.py`) should automatically handle Cloud Run domains, but explicitly setting `CSRF_TRUSTED_ORIGINS` is the recommended approach for production.

