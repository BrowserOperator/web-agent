#!/usr/bin/env python3
"""
Universal Evaluation Runner

Runs evaluations from YAML definitions with flexible execution modes:
- Run specific eval by path: --path action-agent/a11y-001.yaml
- Run all evals in category: --category action-agent
- Run all evals: --all
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add parent directory to path to import from evals/lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import (
    ConfigLoader,
    EvalLoader,
    APIClient,
    LLMJudge,
    VisionJudge,
    Evaluation,
    JudgeResult
)


class EvaluationRunner:
    """Manages evaluation execution and reporting."""

    def __init__(self, config: ConfigLoader, verbose: bool = False):
        """
        Initialize evaluation runner.

        Args:
            config: Configuration loader
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose

        # Initialize components
        self.eval_loader = EvalLoader()
        self.api_client = APIClient(
            base_url=config.get_api_endpoint(),
            timeout=config.get_timeout()
        )

        # Initialize judges
        judge_config = config.get_judge_config()
        self.judge = LLMJudge(
            provider=judge_config['provider'],
            model_name=judge_config['model_name'],
            api_key=judge_config['api_key'],
            temperature=judge_config.get('temperature')
        )
        self.vision_judge = VisionJudge(
            provider=judge_config['provider'],
            model_name=judge_config['model_name'],
            api_key=judge_config['api_key'],
            temperature=judge_config.get('temperature')
        )

        # Get nested model config for API requests
        self.model_config = config.get_nested_model_config()

        # Results tracking
        self.results = []

        # Create screenshots directory
        self.screenshots_dir = Path(__file__).parent / 'screenshots'
        self.screenshots_dir.mkdir(exist_ok=True)

    def run_from_path(self, eval_path: str):
        """
        Run a specific evaluation from a file path.

        Args:
            eval_path: Path to evaluation YAML file (relative to data/ or absolute)
        """
        print(f"\n{'='*70}")
        print(f"Running Evaluation from Path")
        print(f"{'='*70}\n")

        # Check API server health
        print("Checking API server connection...")
        if not self.api_client.check_health():
            print("ERROR: Cannot connect to API server at", self.config.get_api_endpoint())
            print("Please ensure the evaluation server is running.")
            sys.exit(1)
        print("✓ API server is reachable\n")

        # Resolve path
        eval_file = self._resolve_eval_path(eval_path)
        if not eval_file.exists():
            print(f"ERROR: Evaluation file not found: {eval_file}")
            sys.exit(1)

        # Load evaluation
        print(f"Loading evaluation from {eval_path}...")
        import yaml
        with open(eval_file, 'r') as f:
            data = yaml.safe_load(f)

        evaluation = Evaluation(eval_file, data)

        if not evaluation.enabled:
            print(f"WARNING: Evaluation {evaluation.id} is disabled")
            return

        print(f"Found: {evaluation.name} (ID: {evaluation.id})\n")

        # Run evaluation
        try:
            result = self._run_single_evaluation(evaluation)
            self.results.append(result)

            # Print result
            status = "PASS" if result['passed'] else "FAIL"
            print(f"[1/1] Running: {evaluation.name}")
            print(f"  ID: {evaluation.id}")
            print(f"  Status: {status}")
            print(f"  Score: {result['score']:.2f}")
            print(f"  Time: {result['execution_time_ms']}ms")
            print()

        except Exception as e:
            print(f"  ERROR: {str(e)}\n")
            self.results.append({
                'eval_id': evaluation.id,
                'eval_name': evaluation.name,
                'category': evaluation.category,
                'passed': False,
                'score': 0.0,
                'reasoning': f"Execution error: {str(e)}",
                'execution_time_ms': 0,
                'error': str(e)
            })

        # Print summary
        self._print_summary()

        # Save report
        self._save_report(evaluation.category)

    def run_evaluations(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        eval_ids: Optional[List[str]] = None,
        run_all: bool = False
    ):
        """
        Run evaluations for a specific category or all categories.

        Args:
            category: Category name (e.g., 'action-agent'), None for all
            limit: Maximum number of evaluations to run
            eval_ids: Optional list of specific evaluation IDs to run
            run_all: Run all evaluations across all categories
        """
        title = "All Evaluations" if run_all else f"{category} Evaluations"
        print(f"\n{'='*70}")
        print(f"Running {title}")
        print(f"{'='*70}\n")

        # Check API server health
        print("Checking API server connection...")
        if not self.api_client.check_health():
            print("ERROR: Cannot connect to API server at", self.config.get_api_endpoint())
            print("Please ensure the evaluation server is running.")
            sys.exit(1)
        print("✓ API server is reachable\n")

        # Load evaluations
        if run_all:
            print("Loading all evaluations...")
            data_dir = Path(__file__).parent / 'data'
            categories = [d.name for d in data_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            all_evaluations = []
            for cat in categories:
                evals = self.eval_loader.load_from_directory(category=cat, enabled_only=True)
                all_evaluations.extend(evals)
            evaluations = all_evaluations
        else:
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
            msg = "all categories" if run_all else f"category: {category}"
            print(f"No evaluations found in {msg}")
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
                    'category': evaluation.category,
                    'passed': False,
                    'score': 0.0,
                    'reasoning': f"Execution error: {str(e)}",
                    'execution_time_ms': 0,
                    'error': str(e)
                })

        # Print summary
        self._print_summary()

        # Save report
        report_category = 'all' if run_all else category
        self._save_report(report_category)

    def _resolve_eval_path(self, eval_path: str) -> Path:
        """
        Resolve evaluation path to absolute path.

        Args:
            eval_path: Relative or absolute path to eval file

        Returns:
            Absolute Path object
        """
        path = Path(eval_path)

        # If absolute and exists, use it
        if path.is_absolute() and path.exists():
            return path

        # Try relative to data directory
        data_dir = Path(__file__).parent / 'data'
        candidate = data_dir / eval_path
        if candidate.exists():
            return candidate

        # Try as-is (relative to current directory)
        if path.exists():
            return path.resolve()

        # Return the data_dir candidate (will fail with proper error message)
        return candidate

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

        # Verbose: print input
        if self.verbose:
            print(f"\n  Input: {input_message}")

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
                'error': api_response['error'],
                'screenshot_path': None
            }

        # Verbose: print response
        if self.verbose:
            print(f"  Response: {api_response['response'][:200]}{'...' if len(api_response['response']) > 200 else ''}")

        # Capture screenshot if client/tab IDs are available
        screenshot_path = None
        if api_response.get('client_id') and api_response.get('tab_id'):
            screenshot_path = self._capture_screenshot(
                evaluation.id,
                api_response['client_id'],
                api_response['tab_id']
            )

        # Judge the response
        criteria = evaluation.get_validation_criteria()

        # Check if visual verification is required
        if evaluation.requires_vision_judge() and screenshot_path:
            # Use VisionJudge with screenshot
            screenshot_data_url = self._load_screenshot_as_data_url(screenshot_path)
            verification_prompts = evaluation.get_verification_prompts()

            if self.verbose:
                print(f"  Using Vision Judge with screenshot")

            judge_result = self.vision_judge.judge(
                input_prompt=input_message,
                response=api_response['response'],
                criteria=criteria,
                screenshots={"after": screenshot_data_url} if screenshot_data_url else None,
                verification_prompts=verification_prompts if verification_prompts else None
            )
        else:
            # Use standard LLMJudge
            judge_result = self.judge.judge(
                input_prompt=input_message,
                response=api_response['response'],
                criteria=criteria
            )

        # Verbose: print reasoning
        if self.verbose:
            print(f"  Judge Reasoning: {judge_result.reasoning}")
            if screenshot_path:
                print(f"  Screenshot: {screenshot_path}")

        return {
            'eval_id': evaluation.id,
            'eval_name': evaluation.name,
            'category': evaluation.category,
            'passed': judge_result.passed,
            'score': judge_result.score,
            'reasoning': judge_result.reasoning,
            'execution_time_ms': api_response['execution_time_ms'],
            'error': None,
            'screenshot_path': screenshot_path
        }

    def _capture_screenshot(self, eval_id: str, client_id: str, tab_id: str) -> str | None:
        """
        Capture screenshot of the page after evaluation.

        Args:
            eval_id: Evaluation ID for filename
            client_id: Client ID
            tab_id: Tab ID

        Returns:
            Path to saved screenshot or None if failed
        """
        try:
            from datetime import datetime
            import base64

            result = self.api_client.capture_screenshot(client_id, tab_id, full_page=False)

            if result['success'] and result.get('image_data'):
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{eval_id}_{timestamp}.png"
                filepath = self.screenshots_dir / filename

                # Extract base64 data (remove data:image/png;base64, prefix if present)
                image_data = result['image_data']
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',', 1)[1]

                # Save screenshot
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(image_data))

                return str(filepath)

        except Exception as e:
            if self.verbose:
                print(f"  Screenshot capture failed: {e}")

        return None

    def _load_screenshot_as_data_url(self, screenshot_path: str) -> str | None:
        """
        Load a screenshot file and convert it to a base64 data URL.

        Args:
            screenshot_path: Path to the screenshot file

        Returns:
            Data URL string (data:image/png;base64,...) or None if failed
        """
        try:
            import base64

            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                return f"data:image/png;base64,{image_data}"

        except Exception as e:
            if self.verbose:
                print(f"  Screenshot load failed: {e}")
            return None

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
        description="Universal evaluation runner for browser-agent evals",
        epilog="""
Examples:
  # Run specific eval by path
  python3 run.py --path action-agent/a11y-001.yaml

  # Run all evals in a category
  python3 run.py --category action-agent --limit 5

  # Run specific evals by ID
  python3 run.py --category action-agent --eval-ids a11y-001 a11y-002

  # Run all evals across all categories
  python3 run.py --all
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Execution mode (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--path',
        type=str,
        help='Path to specific evaluation YAML file (e.g., action-agent/a11y-001.yaml)'
    )
    mode_group.add_argument(
        '--category',
        type=str,
        help='Run all evaluations in a specific category (e.g., action-agent)'
    )
    mode_group.add_argument(
        '--all',
        action='store_true',
        help='Run all evaluations across all categories'
    )

    # Filtering options (only for category/all modes)
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of evaluations to run (default: all)'
    )
    parser.add_argument(
        '--eval-ids',
        nargs='+',
        help='Specific evaluation IDs to run (only with --category)'
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
        help='Enable verbose output (show input, response, reasoning, screenshots)'
    )

    args = parser.parse_args()

    # Validate argument combinations
    if args.eval_ids and not args.category:
        parser.error("--eval-ids can only be used with --category")

    try:
        # Load configuration
        config = ConfigLoader(config_path=args.config)

        # Create evaluation runner with verbose flag
        runner = EvaluationRunner(config, verbose=args.verbose)

        # Execute based on mode
        if args.path:
            runner.run_from_path(args.path)
        elif args.category:
            # Use limit from config if not specified
            limit = args.limit if args.limit is not None else config.get_default_limit()
            runner.run_evaluations(
                category=args.category,
                limit=limit,
                eval_ids=args.eval_ids
            )
        elif args.all:
            limit = args.limit if args.limit is not None else config.get_default_limit()
            runner.run_evaluations(
                limit=limit,
                run_all=True
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
