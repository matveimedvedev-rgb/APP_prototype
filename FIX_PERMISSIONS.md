# Fix Cloud Build Permissions

The Cloud Build service account needs permissions to build and deploy. Here's how to fix it:

## Option 1: Via Web Console (Easiest)

1. Go to: https://console.cloud.google.com/iam-admin/iam?project=webglazer
2. Find the service account: `56836240603@cloudbuild.gserviceaccount.com`
3. If it doesn't exist, click "Grant Access" and add:
   - Principal: `56836240603@cloudbuild.gserviceaccount.com`
   - Role: `Cloud Build Service Account` (this includes storage permissions)
   - Click "Save"

## Option 2: Ask Your Admin

If you don't have permission to modify IAM policies, ask your Google Workspace admin to grant:
- **Your account** needs: `Owner` or `Editor` role on the project
- **Cloud Build service account** (`56836240603@cloudbuild.gserviceaccount.com`) needs: `Cloud Build Service Account` role

## Option 3: Use Cloud Build with Different Permissions

Try building with explicit service account:

```powershell
gcloud builds submit --tag gcr.io/webglazer/website-feature-finder --service-account=56836240603@cloudbuild.gserviceaccount.com
```

## Quick Fix Command (if you have permissions)

Run this in PowerShell:
```powershell
gcloud projects add-iam-policy-binding webglazer `
  --member="serviceAccount:56836240603@cloudbuild.gserviceaccount.com" `
  --role="roles/cloudbuild.builds.builder"
```

