"""NUCLEUS V1.2 - SQLAlchemy Models"""

from .base import Base, get_db, init_db, engine, SessionLocal
from .dna import Entity, Interest, Goal, Value, RawData
from .memory import Conversation, Summary, Embedding
from .assembly import Agent, Tool, AgentTool, AgentPerformance
from .execution import Task, Job, Log
from .integrations import EntityIntegration

__all__ = [
    # Base
    "Base",
    "get_db",
    "init_db",
    "engine",
    "SessionLocal",
    # DNA
    "Entity",
    "Interest",
    "Goal",
    "Value",
    "RawData",
    # Memory
    "Conversation",
    "Summary",
    "Embedding",
    # Assembly
    "Agent",
    "Tool",
    "AgentTool",
    "AgentPerformance",
    # Execution
    "Task",
    "Job",
    "Log",
    # Integrations
    "EntityIntegration",
]
