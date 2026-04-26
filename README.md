<<<<<<< HEAD
# Multilingual Real-Time Chat Platform

This repository contains a hackathon-ready backend scaffold for a many-to-many multilingual chat system.

## What is included

- FastAPI HTTP API for onboarding and message submission
- Socket.IO real-time delivery per user room
- Preference lookup with a single cache read for sender and recipients
- Pluggable language detection
- Pluggable translation provider with caching
- In-memory defaults so the service runs without external infrastructure

## Core flow

1. Users submit preferred languages during onboarding.
2. The message service fetches sender and recipient preferences in one cache batch.
3. Language is detected on every message.
4. The translation layer resolves one translated variant per recipient language.
5. The translated payload is stored and emitted to recipient rooms.

## Run locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the API:

```bash
uvicorn app.main:app --reload
```

3. Open the health endpoint:

```bash
GET /health
```

## Notes

- The default translation provider is a mock adapter so the scaffold works immediately.
- Swap in IndicTrans2 or an API-backed provider by implementing the `TranslationProvider` protocol in `app/services/translation.py`.
- Swap in Redis, PostgreSQL, and MongoDB adapters through the repository and cache protocols in `app/storage.py`.
=======
# Bhasha_Chat
>>>>>>> 57c816f6193ec9b5425001f8b55f0e1e2c6ed0fd
