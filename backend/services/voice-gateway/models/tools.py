"""
NUCLEUS Voice Gateway - Tool Definitions

Defines the tools available to the xAI voice agent.
These tools map to NUCLEUS capabilities.
"""

from typing import Any, Dict, List


# =============================================================================
# Built-in xAI Tools
# =============================================================================

WEB_SEARCH_TOOL = {
    "type": "web_search"
}

X_SEARCH_TOOL = {
    "type": "x_search"
}


# =============================================================================
# NUCLEUS Custom Tools
# =============================================================================

GET_CALENDAR_EVENTS_TOOL = {
    "type": "function",
    "name": "get_calendar_events",
    "description": "קבל את האירועים הקרובים ביומן של המשתמש. Get the user's upcoming calendar events.",
    "parameters": {
        "type": "object",
        "properties": {
            "days_ahead": {
                "type": "integer",
                "description": "Number of days ahead to look for events",
                "default": 7
            },
            "include_details": {
                "type": "boolean",
                "description": "Whether to include full event details",
                "default": True
            }
        }
    }
}

CREATE_CALENDAR_EVENT_TOOL = {
    "type": "function",
    "name": "create_calendar_event",
    "description": "צור אירוע חדש ביומן של המשתמש. Create a new calendar event for the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Event title"
            },
            "start_time": {
                "type": "string",
                "format": "date-time",
                "description": "Event start time in ISO format"
            },
            "end_time": {
                "type": "string",
                "format": "date-time",
                "description": "Event end time in ISO format"
            },
            "description": {
                "type": "string",
                "description": "Event description"
            },
            "location": {
                "type": "string",
                "description": "Event location"
            },
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of attendee email addresses"
            }
        },
        "required": ["title", "start_time"]
    }
}

GET_RECENT_EMAILS_TOOL = {
    "type": "function",
    "name": "get_recent_emails",
    "description": "קבל את המיילים האחרונים של המשתמש. Get the user's recent emails.",
    "parameters": {
        "type": "object",
        "properties": {
            "count": {
                "type": "integer",
                "description": "Number of emails to retrieve",
                "default": 10
            },
            "unread_only": {
                "type": "boolean",
                "description": "Only retrieve unread emails",
                "default": False
            },
            "from_address": {
                "type": "string",
                "description": "Filter by sender email address"
            }
        }
    }
}

SEND_EMAIL_TOOL = {
    "type": "function",
    "name": "send_email",
    "description": "שלח מייל בשם המשתמש. Send an email on behalf of the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address"
            },
            "subject": {
                "type": "string",
                "description": "Email subject"
            },
            "body": {
                "type": "string",
                "description": "Email body content"
            },
            "cc": {
                "type": "array",
                "items": {"type": "string"},
                "description": "CC recipients"
            }
        },
        "required": ["to", "subject", "body"]
    }
}

GET_MEMORY_CONTEXT_TOOL = {
    "type": "function",
    "name": "get_memory_context",
    "description": "חפש מידע רלוונטי בזיכרון של המשתמש. Retrieve relevant context from the user's memory.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for memory retrieval"
            },
            "time_range_days": {
                "type": "integer",
                "description": "How many days back to search",
                "default": 30
            },
            "memory_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["conversation", "event", "task", "decision"]
                },
                "description": "Types of memories to search"
            }
        },
        "required": ["query"]
    }
}

CREATE_TASK_TOOL = {
    "type": "function",
    "name": "create_task",
    "description": "צור משימה או תזכורת למשתמש. Create a task or reminder for the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Task title"
            },
            "description": {
                "type": "string",
                "description": "Task description"
            },
            "due_date": {
                "type": "string",
                "format": "date-time",
                "description": "Task due date"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"],
                "description": "Task priority level"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Task tags for categorization"
            }
        },
        "required": ["title"]
    }
}

GET_CONTACTS_TOOL = {
    "type": "function",
    "name": "get_contacts",
    "description": "חפש אנשי קשר של המשתמש. Search the user's contacts.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (name, email, company)"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 5
            }
        },
        "required": ["query"]
    }
}

GET_USER_PREFERENCES_TOOL = {
    "type": "function",
    "name": "get_user_preferences",
    "description": "קבל את ההעדפות של המשתמש לנושא מסוים. Get user preferences for a specific topic.",
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Preference category (e.g., 'communication', 'scheduling', 'work')"
            }
        },
        "required": ["category"]
    }
}


# =============================================================================
# Tool Collections
# =============================================================================

def get_all_tools(
    include_web_search: bool = True,
    include_x_search: bool = True,
    include_calendar: bool = True,
    include_email: bool = True,
    include_memory: bool = True,
    include_tasks: bool = True,
    include_contacts: bool = True,
) -> List[Dict[str, Any]]:
    """
    Get the list of tools to enable for a voice session.
    
    Args:
        include_web_search: Enable web search
        include_x_search: Enable X (Twitter) search
        include_calendar: Enable calendar tools
        include_email: Enable email tools
        include_memory: Enable memory search
        include_tasks: Enable task creation
        include_contacts: Enable contact search
    
    Returns:
        List of tool definitions for xAI session configuration
    """
    tools = []
    
    # Built-in xAI tools
    if include_web_search:
        tools.append(WEB_SEARCH_TOOL)
    if include_x_search:
        tools.append(X_SEARCH_TOOL)
    
    # NUCLEUS custom tools
    if include_calendar:
        tools.append(GET_CALENDAR_EVENTS_TOOL)
        tools.append(CREATE_CALENDAR_EVENT_TOOL)
    
    if include_email:
        tools.append(GET_RECENT_EMAILS_TOOL)
        tools.append(SEND_EMAIL_TOOL)
    
    if include_memory:
        tools.append(GET_MEMORY_CONTEXT_TOOL)
        tools.append(GET_USER_PREFERENCES_TOOL)
    
    if include_tasks:
        tools.append(CREATE_TASK_TOOL)
    
    if include_contacts:
        tools.append(GET_CONTACTS_TOOL)
    
    return tools


def get_minimal_tools() -> List[Dict[str, Any]]:
    """Get minimal tool set for basic conversations."""
    return [
        WEB_SEARCH_TOOL,
        GET_CALENDAR_EVENTS_TOOL,
        GET_MEMORY_CONTEXT_TOOL,
    ]


def get_full_tools() -> List[Dict[str, Any]]:
    """Get full tool set for complete NUCLEUS functionality."""
    return get_all_tools()
