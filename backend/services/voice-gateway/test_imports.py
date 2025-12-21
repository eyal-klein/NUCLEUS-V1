"""Test that all voice-gateway modules can be imported correctly."""

import sys
sys.path.insert(0, '.')

print("Testing imports...")

try:
    from config import get_settings, Settings, HEBREW_INSTRUCTION, FOUR_OPTIONS_PROTOCOL
    print("✅ config.py")
except Exception as e:
    print(f"❌ config.py: {e}")

try:
    from models.events import (
        SessionState, MessageRole, ClientAudioEvent, ServerAudioEvent,
        ServerTranscriptEvent, ConversationLog, VoiceSessionEvent
    )
    print("✅ models/events.py")
except Exception as e:
    print(f"❌ models/events.py: {e}")

try:
    from models.session import EntityContext, VoiceSessionConfig, VoiceSession
    print("✅ models/session.py")
except Exception as e:
    print(f"❌ models/session.py: {e}")

try:
    from models.tools import get_all_tools, get_minimal_tools, get_full_tools, NUCLEUS_TOOLS
    tools = get_all_tools()
    print(f"✅ models/tools.py ({len(tools)} tools defined)")
except Exception as e:
    print(f"❌ models/tools.py: {e}")

try:
    from services.xai_bridge import XAIBridge
    print("✅ services/xai_bridge.py")
except Exception as e:
    print(f"❌ services/xai_bridge.py: {e}")

try:
    from services.nucleus_integration import NucleusIntegration
    print("✅ services/nucleus_integration.py")
except Exception as e:
    print(f"❌ services/nucleus_integration.py: {e}")

try:
    from services.session_manager import SessionManager
    print("✅ services/session_manager.py")
except Exception as e:
    print(f"❌ services/session_manager.py: {e}")

try:
    from handlers.rest import router
    print("✅ handlers/rest.py")
except Exception as e:
    print(f"❌ handlers/rest.py: {e}")

try:
    from handlers.tools import handle_tool_call
    print("✅ handlers/tools.py")
except Exception as e:
    print(f"❌ handlers/tools.py: {e}")

try:
    from handlers.websocket import handle_voice_connection
    print("✅ handlers/websocket.py")
except Exception as e:
    print(f"❌ handlers/websocket.py: {e}")

print("\n✅ All imports successful!")
