"""
NUCLEUS Voice Gateway - Tool Execution Handler

Handles the execution of tools called by xAI during voice conversations.
"""

import json
import logging
from typing import Any, Dict
from uuid import UUID

from ..models.session import VoiceSession
from ..models.events import ServerToolCallEvent
from ..services.nucleus_integration import get_nucleus_integration
from ..services.xai_bridge import get_xai_bridge

logger = logging.getLogger(__name__)


async def handle_tool_call(
    session: VoiceSession,
    call_id: str,
    tool_name: str,
    arguments: str,
):
    """
    Handle a tool call from xAI.
    
    This function:
    1. Notifies the client that a tool is being executed
    2. Executes the tool via NUCLEUS services
    3. Sends the result back to xAI
    4. Notifies the client of completion
    
    Args:
        session: The voice session
        call_id: The tool call ID from xAI
        tool_name: Name of the tool to execute
        arguments: JSON string of tool arguments
    """
    xai_bridge = get_xai_bridge()
    nucleus = get_nucleus_integration()
    
    logger.info(f"Session {session.session_id}: Executing tool {tool_name}")
    
    # Notify client
    await session.send_to_client(ServerToolCallEvent(
        name=tool_name,
        status="executing"
    ))
    
    try:
        # Parse arguments
        args = json.loads(arguments) if arguments else {}
        
        # Execute tool based on type
        if tool_name in ["web_search", "x_search"]:
            # Built-in xAI tools - no action needed, xAI handles them
            result = {"status": "handled_by_xai"}
        else:
            # NUCLEUS custom tools
            result = await nucleus.execute_tool(
                entity_id=session.entity_id,
                tool_name=tool_name,
                arguments=args,
            )
        
        # Send result back to xAI
        if session.xai_ws and tool_name not in ["web_search", "x_search"]:
            await xai_bridge.send_tool_result(
                session.xai_ws,
                call_id,
                json.dumps(result, ensure_ascii=False)
            )
        
        # Notify client of completion
        await session.send_to_client(ServerToolCallEvent(
            name=tool_name,
            status="completed",
            result=_summarize_result(result)
        ))
        
        # Increment tool call counter
        session.tool_calls_count += 1
        
        logger.info(f"Session {session.session_id}: Tool {tool_name} completed")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse tool arguments: {e}")
        await _handle_tool_error(session, call_id, tool_name, "Invalid arguments")
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        await _handle_tool_error(session, call_id, tool_name, str(e))


async def _handle_tool_error(
    session: VoiceSession,
    call_id: str,
    tool_name: str,
    error_message: str,
):
    """
    Handle a tool execution error.
    
    Args:
        session: The voice session
        call_id: The tool call ID
        tool_name: Name of the tool
        error_message: Error message
    """
    xai_bridge = get_xai_bridge()
    
    # Send error result to xAI
    if session.xai_ws:
        await xai_bridge.send_tool_result(
            session.xai_ws,
            call_id,
            json.dumps({"error": error_message})
        )
    
    # Notify client
    await session.send_to_client(ServerToolCallEvent(
        name=tool_name,
        status="failed",
        result=f"Error: {error_message}"
    ))


def _summarize_result(result: Dict[str, Any]) -> str:
    """
    Create a brief summary of a tool result for the client.
    
    Args:
        result: The tool result
    
    Returns:
        A brief summary string
    """
    if "error" in result:
        return f"Error: {result['error']}"
    
    if "events" in result:
        count = len(result["events"])
        return f"Found {count} events"
    
    if "emails" in result or "messages" in result:
        count = len(result.get("emails", result.get("messages", [])))
        return f"Found {count} emails"
    
    if "contacts" in result:
        count = len(result["contacts"])
        return f"Found {count} contacts"
    
    if "memories" in result:
        count = len(result["memories"])
        return f"Found {count} relevant memories"
    
    if "created" in result or "id" in result:
        return "Created successfully"
    
    if "sent" in result:
        return "Sent successfully"
    
    return "Completed"


# =============================================================================
# Tool-specific handlers (for complex tools that need special handling)
# =============================================================================

async def handle_calendar_event_creation(
    session: VoiceSession,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle calendar event creation with confirmation.
    
    For sensitive actions, we may want to confirm with the user first.
    This is an example of how to implement the 4 Options Protocol.
    
    Args:
        session: The voice session
        args: Event creation arguments
    
    Returns:
        Tool result
    """
    nucleus = get_nucleus_integration()
    
    # For now, execute directly
    # In the future, we could implement confirmation flow here
    return await nucleus.execute_tool(
        entity_id=session.entity_id,
        tool_name="create_calendar_event",
        arguments=args,
    )


async def handle_email_send(
    session: VoiceSession,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle email sending with confirmation.
    
    Sending emails is a sensitive action that should be confirmed.
    
    Args:
        session: The voice session
        args: Email arguments
    
    Returns:
        Tool result
    """
    nucleus = get_nucleus_integration()
    
    # For now, execute directly
    # In the future, we could implement confirmation flow here
    return await nucleus.execute_tool(
        entity_id=session.entity_id,
        tool_name="send_email",
        arguments=args,
    )
