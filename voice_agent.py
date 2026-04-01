"""
GrowMate Voice Agent Worker
Runs as a LiveKit agent to provide bilingual voice support for:
- Plant disease detection
- Farming recommendations
- Farm management queries
"""

import os
import sys
import asyncio
import json
import logging
import base64
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, function_tool, RunContext
from livekit.plugins import google

try:
    from livekit.plugins import noise_cancellation
except ImportError:
    noise_cancellation = None

# Import GrowMate modules
from disease_detection import analyze_plant_disease, get_gemini_analysis, fetch_gemini_response

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)

# The Google realtime plugin expects GOOGLE_API_KEY.
# Reuse GEMINI_API_KEY when GOOGLE_API_KEY is not explicitly set.
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("growmate-voice-agent")


# ============================================================================
# BACKEND CLIENT
# ============================================================================
class GrowMateBackendClient:
    """Handles async calls to GrowMate backend services."""
    
    @staticmethod
    async def get_farm_recommendations(farm_size: str, crop_type: str, region: str) -> dict:
        """Get farming recommendations based on farm parameters."""
        prompt = (
            f"Provide farming recommendations for:\n"
            f"- Farm Size: {farm_size}\n"
            f"- Crop Type: {crop_type}\n"
            f"- Region: {region}\n\n"
            f"Include: best practices, seasonal tips, water management, and soil care."
        )
        
        try:
            logger.info(f"Fetching recommendations for {crop_type}...")
            response = fetch_gemini_response(prompt)
            return {"status": "success", "recommendations": response}
        except Exception as e:
            logger.error(f"Backend recommendations error: {str(e)}")
            return {"status": "error", "message": "Could not fetch recommendations"}
    
    @staticmethod
    async def analyze_disease_from_image(image_base64: str) -> dict:
        """Analyze plant disease from base64 image."""
        temp_path = None
        try:
            # Decode and save temporarily
            image_data = base64.b64decode(image_base64)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                temp_path = tmp.name
            with open(temp_path, "wb") as f:
                f.write(image_data)
            
            logger.info("Analyzing plant disease from image...")
            disease_result = analyze_plant_disease(temp_path)
            gemini_analysis = get_gemini_analysis(
                disease_result['prediction'], 
                disease_result['confidence']
            )
            
            # Clean up
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                "status": "success",
                "disease": disease_result['prediction'],
                "confidence": round(disease_result['confidence'], 2),
                "analysis": gemini_analysis
            }
        except Exception as e:
            logger.error(f"Disease analysis error: {str(e)}")
            return {"status": "error", "message": "Could not analyze image"}
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


