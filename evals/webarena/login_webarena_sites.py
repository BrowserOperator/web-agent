#!/usr/bin/env python3
"""
Login to WebArena sites using YAML-based tasks.

This script loads login tasks from YAML files and executes them using the
native evaluation runner. Each site has its own YAML task definition in
data/login/ directory.

Usage:
  python3 login_webarena_sites_v2.py                    # Login to all enabled sites
  python3 login_webarena_sites_v2.py --site shopping    # Login to specific site
  python3 login_webarena_sites_v2.py --list             # List available login tasks
  python3 login_webarena_sites_v2.py --verbose          # Verbose output
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add parent directory to path to import from evals/lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import (
    ConfigLoader,
    EvalLoader,
    APIClient,
    Evaluation
)


def expand_env_vars(text: str) -> str:
    """
    Expand environment variables in the format ${VAR:-default}.

    Args:
        text: String potentially containing ${VAR:-default} patterns

    Returns:
        String with environment variables expanded

    Examples:
        "${GITLAB:-http://gitlab.com}" -> "http://gitlab.com" (if GITLAB not set)
        "${GITLAB:-http://gitlab.com}" -> "http://custom.gitlab" (if GITLAB=http://custom.gitlab)
    """
    def replace_var(match):
        var_name = match.group(1)
        default_value = match.group(2)
        return os.environ.get(var_name, default_value)

    # Pattern: ${VAR_NAME:-default_value}
    pattern = r'\$\{([A-Z_]+):-([^}]+)\}'
    return re.sub(pattern, replace_var, text)


class LoginTaskRunner:
    """Manages execution of WebArena login tasks."""

    def __init__(self, config: ConfigLoader, verbose: bool = False):
        """
        Initialize login task runner.

        Args:
            config: ConfigLoader instance
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose
        self.api_client = APIClient(
            base_url=config.get_api_endpoint(),
            timeout=config.get_timeout()
        )
        self.login_tasks_dir = Path(__file__).parent / 'data' / 'login'

    def check_api_health(self) -> bool:
        """Check if API server is accessible."""
        return self.api_client.check_health()

    def load_login_tasks(self, site_filter: Optional[str] = None) -> List[Evaluation]:
        """
        Load login tasks from YAML files.

        Args:
            site_filter: Optional site name to filter (e.g., 'shopping', 'gitlab')

        Returns:
            List of Evaluation objects
        """
        import yaml

        tasks = []

        if not self.login_tasks_dir.exists():
            print(f"Warning: Login tasks directory not found: {self.login_tasks_dir}")
            return tasks

        for yaml_file in sorted(self.login_tasks_dir.glob('*.yaml')):
            try:
                # Load YAML file directly
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                if data is None:
                    continue

                # Create Evaluation object
                evaluation = Evaluation(yaml_file, data)

                # Apply site filter if specified
                if site_filter:
                    site = evaluation.metadata.get('site', '')
                    if site != site_filter:
                        continue

                # Only include enabled tasks
                if evaluation.enabled:
                    tasks.append(evaluation)
                elif self.verbose:
                    print(f"Skipping disabled task: {evaluation.name}")
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")
                continue

        return tasks

    def list_login_tasks(self):
        """List all available login tasks."""
        import yaml

        print("=" * 70)
        print("Available WebArena Login Tasks")
        print("=" * 70)

        all_tasks = []

        for yaml_file in sorted(self.login_tasks_dir.glob('*.yaml')):
            try:
                # Load YAML file directly
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                if data is None:
                    continue

                # Create Evaluation object
                evaluation = Evaluation(yaml_file, data)
                all_tasks.append(evaluation)
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")
                continue

        if not all_tasks:
            print("No login tasks found.")
            return

        for task in all_tasks:
            status = "✅ Enabled" if task.enabled else "❌ Disabled"
            site = task.metadata.get('site', 'unknown')
            raw_url = task.get_target_url()
            expanded_url = expand_env_vars(raw_url) if raw_url else 'N/A'
            print(f"\n{status}")
            print(f"  ID: {task.id}")
            print(f"  Name: {task.name}")
            print(f"  Site: {site}")
            print(f"  URL: {expanded_url}")
            print(f"  File: data/login/{task.file_path.name}")

        print(f"\nTotal: {len(all_tasks)} login tasks ({sum(1 for t in all_tasks if t.enabled)} enabled)")

    def execute_login_task(self, task: Evaluation) -> bool:
        """
        Execute a single login task.

        Args:
            task: Evaluation object for login task

        Returns:
            True if successful, False otherwise
        """
        site = task.metadata.get('site', 'unknown')
        username = task.metadata.get('account', {}).get('username', 'unknown')

        # Expand environment variables in URL
        raw_url = task.get_target_url()
        url = expand_env_vars(raw_url) if raw_url else None

        print(f"\n{'=' * 70}")
        print(f"Logging in to: {site}")
        print(f"{'=' * 70}")
        print(f"Task: {task.name}")
        print(f"URL: {url}")
        print(f"Username: {username}")

        if self.verbose:
            print(f"\nObjective:\n{task.get_input_message()}")

        try:
            print(f"\nSending login task to BrowserOperator...")

            # Get model configuration
            model_config = self.config.get_nested_model_config()

            # Send request
            response = self.api_client.send_request(
                input_message=task.get_input_message(),
                model_config=model_config,
                url=url,
                wait_timeout=task.get_wait_timeout() or 60000
            )

            if not response['success']:
                print(f"❌ Login failed: {response.get('error', 'Unknown error')}")
                return False

            print(f"✅ Login completed")

            if self.verbose:
                print(f"\nResponse:\n{response['response']}")
            else:
                print(f"Response: {response['response'][:200]}...")

            print(f"Time: {response['execution_time_ms']}ms")

            return True

        except Exception as e:
            print(f"\n❌ Error logging in to {site}: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def run_all_logins(self, site_filter: Optional[str] = None, delay: int = 2) -> int:
        """
        Execute all enabled login tasks.

        Args:
            site_filter: Optional site name to filter
            delay: Delay in seconds between login attempts

        Returns:
            Exit code (0 = success, 1 = partial failure)
        """
        print("=" * 70)
        print("WebArena Site Login via BrowserOperator")
        print("=" * 70)
        print("\nThis script logs into WebArena sites using YAML-based tasks.")
        print("The browser session persists, so subsequent tasks will be")
        print("automatically authenticated - no need to capture cookies!")

        # Check API health
        if not self.check_api_health():
            print("\n❌ BrowserOperator API is not accessible")
            print(f"   API endpoint: {self.config.get_api_endpoint()}")
            print("   Please start the container first")
            return 1

        print("\n✅ BrowserOperator API is accessible")
        print(f"   API endpoint: {self.config.get_api_endpoint()}")

        # Show model configuration
        model_config = self.config.get_nested_model_config()
        print(f"\n📋 Model Configuration:")
        print(f"   Main: {model_config['main_model']['provider']}/{model_config['main_model']['model']}")
        print(f"   Mini: {model_config['mini_model']['provider']}/{model_config['mini_model']['model']}")
        print(f"   Nano: {model_config['nano_model']['provider']}/{model_config['nano_model']['model']}")

        # Load login tasks
        tasks = self.load_login_tasks(site_filter=site_filter)

        if not tasks:
            if site_filter:
                print(f"\n⚠️  No enabled login tasks found for site: {site_filter}")
            else:
                print("\n⚠️  No enabled login tasks found")
            return 1

        print(f"\nFound {len(tasks)} login task(s) to execute")

        # Execute each login task
        results = {}
        for i, task in enumerate(tasks):
            site = task.metadata.get('site', 'unknown')
            success = self.execute_login_task(task)
            results[site] = success

            # Delay between logins (except after last one)
            if i < len(tasks) - 1 and delay > 0:
                print(f"\nWaiting {delay} seconds before next login...")
                time.sleep(delay)

        # Print summary
        print(f"\n{'=' * 70}")
        print("Summary")
        print(f"{'=' * 70}")

        for site, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"  {site:20s} {status}")

        success_count = sum(1 for s in results.values() if s)
        total_count = len(results)

        print(f"\n{success_count}/{total_count} sites logged in successfully")

        if success_count == total_count:
            print("\n🎉 All sites logged in successfully!")
            print("\nThe browser is now authenticated for all WebArena sites.")
            print("You can run authenticated tasks directly:")
            print("\n  cd evals/webarena")
            print("  python3 run_shopping_tasks.py --indices 0 --verbose")
            print("\nNote: The session will persist as long as the browser stays open.")
            return 0
        else:
            print("\n⚠️  Some logins failed. Check the errors above.")
            print("You may need to login manually via http://localhost:8000")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WebArena site login using YAML-based tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Login to all enabled sites
  python3 login_webarena_sites_v2.py

  # Login to specific site
  python3 login_webarena_sites_v2.py --site shopping

  # List available login tasks
  python3 login_webarena_sites_v2.py --list

  # Verbose output
  python3 login_webarena_sites_v2.py --verbose

  # Login to specific site with verbose output
  python3 login_webarena_sites_v2.py --site gitlab --verbose
        """
    )

    parser.add_argument(
        '--site',
        type=str,
        help='Login to specific site only (e.g., shopping, gitlab, shopping_admin)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available login tasks and exit'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='../config.yml',
        help='Path to config.yml (default: ../config.yml)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=2,
        help='Delay in seconds between login attempts (default: 2)'
    )

    args = parser.parse_args()

    # Load configuration
    config_path = Path(__file__).parent.parent / 'config.yml'
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        print("Please create config.yml from config.example.openai.yml")
        return 1

    try:
        config = ConfigLoader(str(config_path))
    except Exception as e:
        print(f"Error loading config: {e}")
        return 1

    # Create runner
    runner = LoginTaskRunner(config, verbose=args.verbose)

    # Handle --list flag
    if args.list:
        runner.list_login_tasks()
        return 0

    # Execute login tasks
    return runner.run_all_logins(
        site_filter=args.site,
        delay=args.delay
    )


if __name__ == '__main__':
    exit(main())
