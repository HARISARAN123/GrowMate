import logging
from typing import Any, Dict, List, Optional

from firebase_admin import firestore

logger = logging.getLogger(__name__)


def get_firestore_client():
    """Return a Firestore client instance."""
    return firestore.client()


def upsert_user_profile(uid: str, profile: Dict[str, Any]) -> None:
    """Create or update a user profile document in Firestore."""
    try:
        db = get_firestore_client()
        payload = dict(profile)
        payload["updated_at"] = firestore.SERVER_TIMESTAMP
        db.collection("users").document(uid).set(payload, merge=True)
    except Exception as exc:
        logger.error("Failed to upsert user profile for uid=%s: %s", uid, exc)


def save_disease_analysis(uid: str, data: Dict[str, Any]) -> None:
    """Store disease analysis history for a user."""
    try:
        db = get_firestore_client()
        payload = dict(data)
        payload["created_at"] = firestore.SERVER_TIMESTAMP
        db.collection("users").document(uid).collection("analysis_history").add(payload)
    except Exception as exc:
        logger.error("Failed to save disease analysis for uid=%s: %s", uid, exc)


def save_farm_recommendation(uid: str, data: Dict[str, Any]) -> None:
    """Store farm recommendation history for a user."""
    try:
        db = get_firestore_client()
        payload = dict(data)
        payload["created_at"] = firestore.SERVER_TIMESTAMP
        db.collection("users").document(uid).collection("farm_recommendations").add(payload)
    except Exception as exc:
        logger.error("Failed to save farm recommendation for uid=%s: %s", uid, exc)


def save_chat_message(uid: str, chat_session_id: str, role: str, text: str) -> None:
    """Store a chat message in a user-scoped chat session."""
    try:
        db = get_firestore_client()
        db.collection("users").document(uid).collection("chat_sessions").document(chat_session_id).set(
            {"updated_at": firestore.SERVER_TIMESTAMP}, merge=True
        )
        db.collection("users").document(uid).collection("chat_sessions").document(chat_session_id).collection(
            "messages"
        ).add(
            {
                "role": role,
                "text": text,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
    except Exception as exc:
        logger.error(
            "Failed to save chat message for uid=%s session=%s: %s",
            uid,
            chat_session_id,
            exc,
        )


def get_chat_messages(uid: str, chat_session_id: str, limit: int = 50) -> List[Dict[str, str]]:
    """Fetch chat history for a user/session in chronological order."""
    try:
        db = get_firestore_client()
        messages_ref = (
            db.collection("users")
            .document(uid)
            .collection("chat_sessions")
            .document(chat_session_id)
            .collection("messages")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        docs = list(messages_ref.stream())
        docs.reverse()

        history: List[Dict[str, str]] = []
        for doc in docs:
            payload = doc.to_dict() or {}
            role = payload.get("role", "bot")
            text = payload.get("text", "")
            history.append({"role": role, "text": text})
        return history
    except Exception as exc:
        logger.error(
            "Failed to fetch chat messages for uid=%s session=%s: %s",
            uid,
            chat_session_id,
            exc,
        )
        return []


def create_chat_session(uid: str, chat_session_id: str, meta: Optional[Dict[str, Any]] = None) -> None:
    """Ensure chat session metadata exists."""
    try:
        db = get_firestore_client()
        payload: Dict[str, Any] = {
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
        if meta:
            payload.update(meta)
        db.collection("users").document(uid).collection("chat_sessions").document(chat_session_id).set(
            payload, merge=True
        )
    except Exception as exc:
        logger.error("Failed to create chat session for uid=%s session=%s: %s", uid, chat_session_id, exc)