# ============================================================================
# GROWMATE VOICE AGENT
# ============================================================================
class GrowMateVoiceAgent(Agent):
    def __init__(self):
        instructions = (
            "You are GrowMate, an AI Agricultural Voice Assistant.\n"
            "You help farmers with:\n"
            "1. Plant disease detection and analysis\n"
            "2. Farming recommendations\n"
            "3. Agricultural best practices\n"
            "You operate bilingually in English and Tamil.\n\n"
            "-----------------------------------\n"
            "INTERACTION RULES\n"
            "-----------------------------------\n"
            "1. If language is already provided in session metadata, do NOT ask language again.\n"
            "2. If language is unknown, first ask which language they prefer (English or Tamil).\n"
            "3. If user's name is already known, greet by name once and continue directly.\n"
            "2. Be polite, clear, and concise.\n"
            "3. Ask one question at a time.\n"
            "4. Listen for the user's needs:\n"
            "   - Disease detection? → Guide image upload if possible\n"
            "   - Farm recommendations? → Ask farm details (size, crop, region)\n"
            "   - General advice? → Provide relevant tips\n\n"
            "-----------------------------------\n"
            "DISEASE DETECTION FLOW\n"
            "-----------------------------------\n"
            "If user mentions plant disease or damage:\n"
            "1. Say: 'I can help analyze your plant. Can you describe the symptoms?'\n"
            "2. Listen to their description.\n"
            "3. Provide initial guidance.\n"
            "4. If possible, offer to analyze an image.\n"
            "5. Trigger analyze_disease_from_image tool if you receive image data.\n\n"
            "-----------------------------------\n"
            "RECOMMENDATIONS FLOW\n"
            "-----------------------------------\n"
            "If user asks for farming recommendations:\n"
            "1. Ask: 'What crop are you growing?'\n"
            "2. Ask: 'What is your farm size?'\n"
            "3. Ask: 'What region are you in?'\n"
            "4. Say: 'Getting recommendations for you. Please wait.'\n"
            "5. Trigger get_farm_recommendations tool.\n"
            "6. Share the recommendations naturally.\n\n"
            "-----------------------------------\n"
            "LANGUAGE SUPPORT\n"
            "-----------------------------------\n"
            "If English selected:\n"
            "- Respond in English only\n\n"
            "If Tamil selected:\n"
            "- Respond in Tamil only\n"
            "- Use Tamil script consistently\n\n"
            "-----------------------------------\n"
            "ERROR HANDLING\n"
            "-----------------------------------\n"
            "If image analysis fails:\n"
            "'There was an issue analyzing the image. Please try again.'\n\n"
            "If recommendations fail:\n"
            "'I could not fetch recommendations right now. Please try again shortly.'\n\n"
            "If user is silent for > 5 seconds:\n"
            "'Are you still there? How can I help with your farm?'\n\n"
            "-----------------------------------\n"
            "FINAL SUCCESS RESPONSE\n"
            "-----------------------------------\n"
            "After helping with analysis or recommendations:\n"
            "Say: 'Is there anything else I can help you with?'\n"
            "Listen for follow-up or offer to end the call politely.\n\n"
            "-----------------------------------\n"
            "STRICT RULES\n"
            "-----------------------------------\n"
            "- Never speak JSON out loud\n"
            "- Never expose technical details\n"
            "- Always prioritize the user's language choice\n"
            "- Be encouraging and supportive\n"
        )
        super().__init__(instructions=instructions)
        self.active_session = None
        self.user_language = None
        self.user_memory = {
            "name": "",
            "language": "",
            "farm_location": "",
            "recent_topics": [],
        }

    def set_session(self, session: AgentSession):
        self.active_session = session

    def set_user_profile(self, profile: dict):
        if not isinstance(profile, dict):
            return
        self.user_memory["name"] = str(profile.get("name") or "").strip()
        self.user_memory["language"] = str(profile.get("language") or "").strip().lower()
        self.user_memory["farm_location"] = str(profile.get("farm_location") or "").strip()
        self.user_language = self.user_memory["language"] or None

    def remember_topic(self, topic: str):
        topic = (topic or "").strip()
        if not topic:
            return
        topics = self.user_memory["recent_topics"]
        if topic in topics:
            topics.remove(topic)
        topics.append(topic)
        # Keep a small rolling memory for the current call.
        self.user_memory["recent_topics"] = topics[-6:]

    async def _safe_speak(self, text: str):
        """Safely inject speech into the session during async waits."""
        if self.active_session:
            try:
                self.active_session.chat_ctx.append(text=text, role="user")
                await self.active_session.update_chat_ctx(self.active_session.chat_ctx)
                self.active_session.generate_reply()
                logger.info(f"Agent actively speaking: {text}")
            except Exception as e:
                logger.error(f"Error in safe_speak: {e}")

    async def delay_speech_handler(self, task: asyncio.Task, operation: str = "processing"):
        """Monitors a task and triggers speech at specific intervals."""
        intervals = [
            (3, f"We are {operation}. Thank you for your patience."),
            (8, f"Still {operation}. This may take a moment."),
            (15, f"Almost done {operation}. Thank you for waiting.")
        ]
        
        start_time = datetime.now()
        
        try:
            for seconds, text in intervals:
                elapsed = (datetime.now() - start_time).total_seconds()
                wait_time = seconds - elapsed
                
                if wait_time > 0:
                    done, _ = await asyncio.wait([task], timeout=wait_time)
                    if task in done:
                        return
                
                if not task.done():
                    await self._safe_speak(text)
                    
            await task
        except Exception as e:
            logger.error(f"Error in delay_speech_handler: {e}")

    @function_tool()
    async def get_farm_recommendations(self, context: RunContext, crop_type: str, farm_size: str, region: str) -> str:
        """Get personalized farming recommendations.
        
        Args:
            crop_type: Type of crop (e.g., rice, wheat, tomato)
            farm_size: Size of farm (e.g., 1 acre, 5 hectares)
            region: Geographic region (e.g., Maharashtra, Tamil Nadu)
        
        Returns:
            JSON string with recommendations
        """
        logger.info(f"Tool: get_farm_recommendations for {crop_type} in {region}")
        self.remember_topic(f"recommendations:{crop_type}")
        
        task = asyncio.create_task(
            GrowMateBackendClient.get_farm_recommendations(farm_size, crop_type, region)
        )
        await self.delay_speech_handler(task, f"getting recommendations for {crop_type}")
        
        try:
            result = await task
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Recommendations tool error: {str(e)}")
            return json.dumps({"status": "error", "message": "Failed to get recommendations"})

    @function_tool()
    async def analyze_plant_disease(self, context: RunContext, image_base64: str, description: str) -> str:
        """Analyze plant disease from image and description.
        
        Args:
            image_base64: Image encoded in base64 format
            description: User's description of the symptoms
        
        Returns:
            JSON string with disease analysis and recommendations
        """
        logger.info(f"Tool: analyze_plant_disease - {description}")
        self.remember_topic(f"disease:{description[:80]}")
        
        task = asyncio.create_task(
            GrowMateBackendClient.analyze_disease_from_image(image_base64)
        )
        await self.delay_speech_handler(task, "analyzing your plant")
        
        try:
            result = await task
            if result["status"] == "success":
                # Add user's description to context
                result["user_description"] = description
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Disease analysis tool error: {str(e)}")
            return json.dumps({"status": "error", "message": "Could not analyze the image"})

    @function_tool()
    async def get_general_advice(self, context: RunContext, topic: str) -> str:
        """Get general agricultural advice on a topic.
        
        Args:
            topic: Agricultural topic (e.g., irrigation, pest control, soil management)
        
        Returns:
            JSON string with advice
        """
        logger.info(f"Tool: get_general_advice - {topic}")
        self.remember_topic(f"advice:{topic}")
        
        prompt = (
            f"Provide practical agricultural advice on: {topic}\n"
            f"Include: best practices, common mistakes to avoid, and seasonal tips.\n"
            f"Keep the response concise and actionable."
        )
        
        try:
            response = fetch_gemini_response(prompt)
            return json.dumps({
                "status": "success",
                "topic": topic,
                "advice": response
            })
        except Exception as e:
            logger.error(f"General advice error: {str(e)}")
            return json.dumps({"status": "error", "message": "Could not fetch advice"})


