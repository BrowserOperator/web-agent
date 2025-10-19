#!/usr/bin/env python3
"""
Test Simple Evaluation Runner

Runs evaluations for test-simple category and generates reports.
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    ConfigLoader,
    EvalLoader,
    APIClient,
    LLMJudge,
    Evaluation,
    JudgeResult
)


class EvaluationRunner:
    """Manages evaluation execution and reporting."""

    def __init__(self, config: ConfigLoader):
        """
        Initialize evaluation runner.

        Args:
            config: Configuration loader
        """
        self.config = config

        # Initialize components
        self.eval_loader = EvalLoader()
        self.api_client = APIClient(
            base_url=config.get_api_endpoint(),
            timeout=config.get_timeout()
        )

        # Initialize judge
        judge_config = config.get_judge_config()
        self.judge = LLMJudge(
            provider=judge_config['provider'],
            model_name=judge_config['model_name'],
            api_key=judge_config['api_key'],
            temperature=judge_config.get('temperature')  # None by default for GPT-5 compatibility
        )

        # Get nested model config for API requests
        self.model_config = config.get_nested_model_config()

        # Results tracking
        self.results = []

    def run_evaluations(
        self,
        category: str,
        limit: int = None,
        eval_ids: List[str] = None
    ):
        """
        Run evaluations for a specific category.

        Args:
            category: Category name (e.g., 'test-simple')
            limit: Maximum number of evaluations to run
            eval_ids: Optional list of specific evaluation IDs to run
        """
        print(f"\n{'='*70}")
        print(f"Running {category} Evaluations")
        print(f"{'='*70}\n")

        # Check API server health
        print("Checking API server connection...")
        if not self.api_client.check_health():
            print("ERROR: Cannot connect to API server at", self.config.get_api_endpoint())
            print("Please ensure the evaluation server is running.")
            sys.exit(1)
        print("✓ API server is reachable\n")

        # Load evaluations
        print(f"Loading evaluations from {category}...")
        evaluations = self.eval_loader.load_from_directory(
            category=category,
            enabled_only=True
        )

        # Filter by eval_ids if specified
        if eval_ids:
            evaluations = [e for e in evaluations if e.id in eval_ids]

        # Apply limit
        if limit:
            evaluations = evaluations[:limit]

        if not evaluations:
            print(f"No evaluations found in category: {category}")
            return

        print(f"Found {len(evaluations)} evaluations to run\n")

        # Run each evaluation
        for i, evaluation in enumerate(evaluations, 1):
            print(f"[{i}/{len(evaluations)}] Running: {evaluation.name}")
            print(f"  ID: {evaluation.id}")

            try:
                result = self._run_single_evaluation(evaluation)
                self.results.append(result)

                # Print result
                status = "PASS" if result['passed'] else "FAIL"
                print(f"  Status: {status}")
                print(f"  Score: {result['score']:.2f}")
                print(f"  Time: {result['execution_time_ms']}ms")
                print()

                # Add delay between requests
                if i < len(evaluations):
                    delay = self.config.get_execution_config().get('request_delay', 1)
                    if delay > 0:
                        time.sleep(delay)

            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Saving partial results...")
                break
            except Exception as e:
                print(f"  ERROR: {str(e)}\n")
                # Record failure
                self.results.append({
                    'eval_id': evaluation.id,
                    'eval_name': evaluation.name,
                    'category': category,
                    'passed': False,
                    'score': 0.0,
                    'reasoning': f"Execution error: {str(e)}",
                    'execution_time_ms': 0,
                    'error': str(e)
                })

        # Print summary
        self._print_summary()

        # Save report
        self._save_report(category)

    def _run_single_evaluation(self, evaluation: Evaluation) -> dict:
        """
        Run a single evaluation.

        Args:
            evaluation: Evaluation to run

        Returns:
            Result dictionary
        """
        # Get input message
        input_message = evaluation.get_input_message()

        # Get target URL and wait timeout
        target_url = evaluation.get_target_url()
        wait_timeout = evaluation.get_wait_timeout()

        # Send API request
        api_response = self.api_client.send_request(
            input_message=input_message,
            model_config=self.model_config,
            url=target_url,
            wait_timeout=wait_timeout
        )

        if not api_response['success']:
            return {
                'eval_id': evaluation.id,
                'eval_name': evaluation.name,
                'category': evaluation.category,
                'passed': False,
                'score': 0.0,
                'reasoning': f"API request failed: {api_response['error']}",
                'execution_time_ms': api_response['execution_time_ms'],
                'error': api_response['error']
            }

        # Judge the response
        criteria = evaluation.get_validation_criteria()
        judge_result = self.judge.judge(
            input_prompt=input_message,
            response=api_response['response'],
            criteria=criteria
        )

        return {
            'eval_id': evaluation.id,
            'eval_name': evaluation.name,
            'category': evaluation.category,
            'passed': judge_result.passed,
            'score': judge_result.score,
            'reasoning': judge_result.reasoning,
            'execution_time_ms': api_response['execution_time_ms'],
            'error': None
        }

    def _print_summary(self):
        """Print summary statistics."""
        if not self.results:
            return

        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total) * 100 if total > 0 else 0
        avg_score = sum(r['score'] for r in self.results) / total if total > 0 else 0
        avg_time = sum(r['execution_time_ms'] for r in self.results) / total if total > 0 else 0

        print(f"\n{'='*70}")
        print("Summary")
        print(f"{'='*70}")
        print(f"Total: {total}")
        print(f"Passed: {passed} ({pass_rate:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Average Score: {avg_score:.2f}")
        print(f"Average Time: {avg_time:.0f}ms")
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
                'eval_id',
                'eval_name',
                'category',
                'status',
                'score',
                'judge_reasoning',
                'execution_time_ms',
                'error'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for result in self.results:
                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'eval_id': result['eval_id'],
                    'eval_name': result['eval_name'],
                    'category': result['category'],
                    'status': 'PASS' if result['passed'] else 'FAIL',
                    'score': f"{result['score']:.2f}",
                    'judge_reasoning': result['reasoning'],
                    'execution_time_ms': result['execution_time_ms'],
                    'error': result.get('error', '')
                })

        print(f"Report saved to: {filepath}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run test-simple evaluations"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of evaluations to run (default: all)'
    )
    parser.add_argument(
        '--eval-ids',
        nargs='+',
        help='Specific evaluation IDs to run'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to config.yml (default: evals/config.yml)'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = ConfigLoader(config_path=args.config)

        # Use limit from config if not specified
        limit = args.limit if args.limit is not None else config.get_default_limit()

        # Create and run evaluation runner
        runner = EvaluationRunner(config)
        runner.run_evaluations(
            category='test-simple',
            limit=limit,
            eval_ids=args.eval_ids
        )

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
