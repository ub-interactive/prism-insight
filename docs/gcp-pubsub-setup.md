# GCP Pub/Sub Web Console Configuration Guide

This guide details how to configure GCP Pub/Sub in the Google Cloud Console for use with PRISM-INSIGHT.

## 1. Create or Select a GCP Project

1. Visit the [Google Cloud Console](https://console.cloud.google.com).
2. Click the project selector dropdown at the top.
3. Select an existing project or click "New Project".
4. Enter a project name (e.g., `prism-insight`).
5. Click "Create".
6. Record the generated Project ID (e.g., `prism-insight-12345`).

## 2. Enable the Pub/Sub API

1. Go to the left menu > "APIs & Services" > "Library".
2. Search for "Pub/Sub" in the search box.
3. Click on "Cloud Pub/Sub API".
4. Click the "Enable" button.

## 3. Create a Topic

1. Go to the left menu > "Pub/Sub" > "Topics".
2. Click the "Create Topic" button.
3. Enter the Topic ID: `prism-trading-signals`.
4. Keep the default settings (encryption, schema, etc.).
5. Click "Create".

## 4. Create a Subscription

1. Go to the left menu > "Pub/Sub" > "Subscriptions".
2. Click the "Create Subscription" button.
3. Enter the Subscription ID: `prism-trading-signals-sub`.
4. Select the Cloud Pub/Sub Topic: `prism-trading-signals`.
5. Delivery Type: Select "Pull" (default).
6. Acknowledgement Deadline: 60 seconds (default).
7. Message Retention Duration: 7 days (default).
8. Click "Create".

## 5. Create a Service Account

1. Go to the left menu > "IAM & Admin" > "Service Accounts".
2. Click the "Create Service Account" button.
3. Enter the Service Account Name: `prism-pubsub-service`.
4. Enter the Description (optional): "PRISM-INSIGHT Pub/Sub access".
5. Click "Create and Continue".
6. Grant Access Roles:
   - Click the "Select a role" dropdown.
   - Choose "Pub/Sub Publisher".
   - Click "+ Add another role".
   - Choose "Pub/Sub Subscriber".
7. Click "Continue", then click "Done".

## 6. Generate Service Account Key

1. Click on the newly created Service Account.
2. Go to the "Keys" tab.
3. Click "Add Key" > "Create new key".
4. Select Key Type: JSON.
5. Click "Create".
6. Save the downloaded JSON file locally.
   - Example: `prism-insight-12345-abcdef123456.json`.
7. **Keep this file secure!** (Never commit it to Git.)

## 7. Configure .env File

Add the following variables to the `.env` file at the root of your project:

```bash
# GCP Pub/Sub Configuration
GCP_PROJECT_ID=prism-insight-12345
GCP_PUBSUB_TOPIC_ID=prism-trading-signals
GCP_PUBSUB_SUBSCRIPTION_ID=prism-trading-signals-sub
GCP_CREDENTIALS_PATH=/path/to/prism-insight-12345-abcdef123456.json
```

**Note**: `GCP_CREDENTIALS_PATH` must resolve to the **absolute path** of your downloaded JSON key file.

## 8. Package Installation

```bash
pip install google-cloud-pubsub
```

## 9. Verification Testing

### Publisher Verification

```python
import asyncio
from prism.messaging.gcp_pubsub_signal_publisher import SignalPublisher

async def test_publish():
    async with SignalPublisher() as publisher:
        result = await publisher.publish_buy_signal(
            ticker="AAPL",
            company_name="Apple Inc.",
            price=180.5,
            scenario={"target_price": 200.0}
        )
        print(f"Published: {result}")

asyncio.run(test_publish())
```

## Summary Reference

Resources Configured:
- ✅ Project ID: `prism-insight-12345`
- ✅ Topic: `prism-trading-signals`
- ✅ Subscription: `prism-trading-signals-sub`
- ✅ Service Account: `prism-pubsub-service`
- ✅ Key File: `prism-insight-12345-abcdef123456.json`

`.env` mappings:
```
GCP_PROJECT_ID=GCP_PROJECT_ID
GCP_PUBSUB_TOPIC_ID=prism-trading-signals
GCP_PUBSUB_SUBSCRIPTION_ID=prism-trading-signals-sub
GCP_CREDENTIALS_PATH=/absolute/path/to/json/key/file
```