# ============================================================================
# ENTRY POINT
# ============================================================================
async def entrypoint(job_ctx: agents.JobContext):
    """Main entrypoint for the GrowMate voice agent."""

    dispatch_metadata = {}
    try:
        raw_metadata = None

        # LiveKit 1.5.x carries dispatch metadata in JobContext._info.accept_arguments.metadata.
        info_obj = getattr(job_ctx, "_info", None)
        accept_args = getattr(info_obj, "accept_arguments", None) if info_obj is not None else None
        if accept_args is not None:
            raw_metadata = getattr(accept_args, "metadata", None)

        # Keep compatibility with older/newer variants.
        if raw_metadata is None and getattr(job_ctx, "job", None) is not None:
            raw_metadata = getattr(job_ctx.job, "metadata", None)
        if raw_metadata is None:
            raw_metadata = getattr(job_ctx, "metadata", None)

        if isinstance(raw_metadata, bytes):
            raw_metadata = raw_metadata.decode("utf-8", errors="ignore")

        if isinstance(raw_metadata, str) and raw_metadata.strip():
            dispatch_metadata = json.loads(raw_metadata)
        elif isinstance(raw_metadata, dict):
            dispatch_metadata = raw_metadata
    except Exception as metadata_error:
        logger.warning("Could not parse dispatch metadata: %s", metadata_error)

    logger.info("Dispatch metadata resolved: %s", dispatch_metadata)
    
    agent_logic = GrowMateVoiceAgent()
    agent_logic.set_user_profile(dispatch_metadata)
    google_api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    if not google_api_key:
        raise ValueError("Missing GOOGLE_API_KEY/GEMINI_API_KEY for realtime voice model")
    
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            api_key=google_api_key,
            voice=None,
            temperature=0.4,  # Slightly higher for natural conversation
            instructions=agent_logic.instructions,
        ),
    )
    
    agent_logic.set_session(session)
    
    try:
        room_input_options = RoomInputOptions()
        if noise_cancellation is not None:
            room_input_options = RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            )

        await session.start(
            room=job_ctx.room,
            agent=agent_logic,
            room_input_options=room_input_options,
        )

        user_name = agent_logic.user_memory.get("name", "")
        user_language = agent_logic.user_memory.get("language", "")
        farm_location = agent_logic.user_memory.get("farm_location", "")

        memory_context = (
            "Session memory:\n"
            f"- name: {user_name or 'unknown'}\n"
            f"- language: {user_language or 'unknown'}\n"
            f"- farm_location: {farm_location or 'unknown'}\n"
            "Behavior rules:\n"
            "- Do not repeat onboarding questions already answered.\n"
            "- If language is known, start directly in that language.\n"
            "- Greet the user once at start and move to help intent."
        )

        if user_language in {"en", "ta", "hi", "bn", "es", "fr", "pt"}:
            if user_language == "ta":
                initial_prompt = (
                    "The user has connected and onboarding is already completed.\n"
                    f"Speak in Tamil. Greet {user_name or 'the user'} once politely and ask how you can help with farming today.\n"
                    "Do not ask language preference again."
                )
            else:
                initial_prompt = (
                    "The user has connected and onboarding is already completed.\n"
                    f"Speak in {user_language}. Greet {user_name or 'the user'} once politely and ask how you can help with farming today.\n"
                    "Do not ask language preference again."
                )
        else:
            initial_prompt = (
                "The user has connected to GrowMate. Onboarding may already be complete in the app. "
                "Do not ask language preference again. "
                "Give a short bilingual greeting (English + Tamil) and immediately ask how you can help with farming today."
            )
        
        session.chat_ctx.append(text=memory_context, role="system")
        session.chat_ctx.append(text=initial_prompt, role="user")
        await session.update_chat_ctx(session.chat_ctx)
        session.generate_reply()
        
    except Exception as e:
        logger.error(f"Session error: {e}")


if __name__ == "__main__":
    logger.info("🌾 Starting GrowMate Voice Agent...")
    if len(sys.argv) == 1:
        sys.argv.append("start")

    # Use an ephemeral port by default to avoid local bind collisions on Windows.
    # Override with LIVEKIT_WORKER_PORT or PORT if you need a fixed value.
    worker_port = os.environ.get("LIVEKIT_WORKER_PORT") or os.environ.get("PORT") or "0"
    port = int(worker_port)
    livekit_url = os.environ.get("LIVEKIT_URL", "").strip()
    livekit_api_key = os.environ.get("LIVEKIT_API_KEY", "").strip()
    livekit_api_secret = os.environ.get("LIVEKIT_API_SECRET", "").strip()
    agent_name = os.environ.get("LIVEKIT_AGENT_NAME", "Growmate Voice Bot").strip()

    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        port=port,
        agent_name=agent_name,
        ws_url=livekit_url,
        api_key=livekit_api_key,
        api_secret=livekit_api_secret,
    ))
    logger.info("🌾 GrowMate Voice Agent finished.")
