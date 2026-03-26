# 🏥 WhatsApp Bot for Public Health Units (UBS) — Brazil's SUS/ESF

An open-source, production-ready WhatsApp bot built for **primary healthcare units** (UBS) in Brazil's Unified Health System (SUS). Designed for **Family Health Strategy (ESF)** teams serving rural and underserved communities where WhatsApp is often the only communication channel available.

Built entirely through pair-programming with **Claude AI (Anthropic)** — from architecture to deployment.

---

## 🎯 The Problem

In rural Brazil, many communities have limited cell signal — often only WiFi or low-bandwidth radio signal works. Phone calls don't go through, but **WhatsApp does**. Patients need basic health information (schedules, preparation for exams, emergency contacts, vaccination hours) but can only reach the health unit during business hours.

## 💡 The Solution

A WhatsApp bot that provides **24/7 automated access** to health unit information through interactive menus. No data collection, no clinical advice — just essential information that empowers patients to access healthcare services.

---

## ✨ Features

### Level 1 — Information
- **📅 Who's working today** — dynamic daily schedule with automatic Friday rotation logic
- **📍 Unit locations** — addresses, phone numbers, Google Maps links
- **👩‍⚕️ Full team directory** — all professionals with their days at each unit
- **💊 Pharmacy** — medication pickup schedule and instructions
- **📄 Registration documents** — what to bring for enrollment
- **🚨 Emergency guidance** — when to go to the ER vs. UBS, emergency phone numbers, hospital list for pregnant women
- **❓ FAQ** — 8 common questions with auto-splitting for WhatsApp character limits

### Level 2 — Health Programs & Education
- **HiperDia** (hypertension/diabetes), **Prenatal**, **Childcare**, **Vaccination**, **Women's Health**
- **Oral Health, Mental Health, Elderly Care, Physiotherapy** — each professional has their own section
- **Health education** — nutrition, exercise, medication, prevention tips
- **Community groups** — pregnancy, hypertension/diabetes, smoking cessation
- **Women's Health** — automatically calculates which days nurse + doctor are at the same unit

### Level 3 — Intelligence
- **⭐ Patient satisfaction survey** — rating + comments, stored in SQLite
- **📢 Campaign alerts** — admin creates announcements that appear in every patient's menu
- **📊 Usage metrics** — most accessed routes, messages per day, analytics dashboard
- **🔐 WhatsApp admin panel** — manage the bot via WhatsApp with password authentication
- **🤖 AI-powered Q&A** — placeholder ready for Claude API integration

### Security & Resilience
- HMAC webhook signature verification
- Rate limiting (10 messages/minute per phone number)
- Exponential backoff retry on API failures
- Global error handling with patient-friendly fallback messages
- Connection pooling (persistent httpx client)
- Pydantic config validation (clear errors instead of crashes)
- Periodic background cleanup (sessions, rate limiter, metrics purge)
- Unsupported media handling (audio, photo, sticker → friendly text response)

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Patient    │────▶│  Meta Cloud  │────▶│  FastAPI Server  │
│  (WhatsApp)  │◀────│  API (v25)   │◀────│  (Render.com)    │
└──────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                           ┌───────────────────────┼───────────────┐
                           │                       │               │
                    ┌──────▼──────┐  ┌─────────────▼──┐  ┌────────▼────────┐
                    │   Handlers  │  │   WhatsApp     │  │    SQLite DB    │
                    │  (12 files) │  │   Service      │  │  (metrics,      │
                    │             │  │  (pooling +    │  │   reviews,      │
                    │  menu       │  │   retry)       │  │   alerts)       │
                    │  info       │  └────────────────┘  └─────────────────┘
                    │  programas  │
                    │  exames     │
                    │  saude      │
                    │  grupos     │
                    │  emergencia │
                    │  nivel3     │
                    │  admin_wa   │
                    │  media      │
                    └─────────────┘
