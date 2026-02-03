# Deployment script for WebglazerPrototype
# Project ID: clever-abbey-486313-u8
# Email: matvei.medvedev@startschool.org

$ProjectId = "clever-abbey-486313-u8"
$ServiceName = "webglazer-prototype"
$Region = "us-central1"

Write-Host "Deploying WebglazerPrototype to Google Cloud Run..." -ForegroundColor Cyan
Write-Host "Project ID: $ProjectId" -ForegroundColor White
Write-Host "Service Name: $ServiceName" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host ""

# Refresh PATH
$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Check authentication
Write-Host "Checking authentication..." -ForegroundColor Yellow
$authCheck = gcloud auth list 2>&1 | Out-String
if ($authCheck -match "No credentialed") {
    Write-Host "Not authenticated. Attempting to login..." -ForegroundColor Yellow
    gcloud auth login matvei.medvedev@startschool.org
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Authentication failed!" -ForegroundColor Red
        exit 1
    }
}
$authAccount = (gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1 | Select-Object -First 1)
if ($authAccount) {
    Write-Host "Authenticated as: $authAccount" -ForegroundColor Green
} else {
    Write-Host "Warning: Could not verify authentication" -ForegroundColor Yellow
}

# Set project
Write-Host "Setting project to $ProjectId..." -ForegroundColor Yellow
gcloud config set project $ProjectId
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to set project. Make sure the project exists." -ForegroundColor Red
    exit 1
}

# Enable APIs
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet
gcloud services enable secretmanager.googleapis.com --quiet

# Grant Cloud Build service account necessary permissions
Write-Host "Granting Cloud Build permissions..." -ForegroundColor Yellow
$projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)" 2>&1
if ($projectNumber -and -not ($projectNumber -match "ERROR")) {
    $serviceAccount = "$projectNumber@cloudbuild.gserviceaccount.com"
    Write-Host "   Granting Storage Admin to: $serviceAccount" -ForegroundColor Gray
    gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$serviceAccount" `
        --role="roles/storage.admin" `
        --quiet 2>&1 | Out-Null
    
    Write-Host "   Granting Service Account User to: $serviceAccount" -ForegroundColor Gray
    gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$serviceAccount" `
        --role="roles/iam.serviceAccountUser" `
        --quiet 2>&1 | Out-Null
}

# Build the container
Write-Host "Building container image..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Gray
$imageTag = "$Region-docker.pkg.dev/$ProjectId/$ServiceName/$ServiceName"
gcloud builds submit --tag $imageTag --timeout=20m

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "Note: You will need to set OPENAI_API_KEY and SECRET_KEY after deployment" -ForegroundColor Yellow
Write-Host ""

$imageTag = "$Region-docker.pkg.dev/$ProjectId/$ServiceName/$ServiceName"
gcloud run deploy $ServiceName `
  --image $imageTag `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars "DEBUG=0" `
  2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS: Deployment successful!" -ForegroundColor Green
    Write-Host "Getting service URL..." -ForegroundColor Yellow
    $url = gcloud run services describe $ServiceName --region $Region --format "value(status.url)" 2>&1
    Write-Host ""
    Write-Host "Your app is available at: $url" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Set environment variables:" -ForegroundColor White
    Write-Host "   gcloud run services update $ServiceName --region $Region --set-env-vars `"OPENAI_API_KEY=your_key,SECRET_KEY=your_secret`"" -ForegroundColor Gray
    Write-Host "2. Or use Secret Manager for better security (see DEPLOYMENT.md)" -ForegroundColor White
} else {
    Write-Host "ERROR: Deployment failed!" -ForegroundColor Red
    exit 1
}

