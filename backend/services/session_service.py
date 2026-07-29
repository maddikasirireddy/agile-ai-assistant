import time
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("agile_wellness")

# Global in-memory session stores
SESSIONS: Dict[str, Dict[str, Any]] = {}
FINGERPRINTS: Dict[str, str] = {}

SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes

def get_initial_state() -> Dict[str, Any]:
    return {
        "selected_product": None,
        "pending_intent": None,
        "clarification_candidates": [],
        "user_concern": None,
        "shopping_action": None,
        "last_bot_action": None,
        "last_user_action": None,
        "original_request": None,
        "last_activity": time.time()
    }

def get_session_state(session_id: str) -> Dict[str, Any]:
    """Retrieves or creates the conversation state for a session, checking for timeouts."""
    now = time.time()
    
    # Clean up expired sessions periodically
    expire_sessions()
    
    if session_id not in SESSIONS:
        logger.info(f"Session Service: Creating new session state for '{session_id}'")
        SESSIONS[session_id] = get_initial_state()
    else:
        session = SESSIONS[session_id]
        # Check timeout expiration
        if now - session["last_activity"] > SESSION_TIMEOUT_SECONDS:
            logger.info(f"Session Service: Expiring session '{session_id}' due to inactivity.")
            SESSIONS[session_id] = get_initial_state()
            
    SESSIONS[session_id]["last_activity"] = now
    return SESSIONS[session_id]

def update_session_state(session_id: str, updates: Dict[str, Any]):
    """Updates key-value pairs in the session state."""
    state = get_session_state(session_id)
    for k, v in updates.items():
        state[k] = v
    state["last_activity"] = time.time()

def reset_session(session_id: str):
    """Resets conversation memory state completely."""
    logger.info(f"Session Service: Resetting state memory for '{session_id}'")
    SESSIONS[session_id] = get_initial_state()

def expire_sessions():
    """Removes sessions that have exceeded the inactivity timeout threshold."""
    now = time.time()
    expired_ids = []
    for sid, state in SESSIONS.items():
        if now - state["last_activity"] > SESSION_TIMEOUT_SECONDS:
            expired_ids.append(sid)
            
    for sid in expired_ids:
        del SESSIONS[sid]
        
    # Also clean fingerprints mapping to deleted sessions
    expired_fingerprints = [fp for fp, sid in FINGERPRINTS.items() if sid in expired_ids]
    for fp in expired_fingerprints:
        del FINGERPRINTS[fp]
