#!/usr/bin/env python3
"""
Run shopping tasks from WebArena against BrowserOperator.

This script filters tasks by site (shopping) and runs them through the
eval-server API.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import from evals/lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import ConfigLoader, APIClient
from lib.webarena_adapter import WebArenaExecutor, WebArenaTask, WebArenaTaskLoader


def load_shopping_tasks(limit=10, start_index=0, task_indices=None):
    """
    Load shopping tasks from test.raw.json.

    Args:
        limit: Number of tasks to load (default: 10)
        start_index: Starting index in shopping tasks list (default: 0)
        task_indices: List of specific indices to run (overrides limit and start_index)

    Returns:
        List of task configurations
    """
    # Path from evals/webarena/ to project root, then to submodules
    project_root = Path(__file__).parent.parent.parent
    test_raw_file = project_root / 'submodules' / 'webarena' / 'config_files' / 'test.raw.json'

    if not test_raw_file.exists():
        print(f"Error: {test_raw_file} not found")
        return []

    with open(test_raw_file) as f:
        all_tasks = json.load(f)

    # Filter shopping tasks
    shopping_tasks = [t for t in all_tasks if 'shopping' in t.get('sites', [])]

    # If specific indices provided, use those
    if task_indices is not None:
        selected_tasks = []
        for idx in task_indices:
            if 0 <= idx < len(shopping_tasks):
                selected_tasks.append(shopping_tasks[idx])
            else:
                print(f"Warning: Index {idx} out of range (0-{len(shopping_tasks)-1})")
        return selected_tasks

    # Otherwise use start_index and limit
    end_index = start_index + limit if limit else len(shopping_tasks)
    return shopping_tasks[start_index:end_index]


def run_shopping_eval(limit=10, start_index=0, task_indices=None, verbose=False):
    """
    Run shopping tasks evaluation.

    Args:
        limit: Number of tasks to run (default: 10)
        start_index: Starting index in shopping tasks list (default: 0)
        task_indices: List of specific indices to run (overrides limit and start_index)
        verbose: Enable verbose output
    """

    # Set environment variables
    os.environ.setdefault('SHOPPING', 'http://onestopshop.com')
    os.environ.setdefault('SHOPPING_ADMIN', 'http://onestopshop.com/admin')

    print("=== OneShop WebArena Evaluation ===\n")
    print(f"Environment: SHOPPING={os.environ.get('SHOPPING')}")
    print(f"             SHOPPING_ADMIN={os.environ.get('SHOPPING_ADMIN')}\n")

    # Load config
    config_loader = ConfigLoader()

    # Create API client
    api_client = APIClient(base_url=config_loader.get_api_endpoint())

    # Get model config
    model_config = config_loader.get_nested_model_config()

    # Create executor
    executor = WebArenaExecutor(
        api_client=api_client,
        model_config=model_config,
        openai_api_key=os.environ.get('OPENAI_API_KEY')
    )

    # Load tasks
    if task_indices:
        print(f"Loading shopping tasks at indices: {task_indices}...")
    else:
        print(f"Loading shopping tasks (start={start_index}, limit={limit})...")
    task_configs = load_shopping_tasks(limit=limit, start_index=start_index, task_indices=task_indices)

    if not task_configs:
        print("Error: No shopping tasks found")
        return

    print(f"Found {len(task_configs)} shopping tasks\n")

    # Run tasks
    results = []
    for i, task_config in enumerate(task_configs, 1):
        task_id = task_config['task_id']
        intent = task_config.get('intent', 'No intent')

        print(f"\n[{i}/{len(task_configs)}] Task {task_id}")
        print(f"Intent: {intent[:100]}...")

        # Create WebArenaTask from config dict
        # We need to save it to a temp file first
        temp_file = Path(f'/tmp/webarena_task_{task_id}.json')
        with open(temp_file, 'w') as f:
            json.dump(task_config, f)

        try:
            task = WebArenaTask(temp_file)

            if verbose:
                print(f"Start URL: {task.get_start_url()}")
                print(f"Requires login: {task.requires_auth()}")

            # Execute task
            result = executor.execute_task(task, wait_timeout=30000)

            # Display result
            if result['success']:
                print(f"✓ Success - Score: {result['score']:.2f}")
                if verbose and result['response']:
                    print(f"Response: {result['response'][:200]}...")
            else:
                print(f"✗ Failed - {result.get('error', 'Unknown error')}")

            results.append({
                'task_id': task_id,
                'intent': intent,
                'success': result['success'],
                'score': result['score'],
                'error': result.get('error'),
                'execution_time_ms': result.get('execution_time_ms', 0)
            })

        except Exception as e:
            print(f"✗ Exception: {str(e)}")
            results.append({
                'task_id': task_id,
                'intent': intent,
                'success': False,
                'score': 0.0,
                'error': str(e),
                'execution_time_ms': 0
            })
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for r in results if r['score'] >= 0.5)
    failed = len(results) - passed
    avg_score = sum(r['score'] for r in results) / len(results) if results else 0

    print(f"Total: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Average Score: {avg_score:.2f}")

    # Save results
    results_file = Path(__file__).parent / 'reports' / 'shopping_tasks_results.json'
    results_file.parent.mkdir(exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Run shopping tasks from WebArena',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run first 10 shopping tasks (default)
  python3 run_shopping_tasks.py

  # Run 5 tasks starting from index 0
  python3 run_shopping_tasks.py --limit 5

  # Run tasks starting from index 10
  python3 run_shopping_tasks.py --start 10 --limit 5

  # Run specific tasks by index (0-based)
  python3 run_shopping_tasks.py --indices 0 5 10

  # Run a single task by index with verbose output
  python3 run_shopping_tasks.py --indices 0 --verbose
        """
    )
    parser.add_argument('--limit', type=int, default=10,
                       help='Number of tasks to run (default: 10)')
    parser.add_argument('--start', type=int, default=0,
                       help='Starting index in shopping tasks list (default: 0)')
    parser.add_argument('--indices', type=int, nargs='+',
                       help='Specific task indices to run (0-based, overrides --limit and --start)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')

    args = parser.parse_args()

    run_shopping_eval(
        limit=args.limit,
        start_index=args.start,
        task_indices=args.indices,
        verbose=args.verbose
    )


if __name__ == '__main__':
    main()
