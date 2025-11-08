#!/usr/bin/env python3
"""
Live end-to-end test for WebArena integration.
Requires eval-server to be running at http://localhost:8080
"""

import sys
from pathlib import Path

# Add parent directory to path to import from evals/lib
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_api_connection():
    """Test basic API connectivity."""
    print("Testing API connection...")
    from lib import APIClient

    client = APIClient(base_url="http://localhost:8080", timeout=30)

    if client.check_health():
        print("✓ API server is reachable at http://localhost:8080")
        return True
    else:
        print("✗ API server is NOT reachable at http://localhost:8080")
        print("  Please start the eval-server first:")
        print("  cd .. && make compose-up")
        return False


def test_simple_api_request():
    """Test a simple API request."""
    print("\nTesting simple API request...")
    from lib import APIClient, ConfigLoader

    # Load config
    config = ConfigLoader()
    model_config = config.get_nested_model_config()

    # Create client
    client = APIClient(base_url="http://localhost:8080", timeout=60)

    # Send simple request
    print("  Sending: 'What is 2+2?'")
    result = client.send_request(
        input_message="What is 2+2?",
        model_config=model_config,
        url="about:blank",
        wait_timeout=1000
    )

    if result['success']:
        print(f"✓ Got response: {result['response'][:100]}...")
        print(f"  Execution time: {result['execution_time_ms']}ms")
        print(f"  Client ID: {result.get('client_id')}")
        print(f"  Tab ID: {result.get('tab_id')}")
        return True
    else:
        print(f"✗ Request failed: {result['error']}")
        return False


def test_webarena_task():
    """Test running a WebArena task end-to-end."""
    print("\nTesting WebArena Task 2 (public site)...")
    from lib import ConfigLoader, APIClient
    from lib.webarena_adapter import WebArenaTaskLoader, WebArenaExecutor

    # Load config
    config = ConfigLoader()
    model_config = config.get_nested_model_config()
    judge_config = config.get_judge_config()
    openai_api_key = judge_config.get('api_key') if judge_config['provider'] == 'openai' else None

    # Create components
    task_loader = WebArenaTaskLoader()
    api_client = APIClient(base_url="http://localhost:8080", timeout=120)
    executor = WebArenaExecutor(
        api_client=api_client,
        model_config=model_config,
        openai_api_key=openai_api_key
    )

    # Load task 2 (public site)
    try:
        task = task_loader.load_task(2)
        print(f"  Loaded task: {task.intent}")
        print(f"  Start URL: {task.start_url}")
        print(f"  Eval types: {task.eval_types}")
    except FileNotFoundError:
        print("✗ Task 2 not found. Using task 3 instead...")
        task = task_loader.load_task(3)
        print(f"  Loaded task: {task.intent}")
        print(f"  Start URL: {task.start_url}")
        print(f"  Eval types: {task.eval_types}")

    # Execute task
    print("\n  Executing task via eval-server...")
    result = executor.execute_task(task, wait_timeout=10000)

    if result['success']:
        print(f"✓ Task executed successfully!")
        print(f"  Response: {result['response'][:200]}...")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Execution time: {result['execution_time_ms']}ms")
        print(f"  Page URL: {result.get('page_url')}")
        return True
    else:
        print(f"✗ Task execution failed: {result['error']}")
        return False


def main():
    """Run all live tests."""
    print("="*70)
    print("WebArena Live Integration Test")
    print("="*70)
    print("\nThis test requires:")
    print("1. eval-server running at http://localhost:8080")
    print("2. Valid API keys in config.yml")
    print("3. Internet connection (for public site tasks)")
    print()

    results = []

    # Test 1: API connection
    results.append(("API Connection", test_api_connection()))

    if not results[0][1]:
        print("\n" + "="*70)
        print("STOPPED: API server not reachable")
        print("="*70)
        return 1

    # Test 2: Simple API request
    results.append(("Simple API Request", test_simple_api_request()))

    # Test 3: WebArena task execution
    results.append(("WebArena Task Execution", test_webarena_task()))

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
        print("\n✓ All live tests passed! WebArena integration is working end-to-end.")
        return 0
    else:
        print("\n✗ Some tests failed. Check the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
