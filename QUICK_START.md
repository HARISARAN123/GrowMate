# GrowMate Voice Agent - Quick Start Guide

Get the voice bot running in 3 minutes.

## Prerequisites

- Python 3.8+ installed
- Terminal/Command Prompt
- Internet connection
- GrowMate project downloaded

## Installation (One-time)

### Step 1: Install Dependencies
```bash
cd d:\GrowMate
pip install -r requirements.txt
```

**Expected output:** `Successfully installed livekit livekit-agents ...`

### Step 2: Validate Setup
```bash
python validate-setup.py
```

**Expected output:** `✓ All checks passed! Ready to run.`

If you see errors, check [Troubleshooting](#troubleshooting) below.

## Running (Every time)

### Quick Start (Windows)
```bash
d:\GrowMate\start-dev.bat
```

This opens two windows:
1. **GrowMate Backend** (Flask on port 5000)
2. **GrowMate Voice Agent** (Agent on port 8081)

### Then Open Browser
```
http://localhost:5000/voicebot
```

## Using the Voice Bot

1. **Fill the form:**
   - Name: Your name
   - Language: English or Tamil
   - Farm Location: Your region (optional)

2. **Click "Start Voice Call"**

3. **Wait for greeting:**
   - English: "Welcome to GrowMate. Which language do you prefer?"
   - Tamil: "ஐக்கியவாண்ட்க்கு வரவேற்கிறோம்"

4. **Start talking:**
   - "I have a sick tomato plant" → Agent offers disease detection
   - "What should I grow?" → Agent asks clarifying questions
   - "Tell me about irrigation" → Agent provides agricultural advice

5. **End call:** Say "goodbye" or close the browser tab

## What's Working

✅ **Voice Streaming** - Real-time audio to/from agent  
✅ **Bilingual** - English and Tamil language switching  
✅ **Disease Detection** - Analyze plant images and get treatment  
✅ **Recommendations** - AI-powered farming advice  
✅ **Delay Handling** - Progress updates for long operations  
✅ **Noise Cancellation** - Clean audio even in noisy environments  
✅ **Error Recovery** - Graceful failure handling  

## File Structure

```
d:\GrowMate\
├── app.py                           # Flask backend
├── voice_agent.py                   # ⭐ NEW: Voice agent worker
├── disease_detection.py             # ML analysis
├── firebase_service.py              # Database
├── templates/
│   └── voicebot.html                # Voice UI
├── static/                          # Assets
├── .env                             # Configuration
├── requirements.txt                 # Dependencies
├── start-dev.bat                    # ⭐ NEW: Quick launcher
├── start-dev.ps1                    # ⭐ NEW: PowerShell launcher
├── validate-setup.py                # ⭐ NEW: Setup validator
├── VOICE_AGENT_SETUP.md             # ⭐ NEW: Setup guide
├── VOICE_AGENT_README.md            # ⭐ NEW: Full documentation
└── plant_model_v5-beta.h5           # ML model
```

## Common Tasks

### Check if agent is running
```bash
# Windows (PowerShell)
Get-Process python | Where-Object {$_.CommandLine -like "*voice_agent*"}

# Windows (CMD)
tasklist | find "python"

# Linux/Mac
ps aux | grep voice_agent
```

### Stop the agent
Close the terminal window where it's running or:
```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
pkill -f voice_agent.py
```

### View logs in real-time
Watch the terminal windows directly. Logs appear as:
```
INFO growmate-voice-agent: Tool: analyze_plant_disease
INFO growmate-voice-agent: Analyzing complete...
```

### Test without UI
```bash
# You still need Flask backend running
python app.py

# Then in another terminal, request a token directly
curl -X POST http://localhost:5000/livekit-token \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","language":"en","farm_location":"Test"}'
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'livekit'"
**Solution:** Run `pip install -r requirements.txt`

### "Port 5000 already in use"
**Solution:** 
```bash
# Find what's using it
netstat -ano | findstr :5000

# Kill it
taskkill /PID <PID> /F

# Or use different port in Flask
python app.py --port 5001
```

### "Agent not joining room"
Check agent logs for errors. Common causes:
- LIVEKIT_AGENT_NAME not set in .env
- Network connectivity issue
- LiveKit server unreachable

**Verify:**
```bash
ping onpitch-3p5r1jyv.livekit.cloud
```

### "No audio from agent"
**Try:**
1. Click "Enable Audio" button in UI
2. Check browser speaker icon (not muted)
3. Check system volume
4. Verify microphone is working: click mic icon in UI

### "Disease detection fails"
**Check:**
1. `plant_model_v5-beta.h5` exists in project root
2. `class_indices.json` exists in project root
3. TensorFlow loaded: `python -c "import tensorflow; print(tensorflow.__version__)"`

### "Strange characters in Tamil output"
This is normal with terminal encoding. The agent is speaking correctly in-app.

## Performance Tips

**Reduce Latency:**
- Use Wi-Fi (not cellular)
- Close other bandwidth-heavy apps
- Use regional LiveKit server if possible

**Better Disease Detection:**
- Upload clear images with good lighting
- Get full view of the plant
- Multiple angles for better diagnosis

**Faster Recommendations:**
- Be specific: "rice farming" not "farming"
- Provide region: "Tamil Nadu" helps tailor advice
- Mention farm size: "1 acre" for specific guidance

## Next Steps

1. **Customize the agent:**
   - Edit system instructions in `voice_agent.py`
   - Add more tools for specific needs
   - Change voice/language preferences

2. **Add features:**
   - Weather forecast integration
   - Pest identification
   - Fertilizer calculator
   - Soil testing guide

3. **Deploy to production:**
   - See [VOICE_AGENT_SETUP.md](VOICE_AGENT_SETUP.md) for deployment options
   - Use Docker for easy scaling
   - Set up monitoring and alerts

## Documentation

- **Full Setup Guide:** [VOICE_AGENT_SETUP.md](VOICE_AGENT_SETUP.md)
- **Complete Reference:** [VOICE_AGENT_README.md](VOICE_AGENT_README.md)
- **API Docs:** https://docs.livekit.io/agents/
- **Google Realtime API:** https://ai.google.dev/docs/

## Need Help?

1. **Check setup:** `python validate-setup.py`
2. **Read full docs:** [VOICE_AGENT_SETUP.md](VOICE_AGENT_SETUP.md)
3. **Check logs:** Look at terminal output for error messages
4. **Browser console:** Press F12 in `/voicebot` and check console tab

---

**That's it!** Your GrowMate Voice Agent is ready. 🌾

Questions? Open an issue or check the documentation links above.