```

### Tech Stack
| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| HTTP Client | httpx (async, connection pooling) |
| WhatsApp API | Meta Cloud API v25.0 |
| Database | SQLite (WAL mode) |
| Deployment | Render.com (free tier) + Docker |
| Config Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio (29 tests) |
| AI Pair-Programming | Claude AI (Anthropic) |

---

## 📁 Project Structure

```
bot_ubs/
├── main.py                    # FastAPI app, webhook, routing, admin endpoints
├── config.json                # All UBS data (editable without touching code)
├── admin.py                   # Terminal admin panel
├── chat.py                    # Terminal chat simulator (for testing)
├── Dockerfile                 # Production Docker image
├── Procfile                   # Render deployment (non-Docker fallback)
├── requirements.txt
├── .env.example               # Environment variables template
│
├── handlers/                  # Message handlers (one file per domain)
│   ├── menu.py                # Main menu + submenus (interactive lists)
│   ├── info.py                # Dynamic schedule, units, team, documents
│   ├── programas.py           # Health programs (HiperDia, prenatal, etc.)
│   ├── exames.py              # Lab exams + pharmacy
│   ├── saude.py               # Oral, mental, elderly, physiotherapy
│   ├── grupos.py              # Community health groups
│   ├── emergencia.py          # Emergency/urgency guidance + FAQ
│   ├── nivel3.py              # Satisfaction survey + AI placeholder
│   ├── admin_wa.py            # WhatsApp-based admin panel
│   └── media.py               # Unsupported media response
│
├── services/
│   └── whatsapp.py            # WhatsApp Cloud API client (pooling + retry)
│
├── utils/
│   ├── session.py             # In-memory session management per phone
│   ├── security.py            # HMAC verification + rate limiting
│   ├── database.py            # SQLite persistence (reviews, metrics, alerts)
│   └── config_validator.py    # Pydantic schema validation for config.json
│
└── tests/
    └── test_bot.py            # 29 automated tests
```

---

## 🚀 Reproducing This Project

### Prerequisites
- Python 3.11+
- A Meta (Facebook) Developer account
- A phone number for WhatsApp Business (can be a landline)
- A Render.com account (free tier works)

---

### Step 1: Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/bot-ubs-whatsapp.git
cd bot-ubs-whatsapp

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Edit `config.json` with your health unit's real data: unit names, addresses, phone numbers, professionals, schedules, programs, etc. The bot reads everything from this file — **no code changes needed** to customize for your unit.

---

### Step 2: Meta Developer Setup

This is the most complex part. Follow carefully:

#### 2.1 — Create a Meta App
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **"My Apps"** → **"Create App"**
3. Choose **"Other"** → **"Business"** type
4. Name it (e.g., "Bot UBS") and create
5. On the products screen, find **"WhatsApp"** and click **"Set Up"**
   - If WhatsApp doesn't appear, go to **"Use Cases"** → filter by **"Business Messaging"** and add it

#### 2.2 — Add Your Phone Number
1. Go to **WhatsApp > API Setup** in the left sidebar
2. Click **"Add phone number"**
3. Enter your number with country code (+55 for Brazil)
4. For landlines, choose **"Phone call"** verification (not SMS)
5. Someone must answer the landline and note the 6-digit code
6. Enter the code to verify

⚠️ **Important**: If the number is already registered on WhatsApp Business app, you must either:
- Delete the account from the app first (Settings > Account > Delete), OR
- Use a different number

The number **cannot** be on both the WhatsApp app and Cloud API simultaneously.

#### 2.3 — Get Your Credentials
From the Meta Developer dashboard, collect:

| Credential | Where to Find |
|-----------|--------------|
| **Access Token** | WhatsApp > API Setup > "Generate access token" |
| **Phone Number ID** | WhatsApp > API Setup > below your number |
| **App Secret** | App Settings > Basic > "App Secret" (click "Show") |
| **WhatsApp Business Account ID** | WhatsApp > API Setup > below Phone Number ID |

#### 2.4 — Payment Method
Meta requires a payment method even for free tier usage:
- **1,000 service conversations/month are free**
- A credit/debit card is required as guarantee
- For a small health unit, you'll likely never exceed the free tier

#### 2.5 — Generate a Permanent Token
Temporary tokens expire in 24 hours. For production:

1. Go to [business.facebook.com](https://business.facebook.com) > **Settings**
2. **System Users** → Create a system user
3. Click **"Assign Assets"**:
   - **Apps** tab → select your app → Full Control → Save
   - **WhatsApp Accounts** tab → select your account → Full Control → Save
4. Click **"Generate Token"** → select your app → set expiration to "Never"
5. Check permissions: `whatsapp_business_messaging` and `whatsapp_business_management`
6. Generate and copy the permanent token

---

### Step 3: Configure Webhook

#### 3.1 — Local Testing with ngrok
```bash
# Terminal 1: Start the server
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Expose with ngrok
ngrok http 8000
# Copy the https URL (e.g., https://abc123.ngrok-free.app)
```

#### 3.2 — Register Webhook on Meta
1. In Meta Developer, go to **WhatsApp > Configuration**
2. Under **"Webhook"**, click **"Edit"**
3. **Callback URL**: `https://YOUR_URL/webhook` (ngrok URL + `/webhook`)
4. **Verify Token**: same value as `WEBHOOK_VERIFY_TOKEN` in your `.env`
5. Click **"Verify and Save"**
6. Below, under **"Webhook Fields"**, click **"Manage"** and subscribe to **"messages"**

