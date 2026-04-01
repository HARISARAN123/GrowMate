# GrowMate Voice Agent Setup Guide

## Overview
The GrowMate Voice Agent is a LiveKit-based voice assistant that runs as a separate worker process. It provides real-time voice support for:
- Plant disease detection and analysis
- Farming recommendations
- Agricultural best practices
- Bilingual support (English/Tamil)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GrowMate Web Frontend                   │
│                    (Flask + LiveKit Client)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    Token Gen    Room Creation   Diagnostics
    `/livekit-token` (Flask app.py)
        │
        └────────────────────────┬────────────────────────┐
                                 │                        │
                                 ▼                        ▼
                    ┌──────────────────────────────────────────┐
                    │   LiveKit Cloud Server                    │
                    │  (wss://onpitch-3p5r1jyv.livekit.cloud)  │
                    └──────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────────────────────┐
                    │   GrowMate Voice Agent Worker             │
                    │        (voice_agent.py)                   │
                    │  - Disease Detection                      │
                    │  - Recommendations                        │
                    │  - Bilingual Interaction                  │
                    │  - Delay Handling                         │
                    └──────────────────────────────────────────┘
```

## Prerequisites

### System Requirements
- Python 3.8+
- Windows, macOS, or Linux
- Active internet connection
- LiveKit cloud account (or on-premise server)

### Environment Variables (Already in .env)
```
LIVEKIT_URL=wss://onpitch-3p5r1jyv.livekit.cloud
LIVEKIT_API_KEY=APIBmZc5TL5yA2M
LIVEKIT_API_SECRET=TtFfOmjBtZ3H1pU9aBLx5cJ3pokykazca723yEANXxC
LIVEKIT_AGENT_NAME=Growmate Voice Bot
```

## Installation

### Step 1: Install Dependencies
In your GrowMate project root:

```bash
pip install -r requirements.txt
```

This installs:
- `livekit-agents>=0.12.0` - Agent framework
- `livekit-plugins-google>=0.10.0` - Google Realtime API for voice
- `livekit-plugins-noise-cancellation>=0.6.0` - Audio cleanup

### Step 2: Verify Environment
Ensure these files exist in your GrowMate root:
- `.env` - Configuration (must have LIVEKIT_* variables)
- `voice_agent.py` - The agent worker script
- `disease_detection.py` - Disease analysis module
- `firebase_service.py` - Firestore integration
- `class_indices.json` - Disease class mappings
- `plant_model_v5-beta.h5` - TensorFlow model

## Running the Agent Worker

### Option 1: Direct Python (Development)
```bash
cd d:\GrowMate
python voice_agent.py
```

The agent will start on port 8081 and connect to LiveKit servers.

**Expected Output:**
```
2026-04-01 12:00:00 INFO growmate-voice-agent: 🌾 Starting GrowMate Voice Agent...
```

### Option 2: Background Process (Windows)
Create `run_agent.ps1`:
```powershell
# GrowMate Voice Agent Launcher

Set-Location "d:\GrowMate"

# Check if agent is already running
$existing = Get-Process -Name "python" -ErrorAction SilentlyContinue | `
    Where-Object { $_.CommandLine -like "*voice_agent.py*" }

if ($existing) {
    Write-Host "Agent already running (PID: $($existing.Id))" -ForegroundColor Green
    exit 0
}

# Start the agent
Write-Host "Starting GrowMate Voice Agent..." -ForegroundColor Green
Start-Process python -ArgumentList "voice_agent.py" -NoNewWindow

Write-Host "Agent started on port 8081" -ForegroundColor Green
```

Run with:
```powershell
.\run_agent.ps1
```

### Option 3: Production Deployment (systemd for Linux)
Create `/etc/systemd/system/growmate-agent.service`:
```ini
[Unit]
Description=GrowMate Voice Agent
After=network.target

[Service]
Type=simple
User=growmate
WorkingDirectory=/home/growmate/GrowMate
Environment="PATH=/home/growmate/GrowMate/.venv/bin"
ExecStart=/home/growmate/GrowMate/.venv/bin/python voice_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable growmate-agent
sudo systemctl start growmate-agent
sudo systemctl status growmate-agent
```

## Running Flask Backend + Agent Together

### In Terminal 1 (Flask Web Server):
```bash
cd d:\GrowMate
python app.py
# Starts on http://localhost:5000
```

### In Terminal 2 (Voice Agent Worker):
```bash
cd d:\GrowMate
python voice_agent.py
# Starts on port 8081 (internal, connects to LiveKit)
```

### Then Open Browser:
```
http://localhost:5000/voicebot
```

## How It Works

### User Initiates Voice Call:
1. User opens `/voicebot` in browser
2. Frontend fills form (name, language, farm location)
3. Clicks "Start Voice Call"

### Backend Processes:
1. Flask route `/livekit-token` generates JWT token
2. Creates unique room ID: `voicebot-{uid}-{timestamp}`
3. Dispatches agent to room using `LIVEKIT_AGENT_NAME`

### Agent Worker Activates:
1. Receives dispatch notification from LiveKit
2. Joins the room as "Growmate Voice Bot"
3. Plays initial greeting (bilingual): "Welcome to GrowMate. Which language do you prefer?"
4. Listens to user and processes with LLM

### Tool Execution:
User's intent triggers one of three tools:
- **`get_farm_recommendations`**: For crop and farm advice
- **`analyze_plant_disease`**: For disease detection
- **`get_general_advice`**: For agricultural questions

### Delay Handling:
Long operations (>3 seconds) trigger progress updates:
- 3s: "Processing. Thank you for your patience."
- 8s: "Still processing. This may take a moment."
- 15s: "Almost done. Thank you for waiting."

### Session End:
User or agent ends call → Session metadata saved to Firestore.

## Troubleshooting

### Agent not joining room
Check:
```bash
# Verify transport
curl -H "Authorization: Bearer <token>" \
  https://onpitch-3p5r1jyv.livekit.cloud/api/rooms
```

### No audio from agent
- Ensure `google.beta.realtime.RealtimeModel` is configured
- Check Google Cloud project has Realtime API enabled
- Verify `GEMINI_API_KEY` in .env

### Tool calls not working
- Check disease_detection.py functions exist
- Verify plant_model_v5-beta.h5 is loaded
- Check Firebase service functions return valid JSON

### Agent disconnects frequently
- Check network stability
- Increase `PORT` if port conflicts occur
- Check LiveKit server logs

## Monitoring

### Check Room Participants:
```bash
curl -H "Authorization: Bearer <token>" \
  https://onpitch-3p5r1jyv.livekit.cloud/api/rooms/voicebot-{uid}-{random}/participants
```

### View Session Logs:
- Flask logs: Check terminal running `python app.py`
- Agent logs: Check terminal running `python voice_agent.py`
- Browser logs: Press F12 → Console tab

### Firestore Sessions:
Navigate to: Collections → `voice_sessions` → View metadata

## Performance Optimization

### Reduce Latency:
- Use regional LiveKit server closer to users
- Pre-load models in memory
- Cache frequent Gemini responses

### Scale Agent:
- Run multiple agent workers on different ports (8081, 8082, 8083...)
- Use load balancer to distribute dispatch calls
- Configure horizontal scaling with your deployment platform

## Security

- ✅ JWT tokens expire (default: 24 hours)
- ✅ API keys stored in .env (never commit to GitHub)
- ✅ Firebase auth protects routes
- ✅ Room IDs are unique per user session
- 🔄 Consider: Implement rate limiting on `/livekit-token`

## API Reference

### Frontend → Backend Routes

**POST `/livekit-token`**
```json
{
  "name": "Farmer Name",
  "language": "en",
  "farm_location": "Tamil Nadu"
}
```

Response:
```json
{
  "token": "jwt_token_here",
  "room": "voicebot-uid-abc123",
  "url": "wss://onpitch-3p5r1jyv.livekit.cloud",
  "participant_id": "par_abc123",
  "agent_dispatched": true,
  "dispatch_id": "AD_sAiaW8obMYvd"
}
```

**GET `/livekit-room-debug?room=voicebot-uid-abc123`**

Response:
```json
{
  "room_name": "voicebot-uid-abc123",
  "participant_count": 2,
  "participants": [
    {
      "name": "Farmer Name",
      "tracks": [{"type": "audio"}]
    },
    {
      "name": "Growmate Voice Bot",
      "tracks": [{"type": "audio"}]
    }
  ]
}
```

## Next Steps

1. **Test with simple conversation:**
   - "Hello" → Agent responds
   - "I have a sick tomato plant" → Offers disease analysis
   - "What should I grow?" → Asks clarifying questions

2. **Fine-tune instructions:**
   - Edit `instructions` in `GrowMateVoiceAgent.__init__()` in `voice_agent.py`
   - Customize prompts for your domain

3. **Add more tools:**
   - Weather forecast integration
   - Pest identification
   - Fertilizer calculator

4. **Integrate with backend:**
   - Save recordings to Firestore
   - Create farmer session history
   - Generate voice call transcripts

## Support

For issues, check:
- Agent logs: `python voice_agent.py` terminal output
- Flask logs: `python app.py` terminal output
- Browser console: F12 → Console
- Firestore: Check `voice_sessions` collection
- LiveKit API docs: https://docs.livekit.io/agents/
