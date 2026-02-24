"""
Configuration settings for the Customer Support Agent.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")

    # Model Configuration
    llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL")
    embedding_model: str = Field(
        "text-embedding-3-small", env="EMBEDDING_MODEL")
    temperature: float = Field(0.3, env="TEMPERATURE")
    max_tokens: int = Field(2048, env="MAX_TOKENS")

    # Agent Configuration
    knowledge_base_path: str = Field(
        "src/knowledge_base/documents", env="KB_PATH")
    chunk_size: int = Field(512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(50, env="CHUNK_OVERLAP")

    # Tool Configuration
    enable_billing_tool: bool = Field(True, env="ENABLE_BILLING")
    enable_ticket_tool: bool = Field(True, env="ENABLE_TICKETS")
    enable_status_tool: bool = Field(True, env="ENABLE_STATUS")

    # Evaluation Settings
    eval_batch_size: int = Field(10, env="EVAL_BATCH_SIZE")
    eval_output_dir: str = Field("evaluation_results", env="EVAL_OUTPUT_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create a global settings instance
settings = Settings()
