"""
WebArena Adapter

Adapts WebArena JSON task configurations to work with the eval-server API.

This module provides:
- WebArenaTask: Parses and provides access to WebArena JSON configs
- WebArenaExecutor: Executes tasks via APIClient and evaluates results
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from lib.api_client import APIClient
from lib.webarena_evaluators import create_evaluator

# URL mappings for WebArena sites
# These use the actual WebArena domain names which are routed via Docker host overrides
WEBARENA_URL_MAP = {
    '__SHOPPING__': os.environ.get('SHOPPING', 'http://onestopshop.com'),
    '__SHOPPING_ADMIN__': os.environ.get('SHOPPING_ADMIN', 'http://onestopshop.com/admin'),
    '__REDDIT__': os.environ.get('REDDIT', 'http://reddit.com'),
    '__GITLAB__': os.environ.get('GITLAB', 'http://gitlab.com'),
    '__WIKIPEDIA__': os.environ.get('WIKIPEDIA', 'http://wikipedia.org'),
    '__MAP__': os.environ.get('MAP', 'http://openstreetmap.org'),
    '__HOMEPAGE__': os.environ.get('HOMEPAGE', 'http://homepage.com'),
}


class WebArenaTask:
    """Represents a single WebArena task from JSON configuration."""

    def __init__(self, config_file: Path):
        """
        Initialize WebArena task from config file.

        Args:
            config_file: Path to JSON configuration file
        """
        self.config_file = Path(config_file)
        with open(self.config_file, 'r') as f:
            self.config = json.load(f)

        # Extract key fields
        self.task_id = self.config.get('task_id', self.config_file.stem)
        self.sites = self.config.get('sites', [])
        self.intent = self.config.get('intent', '')
        self.start_url = self.config.get('start_url', '')
        self.require_login = self.config.get('require_login', False)
        self.storage_state = self.config.get('storage_state')

        # Evaluation config
        self.eval_config = self.config.get('eval', {})
        self.eval_types = self.eval_config.get('eval_types', [])

    def get_intent(self) -> str:
        """Get the task intent/instruction."""
        return self.intent

    def get_start_url(self) -> str:
        """Get the starting URL for the task with placeholders replaced."""
        url = self.start_url
        # Replace URL placeholders with actual URLs
        for placeholder, actual_url in WEBARENA_URL_MAP.items():
            if placeholder in url:
                url = url.replace(placeholder, actual_url)
        return url

    def requires_auth(self) -> bool:
        """Check if task requires authentication."""
        return self.require_login

    def get_storage_state_path(self) -> Optional[Path]:
        """Get path to storage state (cookies) if required."""
        if not self.storage_state:
            return None
        # Make path relative to webarena directory
        webarena_dir = Path(__file__).parent.parent / 'webarena'
        return webarena_dir / self.storage_state

    def get_eval_types(self) -> list[str]:
        """Get list of evaluation types (string_match, url_match, program_html)."""
        return self.eval_types

    def is_local_site(self) -> bool:
        """Check if task uses self-hosted WebArena sites."""
        webarena_sites = ['reddit', 'shopping', 'shopping_admin', 'gitlab', 'wikipedia', 'map']
        return any(site in webarena_sites for site in self.sites)

    def get_site_category(self) -> str:
        """Get the primary site category."""
        if self.sites:
            return self.sites[0]
        return 'misc'

    def __repr__(self):
        return (
            f"WebArenaTask(id={self.task_id}, sites={self.sites}, "
            f"eval_types={self.eval_types})"
        )


class WebArenaExecutor:
    """Executes WebArena tasks via eval-server API."""

    def __init__(
        self,
        api_client: APIClient,
        model_config: Dict[str, Dict[str, str]],
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize WebArena executor.

        Args:
            api_client: APIClient instance for communicating with eval-server
            model_config: Nested model configuration for API requests
            openai_api_key: Optional OpenAI API key for fuzzy matching
        """
        self.api_client = api_client
        self.model_config = model_config
        self.openai_api_key = openai_api_key

    def execute_task(self, task: WebArenaTask, wait_timeout: int = 30000) -> Dict[str, Any]:
        """
        Execute a WebArena task.

        Args:
            task: WebArenaTask to execute
            wait_timeout: Page load timeout in milliseconds

        Returns:
            Dictionary with execution results:
            - success: bool
            - response: str (agent's response)
            - page_url: str (final page URL)
            - score: float (evaluation score 0-1)
            - evaluator: EvaluatorCombination (for detailed evaluation)
            - client_id: str (for screenshot capture)
            - tab_id: str (for screenshot capture)
            - execution_time_ms: int
            - error: str (if failed)
        """
        # Note: Self-hosted site check removed - URLs are now mapped via environment variables
        # and Docker host overrides handle routing to 172.16.55.59

        # Send request to eval-server
        api_response = self.api_client.send_request(
            input_message=task.get_intent(),
            model_config=self.model_config,
            url=task.get_start_url(),
            wait_timeout=wait_timeout
        )

        if not api_response['success']:
            return {
                'success': False,
                'response': None,
                'page_url': None,
                'score': 0.0,
                'evaluator': None,
                'client_id': api_response.get('client_id'),
                'tab_id': api_response.get('tab_id'),
                'execution_time_ms': api_response['execution_time_ms'],
                'error': api_response['error']
            }

        # Extract response and metadata
        response_text = api_response['response']
        client_id = api_response.get('client_id')
        tab_id = api_response.get('tab_id')

        # Get current page URL if available
        # TODO: eval-server needs to expose /page/url endpoint to get current URL
        # This is required for URL evaluation (url_match eval type)
        # For now, URL evaluation will score 0.0 without this
        page_url = None

        # Create evaluator for this task
        evaluator = create_evaluator(
            config=task.config,
            openai_api_key=self.openai_api_key
        )

        # Evaluate the response
        try:
            score = evaluator.evaluate(
                response=response_text,
                config=task.config,
                page_url=page_url,
                api_client=self.api_client,
                client_id=client_id,
                tab_id=tab_id
            )
        except Exception as e:
            return {
                'success': False,
                'response': response_text,
                'page_url': page_url,
                'score': 0.0,
                'evaluator': evaluator,
                'client_id': client_id,
                'tab_id': tab_id,
                'execution_time_ms': api_response['execution_time_ms'],
                'error': f"Evaluation failed: {str(e)}"
            }

        return {
            'success': True,
            'response': response_text,
            'page_url': page_url,
            'score': score,
            'evaluator': evaluator,
            'client_id': client_id,
            'tab_id': tab_id,
            'execution_time_ms': api_response['execution_time_ms'],
            'error': None
        }

    def execute_task_from_file(
        self,
        config_file: Path,
        wait_timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Execute a WebArena task from a config file.

        Args:
            config_file: Path to JSON configuration file
            wait_timeout: Page load timeout in milliseconds

        Returns:
            Dictionary with execution results (same as execute_task)
        """
        task = WebArenaTask(config_file)
        return self.execute_task(task, wait_timeout=wait_timeout)


class WebArenaTaskLoader:
    """Load WebArena tasks from various sources."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize task loader.

        Args:
            config_dir: Path to WebArena config_files directory.
                       Defaults to submodules/webarena/config_files/
        """
        if config_dir is None:
            # Go from evals/lib/ to project root, then to submodules/webarena/config_files
            project_root = Path(__file__).parent.parent.parent
            webarena_dir = project_root / 'submodules' / 'webarena'
            config_dir = webarena_dir / 'config_files'

        self.config_dir = Path(config_dir)

        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {self.config_dir}")

    def load_task(self, task_id: int) -> WebArenaTask:
        """
        Load a single task by ID from examples directory.

        Args:
            task_id: Task ID number

        Returns:
            WebArenaTask instance
        """
        config_file = self.config_dir / 'examples' / f'{task_id}.json'
        if not config_file.exists():
            raise FileNotFoundError(f"Task config not found: {config_file}")

        return WebArenaTask(config_file)

    def load_task_from_file(self, config_file: Path) -> WebArenaTask:
        """
        Load a task from a specific config file.

        Args:
            config_file: Path to JSON configuration file

        Returns:
            WebArenaTask instance
        """
        return WebArenaTask(config_file)

    def load_all_example_tasks(self) -> list[WebArenaTask]:
        """
        Load all tasks from examples directory.

        Returns:
            List of WebArenaTask instances
        """
        examples_dir = self.config_dir / 'examples'
        if not examples_dir.exists():
            return []

        tasks = []
        for config_file in sorted(examples_dir.glob('*.json')):
            try:
                task = WebArenaTask(config_file)
                tasks.append(task)
            except Exception as e:
                print(f"Warning: Failed to load {config_file}: {e}")
                continue

        return tasks

    def load_test_raw_tasks(self, limit: Optional[int] = None) -> list[Dict[str, Any]]:
        """
        Load tasks from test.raw.json.

        Args:
            limit: Optional limit on number of tasks to load

        Returns:
            List of task config dictionaries
        """
        test_raw_file = self.config_dir / 'test.raw.json'
        if not test_raw_file.exists():
            raise FileNotFoundError(f"test.raw.json not found: {test_raw_file}")

        with open(test_raw_file, 'r') as f:
            all_tasks = json.load(f)

        if limit:
            all_tasks = all_tasks[:limit]

        return all_tasks

    def filter_public_site_tasks(self, tasks: list[WebArenaTask]) -> list[WebArenaTask]:
        """
        Filter tasks to only those that work on public sites (no self-hosted required).

        Args:
            tasks: List of WebArenaTask instances

        Returns:
            Filtered list of tasks
        """
        return [task for task in tasks if not task.is_local_site()]

    def count_tasks_by_site(self, tasks: list[WebArenaTask]) -> Dict[str, int]:
        """
        Count tasks by site category.

        Args:
            tasks: List of WebArenaTask instances

        Returns:
            Dictionary mapping site category to count
        """
        counts: Dict[str, int] = {}
        for task in tasks:
            category = task.get_site_category()
            counts[category] = counts.get(category, 0) + 1
        return counts

    def count_tasks_by_eval_type(self, tasks: list[WebArenaTask]) -> Dict[str, int]:
        """
        Count tasks by evaluation type.

        Args:
            tasks: List of WebArenaTask instances

        Returns:
            Dictionary mapping eval type to count
        """
        counts: Dict[str, int] = {}
        for task in tasks:
            for eval_type in task.get_eval_types():
                counts[eval_type] = counts.get(eval_type, 0) + 1
        return counts
