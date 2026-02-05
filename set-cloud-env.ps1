# PowerShell script to set environment variables in Google Cloud Run
# This script sets the environment variables from .env file to Cloud Run service

param(
    [string]$ServiceName = "app-prototype",
    [string]$Region = "europe-west1",
    [string]$EnvFile = ".env"
)

Write-Host "Setting environment variables for Cloud Run service: $ServiceName" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Green
Write-Host ""

# Check if .env file exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "Error: $EnvFile file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with the following variables:" -ForegroundColor Yellow
    Write-Host "  SECRET_KEY=your-secret-key"
    Write-Host "  DEBUG=0"
    Write-Host "  ALLOWED_HOSTS=*"
    Write-Host "  CSRF_TRUSTED_ORIGINS=https://app-prototype-56836240603.europe-west1.run.app"
    Write-Host "  OPENAI_API_KEY=your-openai-api-key"
    exit 1
}

# Read .env file and parse variables
$envVars = @{}
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    # Skip empty lines and comments
    if ($line -and -not $line.StartsWith("#")) {
        $parts = $line -split "=", 2
        if ($parts.Length -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()
            # Remove quotes if present
            if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            if ($value.StartsWith("'") -and $value.EndsWith("'")) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            $envVars[$key] = $value
        }
    }
}

if ($envVars.Count -eq 0) {
    Write-Host "Error: No environment variables found in $EnvFile" -ForegroundColor Red
    exit 1
}

Write-Host "Found $($envVars.Count) environment variables:" -ForegroundColor Cyan
foreach ($key in $envVars.Keys) {
    $displayValue = if ($key -eq "OPENAI_API_KEY" -or $key -eq "SECRET_KEY") { "***hidden***" } else { $envVars[$key] }
    Write-Host "  $key = $displayValue" -ForegroundColor Gray
}
Write-Host ""

# Build the --set-env-vars argument
$envVarsString = ($envVars.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ","

Write-Host "Updating Cloud Run service..." -ForegroundColor Yellow

# Update Cloud Run service with environment variables
$command = "gcloud run services update $ServiceName --region $Region --set-env-vars `"$envVarsString`""
Write-Host "Running: $command" -ForegroundColor Gray
Write-Host ""

Invoke-Expression $command

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Success! Environment variables have been set." -ForegroundColor Green
    Write-Host "The service will restart with the new environment variables." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Error: Failed to update Cloud Run service" -ForegroundColor Red
    exit 1
}

