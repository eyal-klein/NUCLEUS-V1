"""NUCLEUS V2.0 - SQLAlchemy Models"""

from .base import Base, get_db, init_db, engine, SessionLocal
from .dna import Entity, Interest, Goal, Value, RawData, DailyReadiness, EnergyPattern, SchedulingPreferences
from .dna_extended import (
    PersonalityTrait, CommunicationStyle, DecisionPattern, WorkHabit,
    Relationship, Skill, Preference, Constraint, Belief, Experience,
    Emotion, Routine, Context, EvolutionHistory
)
from .memory import (
    Conversation, Summary, Embedding, 
    MemoryTier1, MemoryTier2, MemoryTier3, MemoryTier4, 
    HealthMetric, CalendarEvent, EmailMessage, Briefing
)
from .assembly import Agent, Tool, AgentTool, AgentPerformance, AgentNeed, AgentLifecycleEvent
from .execution import Task, Job, Log
from .integrations import EntityIntegration
from .nucleus_core import (
    # Proactive Engagement
    ProactiveTrigger, ProactiveInitiative,
    # Interest Discovery
    InterestSignal, InterestCandidate,
    # Self-Evolution
    EvolutionFeedback, EvolutionCycle,
    # Autonomy Management
    AutonomyLevel, AutonomyTransition,
    # Core Principles
    CorePrinciple, PrincipleViolation,
    # Behavior Monitoring
    BehaviorLog, BehaviorDrift,
    # Domain Management
    Domain, DomainKnowledge,
    # Relationship Building
    PrivateLanguage,
    # Agent Testbed
    TestScenario, TestResult,
    # Wellbeing Guardian
    WellbeingCheck,
)

__all__ = [
    # Base
    "Base",
    "get_db",
    "init_db",
    "engine",
    "SessionLocal",
    # DNA - Core
    "Entity",
    "Interest",
    "Goal",
    "Value",
    "RawData",
    "DailyReadiness",
    "EnergyPattern",
    "SchedulingPreferences",
    # DNA - Extended (V2.0)
    "PersonalityTrait",
    "CommunicationStyle",
    "DecisionPattern",
    "WorkHabit",
    "Relationship",
    "Skill",
    "Preference",
    "Constraint",
    "Belief",
    "Experience",
    "Emotion",
    "Routine",
    "Context",
    "EvolutionHistory",
    # Memory
    "Conversation",
    "Summary",
    "Embedding",
    "MemoryTier1",
    "MemoryTier2",
    "MemoryTier3",
    "MemoryTier4",
    "HealthMetric",
    "CalendarEvent",
    "EmailMessage",
    "Briefing",
    # Assembly
    "Agent",
    "Tool",
    "AgentTool",
    "AgentPerformance",
    "AgentNeed",
    "AgentLifecycleEvent",
    # Execution
    "Task",
    "Job",
    "Log",
    # Integrations
    "EntityIntegration",
    # Nucleus Core - Proactive Engagement
    "ProactiveTrigger",
    "ProactiveInitiative",
    # Nucleus Core - Interest Discovery
    "InterestSignal",
    "InterestCandidate",
    # Nucleus Core - Self-Evolution
    "EvolutionFeedback",
    "EvolutionCycle",
    # Nucleus Core - Autonomy Management
    "AutonomyLevel",
    "AutonomyTransition",
    # Nucleus Core - Core Principles
    "CorePrinciple",
    "PrincipleViolation",
    # Nucleus Core - Behavior Monitoring
    "BehaviorLog",
    "BehaviorDrift",
    # Nucleus Core - Domain Management
    "Domain",
    "DomainKnowledge",
    # Nucleus Core - Relationship Building
    "PrivateLanguage",
    # Nucleus Core - Agent Testbed
    "TestScenario",
    "TestResult",
    # Nucleus Core - Wellbeing Guardian
    "WellbeingCheck",
]
