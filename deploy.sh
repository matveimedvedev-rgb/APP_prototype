#!/bin/bash

# Google Cloud Run Deployment Script
# Usage: ./deploy.sh [PROJECT_ID] [SERVICE_NAME] [REGION]

# Set default values
PROJECT_ID=${1:-"YOUR_PROJECT_ID"}
SERVICE_NAME=${2:-"website-feature-finder"}
REGION=${3:-"us-central1"}

echo "🚀 Deploying to Google Cloud Run..."
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed."
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Build the container image
echo "🔨 Building container image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "DEBUG=0" \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest,SECRET_KEY=django-secret-key:latest" || \
  gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "DEBUG=0,OPENAI_API_KEY=your_key_here,SECRET_KEY=your_secret_key_here"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo "📝 Getting service URL..."
    gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
else
    echo "❌ Deployment failed!"
    exit 1
fi

