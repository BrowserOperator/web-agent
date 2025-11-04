#!/usr/bin/env python3
"""
List all GitLab tasks from WebArena with their indices.
"""

import json
from pathlib import Path
from collections import Counter


def list_gitlab_tasks(show_all=False):
    """List all GitLab tasks with indices and details."""
    test_raw_file = Path(__file__).parent / 'webarena' / 'config_files' / 'test.raw.json'

    if not test_raw_file.exists():
        print(f"Error: {test_raw_file} not found")
        return

    with open(test_raw_file) as f:
        all_tasks = json.load(f)

    # Filter GitLab tasks
    gitlab_tasks = [t for t in all_tasks if 'gitlab' in t.get('sites', [])]

    # Count by eval type
    eval_type_counts = Counter()
    for task in gitlab_tasks:
        eval_types = task.get('eval', {}).get('eval_types', [])
        eval_type_key = ' + '.join(sorted(eval_types))
        eval_type_counts[eval_type_key] += 1

    print(f"Total GitLab Tasks: {len(gitlab_tasks)}")
    print("=" * 80)
    print()
    print("Evaluation Type Distribution:")
    print("-" * 80)
    for eval_type, count in eval_type_counts.most_common():
        print(f"  {eval_type:40} : {count:3d} tasks ({count*100//len(gitlab_tasks):2d}%)")
    print()
    print("=" * 80)
    print()

    for idx, task in enumerate(gitlab_tasks):
        task_id = task.get('task_id')
        intent = task.get('intent', 'No intent')
        requires_login = task.get('require_login', False)
        eval_types = task.get('eval', {}).get('eval_types', [])
        eval_type_str = ' + '.join(eval_types)

        print(f"[{idx:3d}] Task ID: {task_id:3d}  {'🔒' if requires_login else '  '}  [{eval_type_str}]")
        print(f"      Intent: {intent[:70]}...")
        print()

        # Show first 20, then every 10th, unless show_all is True
        if not show_all and idx >= 20 and (idx + 1) % 10 != 0:
            continue


def main():
    import argparse

    parser = argparse.ArgumentParser(description='List all GitLab tasks from WebArena')
    parser.add_argument('--all', action='store_true',
                       help='Show all tasks (default: show first 20 then every 10th)')

    args = parser.parse_args()
    list_gitlab_tasks(show_all=args.all)


if __name__ == '__main__':
    main()
