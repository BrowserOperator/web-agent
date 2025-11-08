#!/usr/bin/env python3
"""
Quick test script to verify WebArena integration.
Tests imports, task loading, and basic functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path to import from evals/lib
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    try:
        from lib.webarena_evaluators import (
            StringEvaluator,
            URLEvaluator,
            HTMLContentEvaluator,
            create_evaluator
        )
        from lib.webarena_adapter import (
            WebArenaTask,
            WebArenaExecutor,
            WebArenaTaskLoader
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_loading():
    """Test loading WebArena tasks."""
    print("\nTesting task loading...")
    try:
        from lib.webarena_adapter import WebArenaTaskLoader

        loader = WebArenaTaskLoader()

        # Load task 1
        task = loader.load_task(1)
        print(f"✓ Loaded task 1: {task.intent}")
        print(f"  Sites: {task.sites}")
        print(f"  Eval types: {task.eval_types}")
        print(f"  Requires auth: {task.requires_auth()}")
        print(f"  Is local site: {task.is_local_site()}")

        # Load all example tasks
        tasks = loader.load_all_example_tasks()
        print(f"✓ Loaded {len(tasks)} example tasks")

        # Count by site
        site_counts = loader.count_tasks_by_site(tasks)
        print(f"  Tasks by site: {site_counts}")

        # Count by eval type
        eval_counts = loader.count_tasks_by_eval_type(tasks)
        print(f"  Tasks by eval type: {eval_counts}")

        # Filter public sites
        public_tasks = loader.filter_public_site_tasks(tasks)
        print(f"✓ Found {len(public_tasks)} public site tasks")

        return True
    except Exception as e:
        print(f"✗ Task loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_evaluators():
    """Test WebArena evaluators."""
    print("\nTesting evaluators...")
    try:
        from lib.webarena_evaluators import StringEvaluator, URLEvaluator

        # Test StringEvaluator
        evaluator = StringEvaluator()

        # Test exact match
        score1 = evaluator.exact_match("hello world", "Hello World")
        print(f"✓ Exact match test: {score1} (expected 1.0)")

        # Test must include
        score2 = evaluator.must_include("world", "hello world!")
        print(f"✓ Must include test: {score2} (expected 1.0)")

        # Test URL evaluator
        url_eval = URLEvaluator()
        print("✓ URL evaluator created")

        return True
    except Exception as e:
        print(f"✗ Evaluator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from lib import ConfigLoader

        config = ConfigLoader()
        print(f"✓ Loaded config from: {config.config_path}")
        print(f"  API endpoint: {config.get_api_endpoint()}")
        print(f"  Timeout: {config.get_timeout()}s")

        # Check judge config
        judge_config = config.get_judge_config()
        print(f"  Judge model: {judge_config['model_name']}")

        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("WebArena Integration Test")
    print("="*70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config_loading()))
    results.append(("Task Loading", test_task_loading()))
    results.append(("Evaluators", test_evaluators()))

    # Print summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)

    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! WebArena integration is ready.")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
