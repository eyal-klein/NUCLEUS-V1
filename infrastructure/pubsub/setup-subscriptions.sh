#!/bin/bash
# NUCLEUS Pub/Sub Push Subscriptions Setup
# Run this after deploying the event consumer service

set -e

PROJECT_ID="${GCP_PROJECT_ID:-thrive-system1}"
REGION="${GCP_REGION:-us-central1}"

# Get the consumer service URL
CONSUMER_URL=$(gcloud run services describe ingestion-event-consumer \
    --project=$PROJECT_ID \
    --region=$REGION \
    --format='value(status.url)' 2>/dev/null)

if [ -z "$CONSUMER_URL" ]; then
    echo "❌ Error: ingestion-event-consumer service not found!"
    echo "   Deploy the service first, then run this script."
    exit 1
fi

echo "🚀 Setting up Push Subscriptions..."
echo "Consumer URL: $CONSUMER_URL"

# Get service account for authentication
SA_EMAIL="${PROJECT_ID}@appspot.gserviceaccount.com"

# ============================================
# Create Push Subscriptions
# ============================================

echo ""
echo "📬 Creating Push Subscription for Digital Events..."
gcloud pubsub subscriptions create nucleus-digital-events-push \
    --topic=nucleus-digital-events \
    --project=$PROJECT_ID \
    --push-endpoint="${CONSUMER_URL}/pubsub/digital" \
    --push-auth-service-account=$SA_EMAIL \
    --ack-deadline=60 \
    --message-retention-duration=7d \
    --min-retry-delay=10s \
    --max-retry-delay=600s \
    --dead-letter-topic=projects/$PROJECT_ID/topics/nucleus-digital-events-dlq \
    --max-delivery-attempts=5 \
    --labels=project=nucleus,type=push \
    2>/dev/null || echo "Subscription already exists, updating..."

echo ""
echo "📬 Creating Push Subscription for Health Events..."
gcloud pubsub subscriptions create nucleus-health-events-push \
    --topic=nucleus-health-events \
    --project=$PROJECT_ID \
    --push-endpoint="${CONSUMER_URL}/pubsub/health" \
    --push-auth-service-account=$SA_EMAIL \
    --ack-deadline=60 \
    --message-retention-duration=7d \
    --min-retry-delay=10s \
    --max-retry-delay=600s \
    --dead-letter-topic=projects/$PROJECT_ID/topics/nucleus-health-events-dlq \
    --max-delivery-attempts=5 \
    --labels=project=nucleus,type=push \
    2>/dev/null || echo "Subscription already exists, updating..."

echo ""
echo "📬 Creating Push Subscription for Social Events..."
gcloud pubsub subscriptions create nucleus-social-events-push \
    --topic=nucleus-social-events \
    --project=$PROJECT_ID \
    --push-endpoint="${CONSUMER_URL}/pubsub/social" \
    --push-auth-service-account=$SA_EMAIL \
    --ack-deadline=60 \
    --message-retention-duration=7d \
    --min-retry-delay=10s \
    --max-retry-delay=600s \
    --dead-letter-topic=projects/$PROJECT_ID/topics/nucleus-social-events-dlq \
    --max-delivery-attempts=5 \
    --labels=project=nucleus,type=push \
    2>/dev/null || echo "Subscription already exists, updating..."

echo ""
echo "============================================"
echo "🎉 Push Subscriptions Created!"
echo "============================================"
echo ""
echo "Subscriptions:"
echo "  - nucleus-digital-events-push → ${CONSUMER_URL}/pubsub/digital"
echo "  - nucleus-health-events-push → ${CONSUMER_URL}/pubsub/health"
echo "  - nucleus-social-events-push → ${CONSUMER_URL}/pubsub/social"
echo ""
echo "Features enabled:"
echo "  - Push authentication (service account)"
echo "  - Dead letter queue (5 retries)"
echo "  - Exponential backoff (10s - 600s)"
echo "  - 7 day message retention"
echo ""
