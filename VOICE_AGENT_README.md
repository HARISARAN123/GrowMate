# GrowMate Voice Agent Worker

Complete LiveKit-based voice agent for real-time agricultural support with bilingual interface and AI-powered tool calling.

## Features

### 🎯 Core Capabilities
- **Plant Disease Detection** - Analyze images and get treatment recommendations
- **Farming Recommendations** - Personalized advice based on crop and region
- **General Agricultural Advice** - Tips on irrigation, pest control, soil management
- **Bilingual Interface** - Seamless English/Tamil conversation switching
- **Delay Handling** - Keeps users engaged during long operations with progress updates
- **Error Recovery** - Graceful error handling with user-friendly messages

### 🔧 Technical Features
- **Real-time Voice** - WebSocket streaming via LiveKit
- **Tool Calling** - LLM-powered tool invocation with parameter extraction
- **Async Processing** - Non-blocking operations with proper timeout handling
- **Noise Cancellation** - BVC (Background Voice Cancellation) for clean audio
- **Firebase Integration** - Session persistence and metadata logging
- **Google Realtime API** - State-of-the-art voice interaction

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  GrowMate Frontend (voicebot.html)                   │
│  - Form collection (name, language, location)       │
│  - Real-time audio streaming                        │
│  - Status display and debugging                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ /livekit-token (Flask)
                  ▼
┌─────────────────────────────────────────────────────┐
│  Flask Backend (app.py)                              │
│  - JWT token generation                             │
│  - Room creation                                    │
│  - Agent dispatch to LiveKit                        │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Dispatch Request
                  ▼
┌─────────────────────────────────────────────────────┐
│  LiveKit Cloud (onpitch-3p5r1jyv.livekit.cloud)     │
│  - Room management                                  │
│  - Participant coordination                         │
│  - Media relay                                      │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Agent Dispatch Event
                  ▼
┌─────────────────────────────────────────────────────┐
│  GrowMate Voice Agent (voice_agent.py)               │
│  ┌──────────────────────────────────────────────┐   │
│  │ Greeting (English/Tamil)                     │   │
│  ├──────────────────────────────────────────────┤   │
│  │ LLM Context:                                 │   │
│  │  - System instructions (role, tone)          │   │
│  │  - Available tools (function signatures)     │   │
│  │  - Language preference                       │   │
│  ├──────────────────────────────────────────────┤   │
│  │ Tool Execution:                              │   │
│  │  ├─ get_farm_recommendations()               │   │
│  │  ├─ analyze_plant_disease()                  │   │
│  │  └─ get_general_advice()                     │   │
│  ├──────────────────────────────────────────────┤   │
│  │ Delay Handler:                               │   │
│  │  - 3s: "Processing. Thank you..."            │   │
│  │  - 8s: "Still processing..."                 │   │
│  │  - 15s: "Almost done..."                     │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Installation

### 1. Install Dependencies
```bash
cd d:\GrowMate
pip install -r requirements.txt
```

Required packages:
- `livekit` - WebRTC client library
- `livekit-agents` - Agent framework
- `livekit-plugins-google` - Google Realtime API integration
- `livekit-plugins-noise-cancellation` - Audio preprocessing
- Plus existing: Flask, Firebase, TensorFlow, etc.

### 2. Verify Configuration

Check `.env` has these keys:
```env
LIVEKIT_URL=wss://onpitch-3p5r1jyv.livekit.cloud
LIVEKIT_API_KEY=APIBmZc5TL5yA2M
LIVEKIT_API_SECRET=TtFfOmjBtZ3H1pU9aBLx5cJ3pokykazca723yEANXxC
LIVEKIT_AGENT_NAME=Growmate Voice Bot
```

Check these files exist:
- `voice_agent.py` - Main agent worker
- `plant_model_v5-beta.h5` - TensorFlow disease model
- `class_indices.json` - Disease labels
- `disease_detection.py` - Analysis module
- `firebase_service.py` - Firestore functions

## Quick Start

### Development Mode

#### Using Batch Script (Windows):
```bash
d:\GrowMate\start-dev.bat
```

This will:
1. Verify Python installation
2. Check dependencies
3. Start Flask backend (port 5000)
4. Start Voice Agent (port 8081)
5. Open two terminal windows

#### Using PowerShell:
```powershell
d:\GrowMate\start-dev.ps1 -CheckOnly:$false
```

Optional flags:
- `-CheckOnly` - Just verify setup, don't start
- `-BackendPort 5001` - Use different Flask port
- `-AgentPort 8082` - Use different Agent port

