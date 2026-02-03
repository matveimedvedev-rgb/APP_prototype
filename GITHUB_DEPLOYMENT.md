# GitHub-Based Deployment Guide

This guide will help you set up continuous deployment from GitHub to Google Cloud Run.

## Prerequisites

1. Your code is pushed to a GitHub repository
2. You have access to Google Cloud Console
3. Cloud Build API is enabled

## Step 1: Connect GitHub Repository to Google Cloud

### Option A: Using Google Cloud Console (Recommended)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Cloud Build** > **Triggers**
3. Click **Create Trigger**
4. Select **GitHub (Cloud Build GitHub App)** or **GitHub** as your source
5. Authenticate with GitHub if prompted
6. Select your repository: `your-username/your-repo-name`
7. Choose the branch (usually `main` or `master`)

### Option B: Using gcloud CLI

```powershell
# Install Cloud Build GitHub app (if not already installed)
gcloud alpha builds triggers create github `
  --name="webglazer-prototype-deploy" `
  --repo-name="YOUR_REPO_NAME" `
  --repo-owner="YOUR_GITHUB_USERNAME" `
  --branch-pattern="^main$" `
  --build-config="website_feature_finder/cloudbuild.yaml" `
  --region="us-central1"
```

## Step 2: Create the Trigger

### Using Cloud Console:

1. **Name**: `webglazer-prototype-deploy`
2. **Event**: Push to a branch
3. **Branch**: `^main$` (or your main branch)
4. **Configuration**: Cloud Build configuration file
5. **Location**: `website_feature_finder/cloudbuild.yaml`
6. **Substitution variables** (optional):
   - `_SERVICE_NAME`: `webglazer-prototype`
   - `_REGION`: `us-central1`

### Using gcloud CLI:

```powershell
gcloud builds triggers create github `
  --name="webglazer-prototype-deploy" `
  --repo-name="YOUR_REPO_NAME" `
  --repo-owner="YOUR_GITHUB_USERNAME" `
  --branch-pattern="^main$" `
  --build-config="website_feature_finder/cloudbuild.yaml" `
  --region="us-central1" `
  --project="clever-abbey-486313-u8"
```

## Step 3: Grant Necessary Permissions

The Cloud Build service account needs permissions to deploy to Cloud Run:

```powershell
# Get your project number
$projectNumber = gcloud projects describe clever-abbey-486313-u8 --format="value(projectNumber)"

# Grant Cloud Run Admin to Cloud Build service account
gcloud projects add-iam-policy-binding clever-abbey-486313-u8 `
  --member="serviceAccount:$projectNumber@cloudbuild.gserviceaccount.com" `
  --role="roles/run.admin"

# Grant Service Account User role
gcloud projects add-iam-policy-binding clever-abbey-486313-u8 `
  --member="serviceAccount:$projectNumber@cloudbuild.gserviceaccount.com" `
  --role="roles/iam.serviceAccountUser"

# Grant Artifact Registry Writer
gcloud projects add-iam-policy-binding clever-abbey-486313-u8 `
  --member="serviceAccount:$projectNumber@cloudbuild.gserviceaccount.com" `
  --role="roles/artifactregistry.writer"
```

## Step 4: Set Environment Variables

After the first deployment, set your environment variables:

```powershell
gcloud run services update webglazer-prototype `
  --region us-central1 `
  --set-env-vars "OPENAI_API_KEY=your_key_here,SECRET_KEY=your_secret_here"
```

Or use Secret Manager (recommended for production):

```powershell
# Create secrets
echo -n "your_openai_key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your_secret_key" | gcloud secrets create django-secret-key --data-file=-

# Grant access
$projectNumber = gcloud projects describe clever-abbey-486313-u8 --format="value(projectNumber)"
gcloud secrets add-iam-policy-binding openai-api-key `
  --member="serviceAccount:$projectNumber-compute@developer.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding django-secret-key `
  --member="serviceAccount:$projectNumber-compute@developer.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

Then update `cloudbuild.yaml` to use secrets (see Step 5).

## Step 5: Update cloudbuild.yaml for Secrets (Optional but Recommended)

If using Secret Manager, update the deploy step in `cloudbuild.yaml`:

```yaml
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'webglazer-prototype'
      - '--image'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/webglazer-prototype/webglazer-prototype:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--memory'
      - '512Mi'
      - '--cpu'
      - '1'
      - '--timeout'
      - '300'
      - '--max-instances'
      - '10'
      - '--set-env-vars'
      - 'DEBUG=0'
      - '--set-secrets'
      - 'OPENAI_API_KEY=openai-api-key:latest,SECRET_KEY=django-secret-key:latest'
```

## Step 6: Test the Deployment

1. Make a small change to your code (e.g., update a comment)
2. Commit and push to your main branch:
   ```powershell
   git add .
   git commit -m "Test deployment"
   git push origin main
   ```
3. Go to Cloud Build in Google Cloud Console
4. You should see a new build triggered automatically
5. Wait for it to complete (5-10 minutes)
6. Your app will be deployed automatically!

## Step 7: Verify Deployment

Get your service URL:

```powershell
gcloud run services describe webglazer-prototype --region us-central1 --format "value(status.url)"
```

Visit the URL in your browser to verify it's working.

## Troubleshooting

### Build Fails
- Check Cloud Build logs in the console
- Verify `cloudbuild.yaml` is in the correct location
- Ensure Dockerfile exists in `website_feature_finder/` directory

### Permission Errors
- Run the permission commands in Step 3
- Wait 2-3 minutes for permissions to propagate

### Deployment Fails
- Check that the image was built successfully
- Verify Cloud Run API is enabled
- Check Cloud Run logs: `gcloud run services logs read webglazer-prototype --region us-central1`

### Environment Variables Not Set
- Set them manually using Step 4
- Or update `cloudbuild.yaml` to include them in the deploy step

## Manual Trigger (Optional)

You can also manually trigger a build:

```powershell
gcloud builds triggers run webglazer-prototype-deploy --branch=main
```

## File Structure

Your repository should have this structure:
```
your-repo/
├── website_feature_finder/
│   ├── cloudbuild.yaml          # Cloud Build configuration
│   ├── Dockerfile               # Docker build instructions
│   ├── requirements.txt        # Python dependencies
│   ├── manage.py
│   ├── config/
│   ├── analyzer/
│   └── ...
└── README.md
```

## Next Steps

1. Push your code to GitHub
2. Connect the repository (Step 1)
3. Create the trigger (Step 2)
4. Grant permissions (Step 3)
5. Set environment variables (Step 4)
6. Push a change to trigger deployment!

