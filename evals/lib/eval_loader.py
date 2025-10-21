"""
Evaluation loader for discovering and loading YAML evaluation definitions.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


class Evaluation:
    """Represents a single evaluation definition."""

    def __init__(self, file_path: Path, data: Dict[str, Any]):
        """
        Initialize evaluation.

        Args:
            file_path: Path to the YAML file
            data: Parsed YAML data
        """
        self.file_path = file_path
        self.data = data

        # Extract key fields
        self.id = data.get('id', file_path.stem)
        self.name = data.get('name', self.id)
        self.description = data.get('description', '')
        self.enabled = data.get('enabled', True)
        self.tool = data.get('tool', 'unknown')
        self.timeout = data.get('timeout', 60000)

        # Target configuration
        self.target = data.get('target', {})
        self.url = self.target.get('url', '')

        # Input configuration
        self.input = data.get('input', {})

        # Validation configuration
        self.validation = data.get('validation', {})
        self.validation_type = self.validation.get('type', 'llm-judge')

        # Metadata
        self.metadata = data.get('metadata', {})
        self.tags = self.metadata.get('tags', [])
        self.priority = self.metadata.get('priority', 'medium')

        # Determine category from file path
        self.category = self._determine_category()

    def _determine_category(self) -> str:
        """Determine evaluation category from file path."""
        # Get parent directory name
        parent_dir = self.file_path.parent.name
        if parent_dir and parent_dir != 'data':
            return parent_dir
        return 'unknown'

    def get_input_message(self) -> str:
        """
        Extract the input message for the evaluation.

        Returns:
            Input message/prompt for the agent
        """
        # For chat tool, extract message
        if self.tool == 'chat':
            return self.input.get('message', '')

        # For action_agent tool, extract objective
        if self.tool == 'action_agent':
            return self.input.get('objective', '')

        # For research_agent tool, extract query
        if self.tool == 'research_agent':
            return self.input.get('query', '')

        # For web_task_agent, extract task
        if self.tool == 'web_task_agent':
            return self.input.get('task', '')

        # For extract_data tools, return instruction
        if self.tool in ['extract_data', 'extract_schema_streamlined']:
            return self.input.get('instruction', 'Extract data according to schema')

        # For take_screenshot tool, describe the action
        if self.tool == 'take_screenshot':
            full_page = self.input.get('fullPage', False)
            return f"Take {'full page' if full_page else 'viewport'} screenshot of {self.url}"

        # Fallback: return description
        return self.description

    def get_validation_criteria(self) -> List[str]:
        """
        Get validation criteria for LLM judge.

        Returns:
            List of criteria strings
        """
        llm_judge = self.validation.get('llm_judge', {})
        return llm_judge.get('criteria', [])

    def get_judge_model(self) -> str:
        """Get the model specified for judging this evaluation."""
        llm_judge = self.validation.get('llm_judge', {})
        return llm_judge.get('model', 'gpt-4.1-mini')

    def requires_vision_judge(self) -> bool:
        """
        Check if this evaluation requires vision judge (visual verification).

        Returns:
            True if visual verification is enabled, False otherwise
        """
        if self.validation_type != 'llm-judge':
            return False

        llm_judge = self.validation.get('llm_judge', {})
        visual_verification = llm_judge.get('visual_verification', {})
        return visual_verification.get('enabled', False)

    def get_visual_verification_config(self) -> Optional[Dict[str, Any]]:
        """
        Get visual verification configuration.

        Returns:
            Visual verification config dict or None if not enabled
        """
        if not self.requires_vision_judge():
            return None

        llm_judge = self.validation.get('llm_judge', {})
        return llm_judge.get('visual_verification', {})

    def get_verification_prompts(self) -> List[str]:
        """
        Get visual verification prompts.

        Returns:
            List of verification prompt strings for vision judge
        """
        visual_config = self.get_visual_verification_config()
        if not visual_config:
            return []

        return visual_config.get('prompts', [])

    def get_target_url(self) -> Optional[str]:
        """
        Get the target URL for this evaluation.

        Returns:
            Target URL or None if not specified
        """
        url = self.target.get('url', '')
        return url if url else None

    def get_wait_timeout(self) -> Optional[int]:
        """
        Get the wait timeout for page load.

        Returns:
            Wait timeout in milliseconds or None if not specified
        """
        return self.target.get('wait_timeout')

    def is_enabled(self) -> bool:
        """Check if evaluation is enabled."""
        return self.enabled

    def __repr__(self):
        return f"Evaluation(id={self.id}, name={self.name}, tool={self.tool}, category={self.category})"


class EvalLoader:
    """Loads evaluation definitions from YAML files."""

    def __init__(self, data_dir: str = None):
        """
        Initialize eval loader.

        Args:
            data_dir: Path to data directory containing evaluation YAML files.
                     If None, uses evals/data/
        """
        if data_dir is None:
            # Default to data/ in evals directory
            script_dir = Path(__file__).parent.parent
            data_dir = script_dir / "data"

        self.data_dir = Path(data_dir)

        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

    def load_from_directory(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Evaluation]:
        """
        Load evaluations from directory.

        Args:
            category: Optional category filter (subdirectory name).
                     If None, loads from all categories.
            enabled_only: If True, only return enabled evaluations.

        Returns:
            List of Evaluation objects
        """
        evaluations = []

        if category:
            # Load from specific category directory
            category_dir = self.data_dir / category
            if not category_dir.exists():
                raise FileNotFoundError(f"Category directory not found: {category_dir}")
            yaml_files = sorted(category_dir.glob("*.yaml"))
        else:
            # Load from all subdirectories
            yaml_files = sorted(self.data_dir.glob("*/*.yaml"))

        for yaml_file in yaml_files:
            try:
                # Skip config.yaml files
                if yaml_file.name == 'config.yaml':
                    continue

                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                if data is None:
                    continue

                evaluation = Evaluation(yaml_file, data)

                # Filter by enabled status
                if enabled_only and not evaluation.is_enabled():
                    continue

                evaluations.append(evaluation)

            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")
                continue

        return evaluations

    def load_by_id(self, eval_id: str) -> Optional[Evaluation]:
        """
        Load a specific evaluation by ID.

        Args:
            eval_id: Evaluation ID to load

        Returns:
            Evaluation object or None if not found
        """
        # Search all YAML files for matching ID
        for yaml_file in self.data_dir.glob("*/*.yaml"):
            try:
                if yaml_file.name == 'config.yaml':
                    continue

                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                if data and data.get('id') == eval_id:
                    return Evaluation(yaml_file, data)

            except Exception:
                continue

        return None

    def get_categories(self) -> List[str]:
        """
        Get list of available evaluation categories.

        Returns:
            List of category names (subdirectory names)
        """
        categories = []
        for item in self.data_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                categories.append(item.name)
        return sorted(categories)

    def count_evaluations(self, category: Optional[str] = None) -> int:
        """
        Count evaluations in a category or all categories.

        Args:
            category: Optional category filter

        Returns:
            Number of evaluation files
        """
        if category:
            category_dir = self.data_dir / category
            if not category_dir.exists():
                return 0
            return len(list(category_dir.glob("*.yaml"))) - \
                   len(list(category_dir.glob("config.yaml")))
        else:
            total = 0
            for subdir in self.data_dir.iterdir():
                if subdir.is_dir():
                    yaml_files = list(subdir.glob("*.yaml"))
                    config_files = list(subdir.glob("config.yaml"))
                    total += len(yaml_files) - len(config_files)
            return total