#### Manual Start (Two Terminals):

**Terminal 1 (Flask):**
```bash
cd d:\GrowMate
python app.py
# http://localhost:5000
```

**Terminal 2 (Agent):**
```bash
cd d:\GrowMate
python voice_agent.py
# Connects to LiveKit on port 8081 (internal)
```

### Access Application
Open browser: http://localhost:5000/voicebot

Fill the form:
- Name: Your name
- Language: English or Tamil
- Farm Location: Your region (optional)

Click **"Start Voice Call"**

## Tool Schema Reference

### Tool 1: get_farm_recommendations
**When triggered:** User asks for farming advice  
**Required parameters:**
- `crop_type` (str) - "rice", "wheat", "tomato", etc.
- `farm_size` (str) - "1 acre", "5 hectares", etc.
- `region` (str) - "Tamil Nadu", "Maharashtra", etc.

**Returns:**
```json
{
  "status": "success",
  "recommendations": "Best practices for rice farming in Tamil Nadu...",
  "crop_type": "rice"
}
```

**Agent behavior:**
1. Asks: "What crop are you growing?"
2. Asks: "What is your farm size?"
3. Asks: "What region are you in?"
4. Says: "Getting recommendations for you..."
5. Calls tool
6. Shares results naturally

### Tool 2: analyze_plant_disease
**When triggered:** User describes plant symptoms  
**Required parameters:**
- `image_base64` (str) - Base64-encoded image or placeholder
- `description` (str) - User's description of symptoms

**Returns:**
```json
{
  "status": "success",
  "disease": "Early Blight",
  "confidence": 87.5,
  "analysis": "Early blight is a fungal disease affecting tomato plants...",
  "user_description": "Yellow spots on leaves"
}
```

**Agent behavior:**
1. Listens to symptom description
2. Offers to analyze image if available
3. Says: "Analyzing your plant..."
4. Calls tool
5. Shares diagnosis and treatment options

### Tool 3: get_general_advice
**When triggered:** User asks open-ended agricultural questions  
**Required parameters:**
- `topic` (str) - "irrigation", "pest control", "soil management", etc.

**Returns:**
```json
{
  "status": "success",
  "topic": "irrigation",
  "advice": "Best practices for efficient irrigation in Indian climate..."
}
```

**Agent behavior:**
1. Receives question
2. Identifies topic from context
3. Calls tool if needed
4. Shares advice naturally

## Code Structure

### voice_agent.py Components

#### GrowMateBackendClient
Static methods for async backend operations:
- `analyze_disease_from_image()` - Uses TensorFlow model + Gemini
- `get_farm_recommendations()` - Queries Gemini for advice
- Error handling with try-catch

#### GrowMateVoiceAgent(Agent)
Main agent class extending LiveKit Agent:

**Methods:**
- `__init__()` - Sets system instructions and configuration
- `set_session()` - Stores session reference for async operations
- `_safe_speak()` - Injects text into LLM for spoken response
- `delay_speech_handler()` - Monitors tasks and speaks at intervals
- `get_farm_recommendations()` - Tool function
- `analyze_plant_disease()` - Tool function
- `get_general_advice()` - Tool function

**Tool Decorators:**
```python
@function_tool()
async def my_tool(self, context: RunContext, param1: str) -> str:
    """
    Tool description for LLM.
    
    Args:
        context: RunContext with room, agent metadata
        param1: Parameter extracted from conversation
    
    Returns:
        JSON string with results
    """
```

#### entrypoint()
LiveKit entry point function:
1. Creates agent instance
2. Creates AgentSession with Google Realtime API
3. Starts session with room and agent
4. Sends initial prompt
5. Handles exceptions

## Performance Optimization

### 1. Reduce Latency
```python
# Preload models on startup
model = load_model('plant_model_v5-beta.h5')

# Cache Gemini responses
response_cache = {}
```

### 2. Parallel Tool Invocation
```python
# If user provides all info at once:
tasks = [
  asyncio.create_task(get_recommendations()),
  asyncio.create_task(analyze_image())
]
results = await asyncio.gather(*tasks)
```

### 3. Temperature Tuning
```python
# Lower temp (0.3) for transactional accuracy
# Higher temp (0.7) for natural conversation
llm=google.beta.realtime.RealtimeModel(temperature=0.4)
```

## Debugging

