"""Default configuration for memory comparison framework."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


def load_env_file() -> None:
    """
    Load .env file from project root directory.

    Searches for .env in:
    1. Environment variable CMEMORY_ENV_PATH (explicit path)
    2. Package installation directory
    3. Current working directory
    """
    try:
        from dotenv import load_dotenv

        # Check for explicit path from environment
        explicit_path = os.getenv("CMEMORY_ENV_PATH")
        if explicit_path:
            env_path = Path(explicit_path)
            if env_path.exists():
                load_dotenv(env_path)
                return

        # Try package directory first (this file is in cmemory/config/)
        pkg_env = Path(__file__).parent.parent.parent / ".env"
        if pkg_env.exists():
            load_dotenv(pkg_env)
            return

        # Try current working directory
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            load_dotenv(cwd_env)
            return

    except ImportError:
        # python-dotenv not installed, use system env vars only
        pass


# Load .env file at module import
load_env_file()


@dataclass
class Config:
    """Main configuration class."""

    # API settings - loaded from .env or system env
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    base_url: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))
    qa_model: str = field(default_factory=lambda: os.getenv("QA_MODEL", "gpt-4o-mini"))
    judge_model: str = field(default_factory=lambda: os.getenv("JUDGE_MODEL", "gpt-4o-mini"))

    # Embedding settings
    embedding_provider: str = field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "openai"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    embedding_dims: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMS", "1536")))

    # Vector Store settings
    vector_store_provider: str = field(default_factory=lambda: os.getenv("VECTOR_STORE_PROVIDER", "qdrant"))
    vector_store_path: str = field(default_factory=lambda: os.getenv("VECTOR_STORE_PATH", ".memory_data/qdrant"))

    # Evaluation settings
    retrieval_limit: int = 10
    batch_size: int = 1

    # Storage settings
    storage_dir: str = field(default_factory=lambda: os.getenv("STORAGE_DIR", ".memory_data"))

    # Engine-specific configs
    engine_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "qa_model": self.qa_model,
            "judge_model": self.judge_model,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "embedding_dims": self.embedding_dims,
            "vector_store_provider": self.vector_store_provider,
            "vector_store_path": self.vector_store_path,
            "retrieval_limit": self.retrieval_limit,
            "batch_size": self.batch_size,
            "storage_dir": self.storage_dir,
            "engine_configs": self.engine_configs,
        }


def get_default_config() -> Config:
    """Get default configuration (loaded from .env)."""
    return Config()