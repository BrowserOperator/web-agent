#!/usr/bin/env python3
"""
List all shopping tasks from WebArena with their indices.
"""

import json
from pathlib import Path


def list_shopping_tasks():
    """List all shopping tasks with indices and details."""
    test_raw_file = Path(__file__).parent / 'webarena' / 'config_files' / 'test.raw.json'

    if not test_raw_file.exists():
        print(f"Error: {test_raw_file} not found")
        return

    with open(test_raw_file) as f:
        all_tasks = json.load(f)

    # Filter shopping tasks
    shopping_tasks = [t for t in all_tasks if 'shopping' in t.get('sites', [])]

    print(f"Total Shopping Tasks: {len(shopping_tasks)}")
    print("=" * 80)
    print()

    for idx, task in enumerate(shopping_tasks):
        task_id = task.get('task_id')
        intent = task.get('intent', 'No intent')
        requires_login = task.get('require_login', False)
        start_url = task.get('start_url', '')

        # Extract product name from URL if possible
        url_parts = start_url.replace('__SHOPPING__/', '').split('.html')[0]
        product = url_parts[:60] + '...' if len(url_parts) > 60 else url_parts

        print(f"[{idx:3d}] Task ID: {task_id:3d}  {'🔒' if requires_login else '  '}")
        print(f"      Intent: {intent[:70]}...")
        if product and product != start_url[:60]:
            print(f"      Product: {product}")
        print()

        # Show first 20, then every 10th
        if idx >= 20 and (idx + 1) % 10 != 0:
            continue


if __name__ == '__main__':
    list_shopping_tasks()