### View Agent Logs
Check the terminal where you ran `python voice_agent.py`:
```
INFO growmate-voice-agent: Tool: analyze_plant_disease - Yellow spots on leaves
INFO growmate-voice-agent: Analyzing your plant...
INFO growmate-voice-agent: Agent actively speaking: Analyzing complete...
```

### View Room State
Use browser console (F12) in `/voicebot`:
```javascript
// Check room connection
console.log("Room:", room.name);
console.log("Participants:", room.numParticipants);
console.log("Local tracks:", room.localParticipant?.videoTracks);
console.log("Remote:", room.participants);
```

### Test via Backend Debug Endpoint
```bash
curl "http://localhost:5000/livekit-room-debug?room=voicebot-uid-abc123"

# Response:
{
  "participant_count": 2,
  "participants": [
    {"name": "User", "tracks": [{"type": "audio"}]},
    {"name": "Growmate Voice Bot", "tracks": [{"type": "audio"}]}
  ]
}
```

### Check Firestore Sessions
Navigate to Firebase Console → voice_sessions collection:
```json
{
  "room_id": "voicebot-uid-abc123",
  "name": "Farmer Name",
  "language": "ta",
  "status": "active",
  "timestamp": "2026-04-01T12:00:00Z"
}
```

## Deployment

### Production Checklist

- [ ] Environment variables loaded from secure vault (not .env)
- [ ] API keys rotated regularly
- [ ] Logging level set to INFO (not DEBUG)
- [ ] Error messages don't expose internal details
- [ ] Patient IDs anonymized in logs
- [ ] Database connections pooled
- [ ] Health check endpoints added
- [ ] Graceful shutdown on SIGTERM
- [ ] Process monitoring (systemd/PM2)
- [ ] Load balancing (multiple agent workers)

### Horizontal Scaling
```bash
# Start multiple agent workers
PORT=8081 python voice_agent.py &
PORT=8082 python voice_agent.py &
PORT=8083 python voice_agent.py &

# Load balancer distributes dispatch calls across workers
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8081
CMD ["python", "voice_agent.py"]
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Port 8081 already in use" | Another process using it | `lsof -i :8081` and kill it |
| Agent not joining room | Dispatch failed | Check Flask logs for dispatch errors |
| No audio from agent | Google API not configured | Verify `GEMINI_API_KEY` in .env |
| User can't hear responses | Browser autoplay policy | Click "Enable Audio" button in UI |
| Long operations timeout | Network slow | Increase timeout in `delay_speech_handler` |
| Disease detection fails | Model not loaded | Check `plant_model_v5-beta.h5` exists |
| Recommendations generic | Prompt too vague | Edit system instructions in `GrowMateVoiceAgent.__init__()` |

## Advanced Customization

### Change System Prompt
Edit `GrowMateVoiceAgent.__init__()`:
```python
instructions = (
    "You are CustomBot, specialized in {your domain}.\n"
    "Your primary goal is: {your goal}.\n"
    # ... more rules
)
```

### Add New Tool
```python
@function_tool()
async def my_new_tool(self, context: RunContext, param: str) -> str:
    """Tool description for LLM."""
    # Implementation
    return json.dumps({"result": "..."})
```

### Change Voice Model
```python
# Current: Google Realtime API
llm=google.beta.realtime.RealtimeModel()

# Alternative: Other Google models
llm=google.fal.RealtimeModel()
```

### Modify Delay Intervals
```python
intervals = [
    (2, "Fast feedback"),
    (5, "Medium feedback"),
    (10, "Late feedback"),
]
```

## API Integration

### Frontend Calls Backend
```javascript
// request to /livekit-token
const response = await fetch('/livekit-token', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    name: "Farmer Name",
    language: "en",
    farm_location: "Tamil Nadu"
  })
});

const data = await response.json();
console.log("Room:", data.room);
console.log("Agent dispatched:", data.agent_dispatched);
```

### Agent Tools Access Room Context
```python
@function_tool()
async def my_tool(self, context: RunContext) -> str:
    room = context.room  # LiveKit Room object
    participants = room.participants  # All participants
    metadata = context.agent.metadata  # Custom metadata
    return json.dumps({"participants": len(participants)})
```

## Support & Resources

- **LiveKit Docs**: https://docs.livekit.io/agents/
- **Google Realtime API**: https://ai.google.dev/docs/
- **Firebase Docs**: https://firebase.google.com/docs
- **GitHub Issues**: Check GrowMate repo for known issues
- **Community**: LiveKit Slack community for peer support

---

**Last Updated**: 2026-04-01  
**Version**: 1.0.0  
**Status**: Production Ready ✅
