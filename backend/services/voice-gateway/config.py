"""
NUCLEUS Voice Gateway - Configuration Module

Manages all configuration settings for the Voice Gateway service.
Follows NUCLEUS patterns for environment-based configuration.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Voice Gateway configuration settings."""
    
    # Service Identity
    service_name: str = "voice-gateway"
    service_version: str = "2.0.0"
    service_port: int = field(default_factory=lambda: int(os.getenv("PORT", "8090")))
    
    # xAI Configuration
    xai_api_key: str = field(default_factory=lambda: os.getenv("XAI_API_KEY", ""))
    xai_ws_url: str = field(default_factory=lambda: os.getenv("XAI_WS_URL", "wss://api.x.ai/v1/realtime"))
    xai_voice: str = field(default_factory=lambda: os.getenv("XAI_VOICE", "Sal"))
    xai_audio_format: str = field(default_factory=lambda: os.getenv("XAI_AUDIO_FORMAT", "audio/pcm"))
    xai_sample_rate: int = field(default_factory=lambda: int(os.getenv("XAI_SAMPLE_RATE", "24000")))
    
    # Turn Detection Settings
    vad_threshold: float = field(default_factory=lambda: float(os.getenv("VAD_THRESHOLD", "0.5")))
    vad_prefix_padding_ms: int = field(default_factory=lambda: int(os.getenv("VAD_PREFIX_PADDING_MS", "300")))
    vad_silence_duration_ms: int = field(default_factory=lambda: int(os.getenv("VAD_SILENCE_DURATION_MS", "200")))
    
    # NUCLEUS Services URLs
    memory_engine_url: str = field(default_factory=lambda: os.getenv("MEMORY_ENGINE_URL", "http://memory-engine:8080"))
    dna_engine_url: str = field(default_factory=lambda: os.getenv("DNA_ENGINE_URL", "http://dna-engine:8080"))
    orchestrator_url: str = field(default_factory=lambda: os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8080"))
    
    # Database
    database_url: Optional[str] = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    
    # Pub/Sub
    pubsub_project_id: Optional[str] = field(default_factory=lambda: os.getenv("PUBSUB_PROJECT_ID"))
    pubsub_topic_voice_events: str = field(default_factory=lambda: os.getenv("PUBSUB_TOPIC_VOICE_EVENTS", "voice-events"))
    
    # Session Settings
    session_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("SESSION_TIMEOUT_SECONDS", "3600")))
    max_concurrent_sessions: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_SESSIONS", "100")))
    
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Default language instruction for Hebrew
HEBREW_INSTRUCTION = """
דבר בעברית באופן טבעי ושוטף.
השתמש בשפה יומיומית ונעימה.
היה קשוב לניואנסים תרבותיים ישראליים.
"""

# 4 Options Protocol instruction
FOUR_OPTIONS_PROTOCOL = """
## פרוטוקול 4 האפשרויות
כשמציע פעולה או עוזר בהחלטה, תמיד הצג את האפשרויות הרלוונטיות:
1. **אוטונומיה מלאה**: "אני אעשה את זה עכשיו" - כשהפעולה ברורה ובטוחה
2. **המלצה עם אישור**: "אני ממליץ לעשות X, מאשר?" - כשצריך אישור
3. **בחירה**: "הנה האפשרויות: A, B, C - מה אתה מעדיף?" - כשיש כמה דרכים
4. **בקשת הבהרה**: "אני צריך יותר מידע לפני שאוכל לעזור" - כשחסר מידע
"""
