# Google Cloud Run Deployment Script for PowerShell
# Usage: .\deploy.ps1 [PROJECT_ID] [SERVICE_NAME] [REGION]

param(
    [string]$ProjectId = "YOUR_PROJECT_ID",
    [string]$ServiceName = "website-feature-finder",
    [string]$Region = "us-central1"
)

Write-Host "🚀 Deploying to Google Cloud Run..." -ForegroundColor Cyan
Write-Host "Project ID: $ProjectId"
Write-Host "Service Name: $ServiceName"
Write-Host "Region: $Region"
Write-Host ""

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: gcloud CLI is not installed." -ForegroundColor Red
    Write-Host "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Set the project
Write-Host "📋 Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Build the container image
Write-Host "🔨 Building container image..." -ForegroundColor Yellow
gcloud builds submit --tag "gcr.io/$ProjectId/$ServiceName"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
  --image "gcr.io/$ProjectId/$ServiceName" `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars "DEBUG=0" `
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest,SECRET_KEY=django-secret-key:latest" `
  2>$null

# If secrets don't exist, deploy with env vars (user will need to set these)
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Secrets not found, deploying with environment variables..." -ForegroundColor Yellow
    Write-Host "⚠️  Make sure to set OPENAI_API_KEY and SECRET_KEY manually after deployment" -ForegroundColor Yellow
    gcloud run deploy $ServiceName `
      --image "gcr.io/$ProjectId/$ServiceName" `
      --platform managed `
      --region $Region `
      --allow-unauthenticated `
      --memory 512Mi `
      --cpu 1 `
      --timeout 300 `
      --max-instances 10 `
      --set-env-vars "DEBUG=0"
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host "📝 Getting service URL..." -ForegroundColor Yellow
    $url = gcloud run services describe $ServiceName --region $Region --format 'value(status.url)'
    Write-Host "🌐 Your app is available at: $url" -ForegroundColor Green
} else {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

