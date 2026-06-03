# PRISM-INSIGHT Real-time Trading Signal Subscription Guide

You can receive real-time AI-based trading signals from PRISM-INSIGHT via GCP Pub/Sub.

## 📋 Overview

- **Free of Charge**: No operational costs on the PRISM-INSIGHT side.
- **Real-time Stream**: Instantly receive BUY/SELL trading signals.
- **Customizable**: Implement your own custom trading bots or alerting tools using the signals.

## 💰 Cost Guide

### PRISM-INSIGHT Side
- Free (Topic operation and ingestion fees are covered by PRISM-INSIGHT).

### Subscriber Side (Your GCP Project)
- **GCP Pub/Sub Pricing**: Refer to [Google Cloud Pub/Sub Pricing](https://cloud.google.com/pubsub/pricing).
- **Free Tier**: The first 10 GB of data usage per month is free.
- **Expected Cost**: Almost zero or free-tier covered, as the overall volume of trading signals is very small.

## 🚀 Quick Start

### 1. Create a GCP Account & Project

1. If you don't have a Google Cloud account: Create one at [Google Cloud Console](https://console.cloud.google.com) (free tiers are available).
2. Create a new GCP project:
   - Project Name: Any name (e.g., `my-prism-subscriber`).
   - Project ID: Note the ID (e.g., `my-prism-subscriber-12345`).

### 2. Enable the Pub/Sub API

```bash
# If you have gcloud CLI installed
gcloud services enable pubsub.googleapis.com --project=MY_PROJECT_ID

# Or via Web Console:
# GCP Console → APIs & Services → Library → Search "Cloud Pub/Sub API" → Click Enable.
```

### 3. Create a Subscription

#### Option A: Using gcloud CLI (Recommended)

```bash
# Set default project
gcloud config set project MY_PROJECT_ID

# Create subscription
gcloud pubsub subscriptions create my-prism-signals \
  --topic=projects/galvanized-sled-435607-p6/topics/prism-trading-signals \
  --project=MY_PROJECT_ID

# Confirm subscription
gcloud pubsub subscriptions list
```

#### Option B: Using GCP Web Console

1. Go to the [Pub/Sub Subscriptions Console](https://console.cloud.google.com/cloudpubsub/subscription/list).
2. Click "Create Subscription".
3. Subscription ID: `my-prism-signals` (or any name you prefer).
4. Click "Select a Cloud Pub/Sub Topic".
5. Select "Enter a topic name from another project".
6. Enter: `projects/galvanized-sled-435607-p6/topics/prism-trading-signals`.

   *(For development/testing, we also provide a testing topic: `projects/galvanized-sled-435607-p6/topics/prism-trading-signals-test`. It is recommended to use the test topic for initial integrations.)*

7. Delivery Type: Pull
8. Click "Create".

### 4. Create a Service Account & Download Key

1. Visit [IAM Service Accounts Console](https://console.cloud.google.com/iam-admin/serviceaccounts).
2. Click "Create Service Account".
3. Name: `prism-subscriber`.
4. Role: Select "Pub/Sub Subscriber".
5. Complete service account creation, then click the newly created service account.
6. Go to the "Keys" tab → "Add Key" → "Create new key".
7. Choose JSON → Create.
8. Store the downloaded JSON key file securely.

### 5. Running Subscriber Clients

#### Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/prism-insight.git
cd prism-insight

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install required packages
pip install google-cloud-pubsub python-dotenv
```

#### Configure Environment Variables

Create a `.env` file at the root:
```bash
GCP_PROJECT_ID=MY_PROJECT_ID
GCP_PUBSUB_SUBSCRIPTION_ID=my-prism-signals
GCP_CREDENTIALS_PATH=/absolute/path/to/downloaded-key.json
```

#### Executing the Subscriber

Use the GCP Pub/Sub SDK to implement and run your own subscriber script to consume events from the topic.

## 📊 Message Data Formats

### BUY Signal

```json
{
  "type": "BUY",
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "price": 180.5,
  "timestamp": "2025-01-15T10:30:00",
  "target_price": 200.0,
  "stop_loss": 170.0,
  "investment_period": "Short-term",
  "sector": "Technology",
  "rationale": "Strong AI growth and technical breakout",
  "buy_score": 8,
  "source": "ai_analysis",
  "trade_success": true,
  "trade_message": "Buy execution complete"
}
```

### SELL Signal

```json
{
  "type": "SELL",
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "price": 200.0,
  "timestamp": "2025-01-20T14:20:00",
  "buy_price": 180.5,
  "profit_rate": 10.8,
  "sell_reason": "Target price reached",
  "source": "ai_analysis",
  "trade_success": true,
  "trade_message": "Sell execution complete"
}
```

### EVENT Signal

```json
{
  "type": "EVENT",
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "price": 180.5,
  "timestamp": "2025-01-15T12:00:00",
  "event_type": "NEWS_CATALYST",
  "event_description": "New product launch announcement",
  "source": "Financial News Wire"
}
```

## 💡 Practical Examples

### 1. Custom Notification System (Slack/Discord/Email)

```python
import json

def callback(message):
    signal = json.loads(message.data.decode("utf-8"))
    
    if signal["type"] == "BUY" and signal["buy_score"] >= 8:
        # Send Slack or Discord alert
        send_alert(f"🔥 Strong BUY signal: {signal['company_name']} ({signal['ticker']}) at ${signal['price']}")
    
    message.ack()
```

### 2. Auto-Trading Bot Integration

```python
def callback(message):
    signal = json.loads(message.data.decode("utf-8"))
    
    if signal["type"] == "BUY":
        # Call your broker's execution API
        my_broker_client.place_market_order(
            ticker=signal["ticker"],
            action="BUY",
            quantity=10
        )
    
    message.ack()
```

### 3. Data Collection and Database Storage

```python
def callback(message):
    signal = json.loads(message.data.decode("utf-8"))
    
    # Save signal payload to DB for archiving and backtesting
    save_to_db(signal)
    
    message.ack()
```

### 4. Custom Filter and Re-Publishing

```python
def callback(message):
    signal = json.loads(message.data.decode("utf-8"))
    
    # Filter for tech sector only
    if signal.get("sector") == "Technology":
        my_internal_publisher.publish(MY_INTERNAL_TOPIC, json.dumps(signal))
    
    message.ack()
```

## 🔧 Advanced Configurations

### Message Filtering (Subscriber-Side or Server-Side)

Create a subscription that only pulls buy signals:

```bash
gcloud pubsub subscriptions create my-buy-signals \
  --topic=projects/galvanized-sled-435607-p6/topics/prism-trading-signals \
  --filter='attributes.signal_type="BUY"' \
  --project=MY_PROJECT_ID
```

### Retry Policies

```bash
gcloud pubsub subscriptions update my-prism-signals \
  --min-retry-delay=10s \
  --max-retry-delay=600s \
  --project=MY_PROJECT_ID
```

### Dead Letter Queue (DLQ)

Handle message parsing failures by routing to a DLQ:

```bash
# Create DLQ topic
gcloud pubsub topics create my-prism-dlq --project=MY_PROJECT_ID

# Attach DLQ to subscription
gcloud pubsub subscriptions update my-prism-signals \
  --dead-letter-topic=my-prism-dlq \
  --max-delivery-attempts=5 \
  --project=MY_PROJECT_ID
```

## 🛠️ Troubleshooting

### No Messages Received

1. **Verify Subscription Status**:
```bash
gcloud pubsub subscriptions describe my-prism-signals --project=MY_PROJECT_ID
```

2. **Verify IAM Roles & Permissions**:
```bash
gcloud pubsub subscriptions get-iam-policy my-prism-signals --project=MY_PROJECT_ID
```

3. **Check Target Topic ID**: Ensure it is exactly `projects/galvanized-sled-435607-p6/topics/prism-trading-signals`.

### Authentication Errors

```bash
# Verify environment variable points to valid credentials path
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json

# Or verify .env configuration
cat .env | grep GCP_CREDENTIALS_PATH
```

### Incurring Unexpected Cost

1. **Set Alerts and Limits**: Go to GCP Console → Billing → Budgets & Alerts.
2. **Deactivate Subscription**:
```bash
gcloud pubsub subscriptions delete my-prism-signals --project=MY_PROJECT_ID
```

## 📞 Support & Resources
- **GitHub Issues**: https://github.com/your-repo/prism-insight/issues
- **Documentation**: https://github.com/your-repo/prism-insight/docs

## ⚠️ Disclaimer
- These signals are generated by an AI agent for research and simulation purposes and do **not** constitute financial advice.
- Investors are solely responsible for their financial decisions and risk management.
- PRISM-INSIGHT makes no guarantees regarding the accuracy or timeliness of the signals.

---

**Happy Trading! 📈**
