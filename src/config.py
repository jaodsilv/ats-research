"""Configuration management for the resume/cover letter tailoring orchestration system.

This module provides configuration loading, validation, and management using Pydantic.
"""

from pathlib import Path
from typing import Any
import os
import uuid
import yaml

from pydantic import BaseModel, Field, field_validator


class Config(BaseModel):
    """Configuration for the tailoring orchestration system.

    Attributes:
        max_iterations: Maximum number of refinement iterations
        quality_threshold: Minimum quality score (0-1) for acceptance
        ai_detection_threshold: AI detection confidence threshold for cover letters (0.0-1.0)
        agent_pool_size: Maximum concurrent agents (None = unlimited)
        api_key: Anthropic API key (loaded from ANTHROPIC_API_KEY env var)
        model_name: Claude model identifier
        run_id: Unique identifier for this execution run
        base_data_dir: Base directory for all data storage
    """

    max_iterations: int = 10
    quality_threshold: float = 0.8
    ai_detection_threshold: float = 0.999
    agent_pool_size: int | None = None
    api_key: str | None = None
    model_name: str = "claude-sonnet-4-5-20250929"
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    base_data_dir: Path = Path("data")

    @field_validator('quality_threshold')
    @classmethod
    def validate_quality_threshold(cls, v: float) -> float:
        """Validate quality threshold is between 0 and 1.

        Args:
            v: Quality threshold value to validate

        Returns:
            Validated quality threshold

        Raises:
            ValueError: If threshold is not in range [0, 1]
        """
        if not 0 <= v <= 1:
            raise ValueError(f"quality_threshold must be between 0 and 1, got {v}")
        return v

    @field_validator('ai_detection_threshold')
    @classmethod
    def validate_ai_detection_threshold(cls, v: float) -> float:
        """Validate AI detection threshold is between 0 and 1.

        Args:
            v: AI detection threshold value to validate

        Returns:
            Validated AI detection threshold

        Raises:
            ValueError: If threshold is not in range [0, 1]
        """
        if not 0.0 <= v <= 1.0:
            raise ValueError("ai_detection_threshold must be between 0.0 and 1.0")
        return v

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: str | None) -> str:
        """Load API key from environment if not provided.

        Args:
            v: API key value (None to load from environment)

        Returns:
            API key string

        Raises:
            ValueError: If API key not found in config or environment
        """
        if v is None:
            v = os.getenv("ANTHROPIC_API_KEY")
            if v is None:
                raise ValueError(
                    "api_key not found. Set ANTHROPIC_API_KEY environment variable "
                    "or provide in config file"
                )
        return v

    @property
    def runs_dir(self) -> Path:
        """Get the directory for this specific run.

        Returns:
            Path to run-specific directory
        """
        return self.base_data_dir / "runs" / f"run-{self.run_id}"

    @property
    def inputs_dir(self) -> Path:
        """Get the directory for input files.

        Returns:
            Path to inputs directory
        """
        return self.base_data_dir / "inputs"

    @property
    def templates_dir(self) -> Path:
        """Get the directory for template files.

        Returns:
            Path to templates directory
        """
        return self.base_data_dir / "templates"

    @classmethod
    def load_from_file(cls, path: Path) -> "Config":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            Config instance with loaded settings

        Raises:
            FileNotFoundError: If config file does not exist
            yaml.YAMLError: If file is not valid YAML
        """
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Convert base_data_dir to Path if present
        if 'base_data_dir' in config_data:
            config_data['base_data_dir'] = Path(config_data['base_data_dir'])

        return cls(**config_data)

    def save_to_file(self, path: Path) -> None:
        """Save configuration to YAML file.

        Args:
            path: Path where configuration should be saved
        """
        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and handle Path objects
        config_dict = self.model_dump()
        config_dict['base_data_dir'] = str(self.base_data_dir)

        # Don't save API key to file for security
        if 'api_key' in config_dict:
            config_dict['api_key'] = None

        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)
