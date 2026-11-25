# unified-alerts 🚀

[![CI](https://github.com/vinu24/unified-alerts/actions/workflows/ci.yml/badge.svg)](https://github.com/vinu24/unified-alerts/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/unified-alerts/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight, zero-dependency Python notification library providing a unified, fluent API for sending structured alerts to **Slack** (Incoming Webhooks and Bot API) and **Telegram** (Bot API).

Designed to integrate seamlessly into **Django**, **FastAPI**, **Flask**, or any standalone Python service or background worker.

---

## ✨ Features

- **Zero External Dependencies**: Built entirely with Python's standard library (`urllib.request`). No heavy requests/httpx dependencies required.
- **Unified Fluent API**: Construct rich messages with `.field()`, `.action()`, and `.channel()` regardless of destination.
- **Multiple Supported Backends**:
  - **Slack Incoming Webhook**: Simple channel-locked webhooks with structured Block Kit layouts.
  - **Slack Bot Token (`xoxb-`)**: Dynamic multi-channel routing with custom bot authentication (`chat.postMessage`).
  - **Telegram Bot API**: HTML message formatting with inline action URL buttons.
  - **Console Driver**: Colorized local terminal output for debugging.
  - **Memory Driver**: In-memory message outbox for fast, isolated unit testing.
- **Multi-Driver Dispatch**: Broadcast alerts to Slack and Telegram simultaneously.
- **Fail-Safe & Non-Blocking**: Delivery errors are logged cleanly and never crash host applications.
- **First-Class Django Integration**: Ready-to-use Django app with settings auto-loading and `manage.py test_alerts` CLI command.

---

## 📦 Installation

```bash
pip install unified-alerts
```

---

## 🚀 Quickstart

### 1. Fluent Alert Construction

```python
from unified_alerts import Alert

# Broadcast an informational alert
Alert.info("Deployment Succeeded", "Version 2.4.0 successfully deployed.") \
    .field("Service", "payment-gateway") \
    .field("Environment", "production") \
    .action("View Metrics", "https://grafana.example.com/d/payments") \
    .send()
```

### 2. Available Alert Levels

Each alert level includes corresponding emojis and native Slack attachment border colors:

```python
Alert.info("Sync Completed")       # ℹ️ Blue
Alert.success("Order Processed")   # ✅ Green
Alert.warning("High Memory Usage") # ⚠️ Yellow
Alert.error("Payment Failed")      # 🚨 Red
Alert.critical("Database Down")    # 🛑 Dark Red
```

---

## ⚙️ Configuration

### Option A: Environment Variables (Recommended)

`unified-alerts` automatically detects standard environment variables:

```bash
# Slack Incoming Webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/X00"

# OR Slack Bot API (Token + Default Channel)
export SLACK_BOT_TOKEN="xoxb-1234567890-..."
export SLACK_CHANNEL="#alerts"

# Telegram Bot API (Token + Chat ID)
export TELEGRAM_BOT_TOKEN="123456789:ABC-DEF..."
export TELEGRAM_CHAT_ID="-1001234567890"

# Optional: Force local console mode during development
export ALERTS_BACKEND="console"
```

Once exported, simply invoke `.send()`:

```python
from unified_alerts import Alert

Alert.warning("Queue Depth Exceeded").field("Depth", 450).send()
```

---

### Option B: Programmatic Configuration via `AlertManager`

Configure drivers programmatically or dynamically at application startup:

```python
from unified_alerts import Alert, AlertManager, SlackBotDriver, TelegramDriver

manager = AlertManager()

# Register drivers
manager.register("slack", SlackBotDriver(
    bot_token="xoxb-your-token",
    default_channel="#dev-ops"
), as_default=True)

manager.register("telegram", TelegramDriver(
    bot_token="123456:ABC-DEF...",
    default_chat_id="-100123456789"
), as_default=True)

# Send through custom manager
Alert.critical("Database Out of Memory").send(manager=manager)
```

You can also route an alert to a specific driver or channel on the fly:

```python
# Route only to Telegram
Alert.info("Nightly Backup Finished") \
    .to_driver("telegram") \
    .send()

# Route to a specific Slack channel
Alert.error("Customer Churn Risk") \
    .channel("#account-managers") \
    .send()
```

---

## 🎸 Django Integration

### 1. Add to `INSTALLED_APPS`

In your Django `settings.py`:

```python
INSTALLED_APPS = [
    ...,
    "unified_alerts.contrib.django",
]
```

### 2. Configure `UNIFIED_ALERTS` in `settings.py`

```python
UNIFIED_ALERTS = {
    "default": ["slack", "telegram"],
    "drivers": {
        "slack": {
            "type": "bot", # or "webhook"
            "token": os.getenv("SLACK_BOT_TOKEN"),
            "channel": "#django-alerts",
        },
        "telegram": {
            "token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        },
    },
}
```

### 3. Verify Delivery via Django Management Command

Test your integration and token credentials directly from the command line:

```bash
# Verify all configured drivers
python manage.py test_alerts

# Test a specific driver
python manage.py test_alerts --driver slack

# Test targeting a custom channel
python manage.py test_alerts --driver slack --channel "#emergency-alerts"
```

---

## 🧪 Testing Your Application

When writing unit tests for your application, swap the backend to `memory` to prevent network requests and make assertions against sent alerts:

```python
import unittest
from unified_alerts import Alert, AlertManager, MemoryDriver

class OrderTestCase(unittest.TestCase):
    def setUp(self):
        self.outbox = MemoryDriver()
        self.mgr = AlertManager()
        self.mgr.register("memory", self.outbox, as_default=True)

    def test_order_creation_triggers_alert(self):
        # Your service logic that calls Alert.success(...).send(manager=self.mgr)
        Alert.success("Order Created").field("Order ID", "1042").send(manager=self.mgr)

        self.assertEqual(len(self.outbox.outbox), 1)
        self.assertEqual(self.outbox.outbox[0].title, "Order Created")
        self.assertEqual(self.outbox.outbox[0].fields[0].value, "1042")
```

---

## 🛠️ Development

Run unit tests locally using standard library `unittest`:

```bash
# Run all tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
