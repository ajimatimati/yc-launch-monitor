# 🚀 YC & Speedrun Launch Monitor Slack Bot

> **A real-time GTM intelligence radar and persistent Slack bot that monitors Y Combinator & a16z Speedrun startup launches across 4 continuous data streams, specifically detecting early founder announcements before official directory publication.**

[![Pond Protocol V1](https://img.shields.io/badge/Pond%20Protocol-v1.0-blue.svg)](https://joinpond.ai)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Slack Block Kit](https://img.shields.io/badge/Slack-Block%20Kit-4A154B.svg)](https://api.slack.com/block-kit)
[![Cost](https://img.shields.io/badge/Cost-%240.00%20(100%25%20Free)-success.svg)]()
[![Author](https://img.shields.io/badge/Author-ajimatimati-orange.svg)](https://github.com/ajimatimati)

---

## 📌 Overview

Built for **Go-To-Market (GTM) professionals and Business Development leaders at Rho**, this bot provides an unfair advantage by alerting you the second a new YC or Speedrun company is launched.

Most tools wait for official YC directory updates or press releases. **This bot actively catches early signals from founders announcing their acceptance on X (Twitter) and LinkedIn days or weeks before YC officially lists them.**

```
                               ┌────────────────────────────────────────────────────────┐
                               │             4 Continuous Monitoring Sources             │
                               └────────────────────────────────────────────────────────┘
                                      │                  │                 │
              ┌───────────────────────┴─────────┐        │        ┌────────┴────────────────────────┐
              ▼                                 ▼        │        ▼                                 ▼
   📙 YC Official Directory            🚀 Speedrun API   │   🐦 X (Twitter) Feeds          💼 LinkedIn Feeds
 (Algolia Real-Time Index)           (a16z Next.js API)  │ (Search + Syndication)          (Post Index & Web)
              │                                 │        │        │                                 │
              └────────────────────────┬────────┘        │        └────────────────┬────────────────┘
                                       │                 │                         │
                                       ▼                 ▼                         ▼
                            ┌─────────────────────────────────────────────────────────────┐
                            │            Stateful Deduplication & NLP Classifier          │
                            │           (SQLite Persistent State Machine: 8h Loop)        │
                            └─────────────────────────────────────────────────────────────┘
                                                         │
                                    ┌────────────────────┴────────────────────┐
                                    ▼                                         ▼
                     💬 Slack App (Block Kit Alert)            🤖 Pond Agent Protocol V1
                   • 🔥 Early Founder Signal Cards            • GET /manifest (Public Spec)
                   • ✅ Confirmed Official Launches           • POST /runs (Idempotent Exec)
                   • 📱 Quick Outreach CTA Actions            • GET /health (Infra Monitoring)
```

---

## 🔥 Key Innovations & Capabilities

1. **Early-Detection Social Intelligence**:
   - Specifically highlights founders posting on X or LinkedIn (*e.g., "We got into YC S26! Moving to SF..."*) before YC makes an official announcement.
   - Extracts company name, founder social handle, batch/cohort, website domain, and original quote.
2. **Persistent Stateful SQLite Engine**:
   - Maintains complete history in local SQLite (`yc_launches.db`).
   - Automatically handles the lifecycle state machine:
     $$\text{EARLY\_SIGNAL (Social Feed)} \longrightarrow \text{CONFIRMED (Official Directory)}$$
   - Runs continuously on an **8-hour cadence** with zero duplicate alerts.
3. **Four Distinct Data Sources Monitored**:
   - **YC Directory**: Direct integration with YC's live Algolia production index (`YCCompany_By_Launch_Date_production`).
   - **Speedrun Directory**: Direct integration with `speedrun-api.a16z.com` and Next.js SSR scraper.
   - **X (Twitter)**: Multi-strategy monitoring (API v2 + Zero-Cost Search Syndication/RSS fallback).
   - **LinkedIn**: Zero-cost web search indexing and founder post scraper.
4. **Interactive Slack Block Kit Alerting**:
   - Eye-catching cards with color-coded badges:
     - `🔥 EARLY YC SIGNAL — Founder Announced Before YC`
     - `⚡ EARLY SPEEDRUN SIGNAL — Founder Announced Before Directory`
     - `✅ NEW YC COMPANY — CONFIRMED BY YC`
     - `🚀 NEW SPEEDRUN COMPANY LAUNCH`
   - Interactive buttons: `📱 Open Post`, `🌐 Visit Website`, `📙 View YC Profile`.
5. **Pond Agent Infrastructure Compliance**:
   - Full implementation of **Pond Protocol V1** (`https://joinpond.ai/agent/create`).
   - Provides public `GET /manifest`, Bearer-authenticated `POST /runs`, and `GET /health` infrastructure monitoring.
6. **Zero Running Cost (\$0.00)**:
   - Built 100% on open-source libraries, free public endpoints, and free-tier integrations.

---

## 📸 Proof of Functionality & Example Deliverables

### Example 1 — Early YC Founder Detection 🔥
```
🔥 EARLY YC SIGNAL — Founder Announced Before YC
Company: Acme AI (https://acme.ai)
Founder: Jane Doe (@janedoe)
Batch: YC S26
Source: X (Twitter)
Status: ⚡ Founder announced / not yet officially announced by YC

Original post:
"We got into YC S26! Excited to move to SF and start building."

🔗 Original post: https://x.com/janedoe/status/2061493360150601738
🌐 Website: https://acme.ai
🕒 Detected: Aug. 29, 2026, 9:14 AM UTC
[ 📱 Open Post on X ]  [ 🌐 Visit Website ]
```

### Example 2 — Official YC Confirmation ✅
```
✅ NEW YC COMPANY — CONFIRMED BY YC
Company: Talos (https://www.talos-us.com/)
Batch: Fall 2026
Source: YC Directory
Status: ✅ Confirmed by YC

Description: Predictive maintenance for power infrastructure.
📙 YC Profile: https://www.ycombinator.com/companies/talos-us
🌐 Website: https://www.talos-us.com/
🕒 Detected: Aug. 29, 2026, 2:03 PM UTC
[ 📙 View YC Profile ]  [ 🌐 Visit Website ]
```

> 💡 **Visual HTML Proof:** An interactive browser rendering of these alerts is available at [`docs/slack_demo_preview.html`](docs/slack_demo_preview.html).

---

## 🛠️ Step-by-Step Installation & Setup

### Prerequisites
- Python 3.10+ installed
- Slack Workspace (Free or Paid)

### Step 1: Clone and Install Dependencies
```bash
git clone https://github.com/ajimatimati/yc-launch-monitor.git
cd yc-launch-monitor
pip install -r requirements.txt
```

### Step 2: 1-Click Slack App Creation (10 Seconds)
1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App** $\rightarrow$ **From an app manifest**.
2. Select your workspace.
3. Paste the contents of [`manifest.json`](manifest.json) into the JSON tab and click **Create**.
4. In **OAuth & Permissions**, click **Install to Workspace**.
5. Copy the **Bot User OAuth Token** (starts with `xoxb-...`).

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your tokens:
```ini
# Slack Bot Token & Channel
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL_ID=C0123456789  # Target Channel ID or User ID for DMs

# Polling interval in hours (Default: 8)
POLL_INTERVAL_HOURS=8

# Optional: Pond Access Key
POND_ACCESS_KEY=pond_sk_yc_launch_monitor_2026
```

---

## 🎮 Running the Bot

### 1. Test Slack Alert Formatting (Dry Run or Live)
```bash
# Test alert formatting in terminal preview
python cli.py test-slack --dry-run

# Send real test cards to your Slack channel
python cli.py test-slack
```

### 2. Run an Immediate Incremental Scan
```bash
# Scan all 4 sources in dry-run mode
python cli.py scan --dry-run

# Scan and push real-time alerts to Slack
python cli.py scan
```

### 3. View Tracked Companies & Stats
```bash
# View database statistics (total tracked, early signals, confirmed)
python cli.py stats

# List tracked launches
python cli.py list-launches --limit 20
```

### 4. Start the Continuous Daemon & Pond Agent Server
```bash
# Starts Pond Protocol V1 server on port 8000 + 8-hour continuous scheduler
python cli.py serve --port 8000
```

---

## 🤖 Pond Agent Infrastructure Integration

This agent is built to integrate natively with **Pond** ([https://joinpond.ai/agent/create](https://joinpond.ai/agent/create)).

### Pond Protocol V1 Endpoints
| Endpoint | Method | Purpose | Auth |
| :--- | :--- | :--- | :--- |
| `/manifest` | `GET` | Public discovery returning Pond V1 schema, metadata, actions, limits | None (Public) |
| `/runs` | `POST` | Executes agent runs (e.g. `check_new_launches`, `search_yc_companies`) | `Bearer <POND_ACCESS_KEY>` |
| `/health` | `GET` | Health check reporting DB status, uptime, crawler health, and Slack status | None (Public) |

### Pond Manifest Verification
```bash
curl http://localhost:8000/manifest
curl http://localhost:8000/health
```

### Publishing on Pond (`joinpond.ai`)
1. Host the agent server on any public HTTPS URL (e.g., Render, Railway, fly.io, or ngrok for local testing).
2. Go to [joinpond.ai/agent/create](https://joinpond.ai/agent/create).
3. Set **Server Base URL** to your hosted domain (e.g. `https://yc-monitor.example.com`).
4. Set **Access Key** to match your `POND_ACCESS_KEY`.
5. Pond will automatically query `GET /manifest` and pre-populate the agent listing!

---

## 🧪 Automated Test Suite

The project includes unit and integration tests covering database state management, Algolia YC parsing, Speedrun API parsing, social NLP extraction, Slack Block Kit generation, and Pond Protocol endpoints.

Run tests with:
```bash
pytest -v
```

Output:
```text
tests/test_database.py::test_save_and_retrieve_launch PASSED             [  5%]
tests/test_database.py::test_deduplication_and_upgrade_to_confirmed PASSED [ 11%]
tests/test_database.py::test_stats_and_filtering PASSED                  [ 17%]
tests/test_database.py::test_idempotency_store PASSED                    [ 23%]
tests/test_monitors.py::test_yc_directory_algolia_parsing PASSED         [ 29%]
tests/test_monitors.py::test_speedrun_api_parsing PASSED                 [ 35%]
tests/test_monitors.py::test_x_twitter_early_signal_extraction PASSED    [ 41%]
tests/test_monitors.py::test_linkedin_early_signal_extraction PASSED     [ 47%]
tests/test_pond.py::test_pond_manifest_public PASSED                     [ 52%]
tests/test_pond.py::test_pond_health_check PASSED                        [ 58%]
tests/test_pond.py::test_pond_run_unauthorized PASSED                    [ 64%]
tests/test_pond.py::test_pond_run_invalid_protocol_version PASSED        [ 70%]
tests/test_pond.py::test_pond_run_get_monitor_status PASSED              [ 76%]
tests/test_pond.py::test_pond_run_idempotency PASSED                     [ 82%]
tests/test_slack.py::test_slack_block_builder_early_signal PASSED        [ 88%]
tests/test_slack.py::test_slack_block_builder_confirmed_speedrun PASSED  [ 94%]
tests/test_slack.py::test_slack_notifier_dry_run PASSED                  [100%]

============================= 17 passed in 2.26s ==============================
```

---

## 🔮 Future Upgradability

The monitor is architected around an extensible `BaseMonitor` interface (`yc_launch_monitor/monitors/base.py`). To add a new platform in the future (e.g. **Bluesky**, **Product Hunt**, **Hacker News "Launch YC"**, **Reddit r/ycombinator**):

1. Create a new file in `yc_launch_monitor/monitors/my_source.py` inheriting from `BaseMonitor`.
2. Implement `scan() -> List[LaunchItem]`.
3. Register the monitor in `yc_launch_monitor/engine.py`.

The database state machine, deduplication, Slack alerting, and Pond protocol will automatically handle the new stream with zero extra wiring.

---

## 💰 Cost Breakdown

| Component | Provider / Tool | Cost |
| :--- | :--- | :--- |
| **Slack Bot Integration** | Slack API (Personal Workspace App) | **$0.00 / Free** |
| **Stateful Persistence** | Embedded SQLite 3 | **$0.00 / Free** |
| **YC Directory Ingestion** | Public Algolia Index Endpoint | **$0.00 / Free** |
| **Speedrun Ingestion** | Public Speedrun API | **$0.00 / Free** |
| **X & LinkedIn Detection** | Web Syndication & Search Index Fallback | **$0.00 / Free** |
| **Pond Agent Protocol** | Pond Protocol V1 Server | **$0.00 / Free** |
| **Total Monthly Cost** | | **$0.00** |

---

## 👤 Author & Support

- **Author**: Abiodun Ajimati
- **GitHub**: [@ajimatimati](https://github.com/ajimatimati)
- **Email**: [ajimatimati@gmail.com](mailto:ajimatimati@gmail.com)
- **Target User**: Jayson Fung (Senior GTM Professional at Rho)