⚠️ **Critical**: The `messages` field must be subscribed on your **production** WhatsApp Business Account, not just the test account. If messages aren't arriving, run this command to force-subscribe:

```bash
# PowerShell (Windows)
Invoke-RestMethod -Method POST -Uri "https://graph.facebook.com/v25.0/YOUR_WABA_ID/subscribed_apps" -Headers @{"Authorization"="Bearer YOUR_TOKEN"}

# Bash (Linux/Mac)
curl -X POST "https://graph.facebook.com/v25.0/YOUR_WABA_ID/subscribed_apps" -H "Authorization: Bearer YOUR_TOKEN"
```

Replace `YOUR_WABA_ID` with your WhatsApp Business Account ID.

#### 3.3 — Publish the App
1. In Meta Developer, go to **"Publish"** in the left sidebar
2. Click publish (may require a Privacy Policy URL — any URL works initially)

---

### Step 4: Deploy to Render (Free Hosting)

1. Push your code to GitHub (**without** the `.env` file — use `.gitignore`)

2. Go to [render.com](https://render.com) → **New Web Service** → connect your GitHub repo

3. Configure:
   - **Environment**: Docker
   - **Health Check Path**: `/health`

4. Add **Environment Variables** (not Secret Files):

| Key | Value |
|-----|-------|
| `WHATSAPP_TOKEN` | Your permanent token |
| `WHATSAPP_PHONE_ID` | Your phone number ID |
| `WEBHOOK_VERIFY_TOKEN` | Your chosen verify token |
| `WHATSAPP_APP_SECRET` | Your app secret |
| `ADMIN_TOKEN` | A strong password for admin access |
| `DB_PATH` | `/data/bot_ubs.db` |
| `PYTHONUNBUFFERED` | `1` |

5. Deploy → wait for `🟢 Bot UBS v3.1 pronto!`

6. Copy your Render URL (e.g., `https://your-bot.onrender.com`)

7. Go back to Meta and **update the webhook URL** to:
   ```
   https://your-bot.onrender.com/webhook
   ```

⚠️ **Render free tier**: The server sleeps after 15 minutes of inactivity. First message after sleep takes ~30 seconds. For always-on, consider Render paid ($7/month) or Railway.

---

### Step 5: Test

Send **"oi"** from any WhatsApp to your registered phone number. The bot should respond with the interactive menu.

**Quick test links:**
```
# Test terminal simulator (no server needed)
python chat.py

# Run automated tests
python -m pytest tests/ -v

# Terminal admin panel
python admin.py
```

---

## 🔐 Admin Panel

### Via WhatsApp
Send to the bot's number:
```
admin YOUR_ADMIN_TOKEN
```
Opens an interactive menu to:
- Create/remove campaign announcements
- View patient satisfaction ratings
- View usage metrics
- Exit admin mode

### Via Terminal
```bash
python admin.py
```

### Via API
```bash
# View metrics
curl "https://your-bot.onrender.com/admin/metricas?token=YOUR_TOKEN&dias=30"

# View ratings
curl "https://your-bot.onrender.com/admin/avaliacoes?token=YOUR_TOKEN"

# Create announcement
curl -X POST "https://your-bot.onrender.com/admin/aviso" \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN", "mensagem": "Flu vaccination campaign this Saturday!"}'
```

---

## 🔧 Customization

### Adding a New Menu Option

1. Create a handler in `handlers/your_handler.py`:
```python
from services.whatsapp import WhatsAppService

async def handle_your_feature(phone: str, wa: WhatsAppService, config: dict) -> None:
    msg = "Your message here\n\nDigite *menu* para voltar."
    await wa.send_text(to=phone, body=msg)
```

2. Import in `handlers/__init__.py`:
```python
from .your_handler import handle_your_feature
```

3. Add to `ROUTE_MAP` in `main.py`:
```python
ROUTE_MAP = {
    ...
    "YOUR_FEATURE": handle_your_feature,
}
```

4. Add to a menu/submenu in `handlers/menu.py`:
```python
{"id": "YOUR_FEATURE", "title": "Your Title", "description": "Description"}
```

### Modifying Content
Edit `config.json` — no code changes needed. The bot reads all content from this file at startup.

---

## 🤖 Built with Claude AI

This entire project was built through pair-programming with **Claude AI (Anthropic)**. The development process:

1. **Architecture Design** — Claude designed the modular handler-based architecture, session management, and security layers
2. **Implementation** — All Python code was written collaboratively, with Claude generating complete files and the developer testing/deploying
3. **Code Review & Hardening** — Claude performed security audits identifying 15 vulnerabilities across 5 categories, then fixed all of them
4. **Meta Integration** — Claude provided step-by-step guidance for Meta Developer setup, webhook configuration, and troubleshooting
5. **Deployment** — Claude configured Docker, Render.com deployment, and production environment variables
6. **Content Creation** — Claude generated all patient-facing messages, FAQ content, emergency guidance, and WhatsApp Business catalog descriptions

The AI was used as a **copilot** — the developer (a nurse) provided all domain expertise about healthcare workflows, patient needs, and unit operations. Claude translated that knowledge into working software.

---

## 📋 Troubleshooting

| Problem | Solution |
|---------|----------|
| Webhook returns 403 | Check that `.env` file has the correct name (`.env`, not `env`) and `WEBHOOK_VERIFY_TOKEN` matches Meta |
| Messages not arriving | Subscribe `messages` field on your production WABA, not test account. Use the `subscribed_apps` API call |
| `Bearer` errors in logs | Access token is empty or expired. Generate a new permanent token |
| Bot doesn't respond | Check Render logs. Add `PYTHONUNBUFFERED=1` to env vars for real-time logging |
| `Session expired` error | Access token expired (24h for temporary). Generate a permanent token via System Users |
| Config validation fails | A required field is missing from `config.json`. Error message tells you exactly which field |

---

## 📄 License

MIT License — feel free to adapt for your own health unit.

---

## 🙏 Acknowledgments

- **Brazil's SUS** (Unified Health System) — for providing universal healthcare
- **Anthropic's Claude AI** — for making this development possible through AI pair-programming
- **Meta's WhatsApp Cloud API** — for the free tier that makes this viable for public health
- **Render.com** — for free hosting that keeps the bot running

---

*Built with ❤️ for public health by Lucas Daniel — ESF Nurse, Uberaba/MG, Brazil*
