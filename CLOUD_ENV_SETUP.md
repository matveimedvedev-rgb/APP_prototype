# Setting Environment Variables in Google Cloud Run

This guide explains how to add your `.env` file variables to your Cloud Run service.

## Quick Setup

### Option 1: Using the PowerShell Script (Recommended)

1. **Create a `.env` file** in the `website_feature_finder` directory with your variables:

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=0
ALLOWED_HOSTS=*
CSRF_TRUSTED_ORIGINS=https://app-prototype-56836240603.europe-west1.run.app
OPENAI_API_KEY=your-openai-api-key-here
```

2. **Run the script**:

```powershell
cd website_feature_finder
.\set-cloud-env.ps1
```

The script will automatically read your `.env` file and set all variables in Cloud Run.

### Option 2: Manual Setup via gcloud CLI

1. **Get your Cloud Run service URL** (if you don't know it):

```powershell
gcloud run services describe app-prototype --region europe-west1 --format "value(status.url)"
```

2. **Set environment variables**:

```powershell
gcloud run services update app-prototype `
  --region europe-west1 `
  --set-env-vars "SECRET_KEY=your-secret-key,DEBUG=0,ALLOWED_HOSTS=*,CSRF_TRUSTED_ORIGINS=https://app-prototype-56836240603.europe-west1.run.app,OPENAI_API_KEY=your-openai-api-key"
```

### Option 3: Using Google Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service: `app-prototype`
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Click "Add Variable" for each environment variable:
   - **SECRET_KEY**: Your Django secret key
   - **DEBUG**: `0` (for production)
   - **ALLOWED_HOSTS**: `*` (or specific domains)
   - **CSRF_TRUSTED_ORIGINS**: `https://app-prototype-56836240603.europe-west1.run.app`
   - **OPENAI_API_KEY**: Your OpenAI API key
6. Click "Deploy"

## Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key for cryptographic signing | Generated key (see below) |
| `DEBUG` | Debug mode (0 for production, 1 for development) | `0` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `*` or `example.com,www.example.com` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins for CSRF | `https://app-prototype-56836240603.europe-west1.run.app` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |

## Generating a Secure SECRET_KEY

If you need to generate a new Django secret key:

```powershell
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Or use Python directly:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Verifying Environment Variables

After setting the variables, verify they're set correctly:

```powershell
gcloud run services describe app-prototype --region europe-west1 --format "value(spec.template.spec.containers[0].env)"
```

## Important Notes

- **Never commit your `.env` file to Git** - it contains sensitive information
- The `.env` file is for local development only
- For Cloud Run, always use environment variables (not a `.env` file)
- After updating environment variables, Cloud Run will automatically restart your service
- Changes take effect immediately after deployment

## Troubleshooting

### Service not updating
- Wait a few seconds for the deployment to complete
- Check the Cloud Run console for deployment status

### Variables not working
- Ensure variable names match exactly (case-sensitive)
- Check for typos in variable values
- Verify the service name and region are correct

### CSRF errors
- Make sure `CSRF_TRUSTED_ORIGINS` includes your full Cloud Run URL (with `https://`)
- The URL must match exactly (no trailing slash)

