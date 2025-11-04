#!/usr/bin/env python3
"""
WebArena Evaluation Runner

Runs WebArena benchmark tasks using the eval-server API infrastructure.

Usage:
  python3 run_webarena.py --task-id 1                    # Run specific task
  python3 run_webarena.py --all --public-only            # Run all public site tasks
  python3 run_webarena.py --limit 10 --verbose           # Run 10 tasks with verbose output
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib import ConfigLoader, APIClient
from lib.webarena_adapter import WebArenaTask, WebArenaExecutor, WebArenaTaskLoader


class WebArenaRunner:
    """Manages WebArena task execution and reporting."""

    def __init__(self, config: ConfigLoader, verbose: bool = False):
        """
        Initialize WebArena runner.

        Args:
            config: Configuration loader
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose

        # Initialize components
        self.task_loader = WebArenaTaskLoader()
        # Use longer timeout for WebArena tasks (can take 60-120 seconds)
        timeout = max(config.get_timeout(), 180)
        self.api_client = APIClient(
            base_url=config.get_api_endpoint(),
            timeout=timeout
        )

        # Get nested model config for API requests
        model_config = config.get_nested_model_config()

        # Get OpenAI API key for fuzzy matching
        judge_config = config.get_judge_config()
        openai_api_key = judge_config.get('api_key') if judge_config['provider'] == 'openai' else None

        # Initialize executor
        self.executor = WebArenaExecutor(
            api_client=self.api_client,
            model_config=model_config,
            openai_api_key=openai_api_key
        )

        # Results tracking
        self.results = []

    def run_task_by_id(self, task_id: int):
        """
        Run a specific task by ID.

        Args:
            task_id: Task ID number
        """
        print(f"\n{'='*70}")
        print(f"Running WebArena Task {task_id}")
        print(f"{'='*70}\n")

        # Check API server health
        print("Checking API server connection...")
        if not self.api_client.check_health():
            print("ERROR: Cannot connect to API server at", self.config.get_api_endpoint())
            print("Please ensure the evaluation server is running.")
            sys.exit(1)
        print("✓ API server is reachable\n")

        try:
            # Load task
            task = self.task_loader.load_task(task_id)
            print(f"Loaded task: {task.intent}")
            print(f"Sites: {task.sites}")
            print(f"Eval types: {task.eval_types}\n")

            # Execute task
            result = self._run_single_task(task)
            self.results.append(result)

            # Print result
            self._print_task_result(result, 1, 1)

        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to run task {task_id}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        # Print summary
        self._print_summary()

        # Save report
        self._save_report('webarena-single')

    def run_all_tasks(
        self,
        limit: Optional[int] = None,
        public_only: bool = False
    ):
        """
        Run all available WebArena tasks.

        Args:
            limit: Maximum number of tasks to run
            public_only: If True, only run tasks that don't require self-hosted sites
        """
        print(f"\n{'='*70}")
        print(f"Running WebArena Tasks")
        print(f"{'='*70}\n")

        # Check API server health
        print("Checking API server connection...")
        if not self.api_client.check_health():
            print("ERROR: Cannot connect to API server at", self.config.get_api_endpoint())
            print("Please ensure the evaluation server is running.")
            sys.exit(1)
        print("✓ API server is reachable\n")

        # Load tasks
        print("Loading WebArena tasks...")
        tasks = self.task_loader.load_all_example_tasks()

        if public_only:
            tasks = self.task_loader.filter_public_site_tasks(tasks)
            print(f"Filtered to {len(tasks)} public site tasks")

        # Apply limit
        if limit and limit < len(tasks):
            tasks = tasks[:limit]

        if not tasks:
            print("No tasks found to run.")
            return

        print(f"Found {len(tasks)} tasks to run\n")

        # Print statistics
        site_counts = self.task_loader.count_tasks_by_site(tasks)
        eval_counts = self.task_loader.count_tasks_by_eval_type(tasks)
        print("Tasks by site:", dict(sorted(site_counts.items())))
        print("Tasks by eval type:", dict(sorted(eval_counts.items())))
        print()

        # Run each task
        for i, task in enumerate(tasks, 1):
            print(f"[{i}/{len(tasks)}] Running task {task.task_id}: {task.get_site_category()}")

            if self.verbose:
                print(f"  Intent: {task.intent}")
                print(f"  Start URL: {task.start_url}")

            try:
                result = self._run_single_task(task)
                self.results.append(result)

                # Print result
                self._print_task_result(result, i, len(tasks))

            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Saving partial results...")
                break
            except Exception as e:
                print(f"  ERROR: {str(e)}\n")
                # Record failure
                self.results.append({
                    'task_id': task.task_id,
                    'site': task.get_site_category(),
                    'intent': task.intent,
                    'success': False,
                    'score': 0.0,
                    'response': None,
                    'execution_time_ms': 0,
                    'error': str(e)
                })

        # Print summary
        self._print_summary()

        # Save report
        self._save_report('webarena-batch')

    def _run_single_task(self, task: WebArenaTask) -> dict:
        """
        Run a single WebArena task.

        Args:
            task: WebArenaTask to execute

        Returns:
            Result dictionary
        """
        # Execute task
        result = self.executor.execute_task(task)

        # Add task metadata to result
        result['task_id'] = task.task_id
        result['site'] = task.get_site_category()
        result['intent'] = task.intent
        result['eval_types'] = task.eval_types

        # Verbose output
        if self.verbose and result['success']:
            print(f"\n  Response: {result['response'][:200]}{'...' if len(result['response']) > 200 else ''}")
            print(f"  Score: {result['score']:.2f}")
            if result['page_url']:
                print(f"  Final URL: {result['page_url']}")

        return result

    def _print_task_result(self, result: dict, current: int, total: int):
        """Print result for a single task."""
        status = "PASS" if result['success'] and result['score'] >= 0.8 else "FAIL"
        print(f"  Task ID: {result['task_id']}")
        print(f"  Site: {result['site']}")
        print(f"  Status: {status}")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Time: {result['execution_time_ms']}ms")

        if result['error']:
            print(f"  Error: {result['error']}")

        print()

    def _print_summary(self):
        """Print summary statistics."""
        if not self.results:
            return

        total = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        passed = sum(1 for r in self.results if r['success'] and r['score'] >= 0.8)
        failed = total - passed

        avg_score = sum(r['score'] for r in self.results) / total if total > 0 else 0
        avg_time = sum(r['execution_time_ms'] for r in self.results) / total if total > 0 else 0

        # Success rate
        success_rate = (successful / total) * 100 if total > 0 else 0
        pass_rate = (passed / total) * 100 if total > 0 else 0

        print(f"\n{'='*70}")
        print("Summary")
        print(f"{'='*70}")
        print(f"Total Tasks: {total}")
        print(f"Successful Execution: {successful} ({success_rate:.1f}%)")
        print(f"Passed (score >= 0.8): {passed} ({pass_rate:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Average Score: {avg_score:.2f}")
        print(f"Average Time: {avg_time:.0f}ms")

        # Break down by site
        if total > 1:
            site_scores = {}
            for result in self.results:
                site = result['site']
                if site not in site_scores:
                    site_scores[site] = []
                site_scores[site].append(result['score'])

            print("\nScores by site:")
            for site, scores in sorted(site_scores.items()):
                avg = sum(scores) / len(scores)
                print(f"  {site}: {avg:.2f} ({len(scores)} tasks)")

        print(f"{'='*70}\n")

    def _save_report(self, category: str):
        """
        Save evaluation results to CSV report.

        Args:
            category: Category name for report filename
        """
        if not self.results:
            return

        # Create reports directory
        reports_dir = self.config.get_reports_dir()
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{category}_{timestamp}.csv"
        filepath = reports_dir / filename

        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'timestamp',
                'task_id',
                'site',
                'intent',
                'eval_types',
                'status',
                'score',
                'response',
                'execution_time_ms',
                'error'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for result in self.results:
                status = "PASS" if result['success'] and result['score'] >= 0.8 else "FAIL"
                # Handle None response safely
                response_text = result.get('response') or ''
                response_truncated = response_text[:500] if response_text else ''

                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'task_id': result['task_id'],
                    'site': result['site'],
                    'intent': result['intent'],
                    'eval_types': ', '.join(result.get('eval_types', [])),
                    'status': status,
                    'score': f"{result['score']:.2f}",
                    'response': response_truncated,
                    'execution_time_ms': result['execution_time_ms'],
                    'error': result.get('error', '')
                })

        print(f"Report saved to: {filepath}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WebArena evaluation runner for browser-agent",
        epilog="""
Examples:
  # Run specific task
  python3 run_webarena.py --task-id 1

  # Run all tasks (limited to 10)
  python3 run_webarena.py --all --limit 10

  # Run only public site tasks (no self-hosted required)
  python3 run_webarena.py --all --public-only --limit 20

  # Verbose mode
  python3 run_webarena.py --task-id 2 --verbose
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Execution mode
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--task-id',
        type=int,
        help='Run a specific WebArena task by ID (e.g., 1, 2, 3)'
    )
    mode_group.add_argument(
        '--all',
        action='store_true',
        help='Run all available WebArena tasks'
    )

    # Options
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of tasks to run (default: all)'
    )
    parser.add_argument(
        '--public-only',
        action='store_true',
        help='Only run tasks that work on public sites (no self-hosted required)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to config.yml (default: evals/config.yml)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output (show intent, response, URLs)'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = ConfigLoader(config_path=args.config)

        # Create runner
        runner = WebArenaRunner(config, verbose=args.verbose)

        # Execute based on mode
        if args.task_id:
            runner.run_task_by_id(args.task_id)
        elif args.all:
            limit = args.limit if args.limit is not None else config.get_default_limit()
            runner.run_all_tasks(
                limit=limit,
                public_only=args.public_only
            )

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
