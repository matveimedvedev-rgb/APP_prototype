# Quick setup script for GitHub-based deployment
# Run this after connecting your GitHub repo to Google Cloud

$ProjectId = "clever-abbey-486313-u8"
$Region = "us-central1"

Write-Host "Setting up GitHub deployment for WebglazerPrototype..." -ForegroundColor Cyan
Write-Host ""

# Refresh PATH
$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Set project
Write-Host "Setting project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Get project number
$projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)"
Write-Host "Project Number: $projectNumber" -ForegroundColor Gray

# Grant necessary permissions to Cloud Build service account
Write-Host "Granting permissions to Cloud Build service account..." -ForegroundColor Yellow

Write-Host "  - Cloud Run Admin" -ForegroundColor Gray
gcloud projects add-iam-policy-binding $ProjectId `
  --member="serviceAccount:$projectNumber@cloudbuild.gserviceaccount.com" `
  --role="roles/run.admin" `
  --quiet

Write-Host "  - Service Account User" -ForegroundColor Gray
gcloud projects add-iam-policy-binding $ProjectId `
  --member="serviceAccount:$projectNumber@cloudbuild.gserviceaccount.com" `
  --role="roles/iam.serviceAccountUser" `
  --quiet

Write-Host "  - Artifact Registry Writer" -ForegroundColor Gray
gcloud projects add-iam-policy-binding $ProjectId `
  --member="serviceAccount:$projectNumber@cloudbuild.gserviceaccount.com" `
  --role="roles/artifactregistry.writer" `
  --quiet

Write-Host ""
Write-Host "SUCCESS: Permissions granted!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Go to Google Cloud Console > Cloud Build > Triggers" -ForegroundColor White
Write-Host "2. Click 'Create Trigger'" -ForegroundColor White
Write-Host "3. Connect your GitHub repository" -ForegroundColor White
Write-Host "4. Set configuration:" -ForegroundColor White
Write-Host "   - Name: webglazer-prototype-deploy" -ForegroundColor Gray
Write-Host "   - Event: Push to a branch" -ForegroundColor Gray
Write-Host "   - Branch: ^main$" -ForegroundColor Gray
Write-Host "   - Configuration: Cloud Build configuration file" -ForegroundColor Gray
Write-Host "   - Location: website_feature_finder/cloudbuild.yaml" -ForegroundColor Gray
Write-Host "5. After first deployment, set environment variables:" -ForegroundColor White
Write-Host "   gcloud run services update webglazer-prototype --region $Region --set-env-vars `"OPENAI_API_KEY=your_key,SECRET_KEY=your_secret`"" -ForegroundColor Gray
Write-Host ""
Write-Host "See GITHUB_DEPLOYMENT.md for detailed instructions." -ForegroundColor Cyan

