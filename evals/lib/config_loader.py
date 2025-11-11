"""
Configuration loader for evaluation framework.
Loads config.yml and performs environment variable substitution.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class ConfigLoader:
    """Loads and manages evaluation framework configuration."""

    def __init__(self, config_path: str = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to config.yml. If None, looks in evals/config.yml
        """
        # Load .env file if it exists
        if DOTENV_AVAILABLE:
            script_dir = Path(__file__).parent.parent
            env_file = script_dir / ".env"
            if env_file.exists():
                load_dotenv(env_file, override=True)

        if config_path is None:
            # Default to config.yml in evals directory
            script_dir = Path(__file__).parent.parent
            config_path = script_dir / "config.yml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Substitute environment variables
        config = self._substitute_env_vars(config)

        return config

    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in config.
        Supports ${VAR_NAME} and ${VAR_NAME:-default} syntax.

        Args:
            obj: Config object (dict, list, str, etc.)

        Returns:
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_env_var_in_string(obj)
        else:
            return obj

    def _substitute_env_var_in_string(self, value: str) -> str:
        """
        Substitute environment variables in a string.

        Supports:
        - ${VAR_NAME} - Required variable
        - ${VAR_NAME:-default} - Variable with default value

        Args:
            value: String that may contain env var references

        Returns:
            String with variables substituted
        """
        # Pattern for ${VAR_NAME} or ${VAR_NAME:-default}
        pattern = r'\$\{([A-Z_][A-Z0-9_]*)(:-([^}]*))?\}'

        def replace_match(match):
            var_name = match.group(1)
            default_value = match.group(3) if match.group(3) is not None else None

            # Get environment variable
            env_value = os.getenv(var_name)

            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                raise ValueError(
                    f"Environment variable ${{{var_name}}} not found and no default provided"
                )

        return re.sub(pattern, replace_match, value)

    def get_api_endpoint(self) -> str:
        """Get API endpoint URL."""
        return self.config.get('api_endpoint', 'http://localhost:8080')

    def get_model_config(self, model_tier: str) -> Dict[str, str]:
        """
        Get model configuration for a specific tier.

        Args:
            model_tier: One of 'main_model', 'mini_model', 'nano_model', 'judge_model'

        Returns:
            Dictionary with provider, model_name, api_key
        """
        if model_tier not in self.config:
            raise ValueError(f"Unknown model tier: {model_tier}")

        return self.config[model_tier]

    def get_nested_model_config(self) -> Dict[str, Dict[str, str]]:
        """
        Get nested model configuration for API requests.

        Returns:
            Dictionary in format expected by /v1/responses API:
            {
                "main_model": {"provider": "...", "model": "...", "api_key": "..."},
                "mini_model": {"provider": "...", "model": "...", "api_key": "..."},
                "nano_model": {"provider": "...", "model": "...", "api_key": "..."}
            }
        """
        result = {}

        for tier in ['main_model', 'mini_model', 'nano_model']:
            if tier in self.config:
                model_config = self.config[tier]
                result[tier] = {
                    'provider': model_config['provider'],
                    'model': model_config['model_name'],
                    'api_key': model_config['api_key']
                }

        return result

    def get_judge_config(self) -> Dict[str, Any]:
        """Get judge model configuration."""
        return self.config.get('judge_model', {})

    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution settings."""
        return self.config.get('execution', {})

    def get_reporting_config(self) -> Dict[str, Any]:
        """Get reporting settings."""
        return self.config.get('reporting', {})

    def get_default_limit(self) -> int:
        """Get default limit for number of evaluations to run."""
        return self.config.get('execution', {}).get('default_limit', 20)

    def get_timeout(self) -> int:
        """Get timeout for API requests in seconds."""
        return self.config.get('execution', {}).get('timeout', 300)

    def get_reports_dir(self) -> Path:
        """Get reports directory path."""
        reports_dir = self.config.get('reporting', {}).get('reports_dir', 'reports')
        # Make path relative to config file location
        config_dir = self.config_path.parent
        return config_dir / reports_dir


# Singleton instance
_config_loader = None


def get_config() -> ConfigLoader:
    """
    Get global config loader instance.

    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader
