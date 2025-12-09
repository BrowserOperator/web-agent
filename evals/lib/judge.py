"""
LLM-as-a-judge implementation for evaluating agent responses.
"""

import json
from typing import Dict, Any, List
from openai import OpenAI


# Provider default endpoints (OpenAI-compatible APIs)
PROVIDER_ENDPOINTS = {
    "cerebras": "https://api.cerebras.ai/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai"
}


class JudgeResult:
    """Result of judging an evaluation."""

    def __init__(
        self,
        passed: bool,
        score: float,
        reasoning: str,
        criteria_results: Dict[str, bool] = None
    ):
        """
        Initialize judge result.

        Args:
            passed: Whether the evaluation passed
            score: Numerical score (0-1)
            reasoning: Explanation of the judgment
            criteria_results: Dict mapping criterion to pass/fail
        """
        self.passed = passed
        self.score = score
        self.reasoning = reasoning
        self.criteria_results = criteria_results or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "passed": self.passed,
            "score": self.score,
            "reasoning": self.reasoning,
            "criteria_results": self.criteria_results
        }


class LLMJudge:
    """LLM-based judge for evaluating agent responses."""

    def __init__(
        self,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = None,
        endpoint: str = None
    ):
        """
        Initialize LLM judge.

        Args:
            provider: Provider name ("openai", "litellm", "cerebras", "anthropic", "google", etc.)
            model_name: Model name (e.g., "gpt-4", "qwen3:14b-q8_0")
            api_key: API key for the provider
            temperature: Sampling temperature (optional, None uses model default)
            endpoint: Custom endpoint URL (optional, for LiteLLM or custom deployments)
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.endpoint = endpoint

        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif provider == "litellm":
            # LiteLLM uses OpenAI-compatible API
            if not endpoint:
                raise ValueError("LiteLLM provider requires 'endpoint' parameter")
            self.client = OpenAI(api_key=api_key, base_url=endpoint)
        elif provider in PROVIDER_ENDPOINTS:
            # Providers with known OpenAI-compatible endpoints (cerebras, anthropic, google)
            base_url = endpoint or PROVIDER_ENDPOINTS[provider]
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            # Try to initialize with custom endpoint if provided
            if endpoint:
                self.client = OpenAI(api_key=api_key, base_url=endpoint)
            else:
                raise ValueError(f"Unsupported judge provider: {provider}")

    def judge(
        self,
        input_prompt: str,
        response: str,
        criteria: List[str]
    ) -> JudgeResult:
        """
        Judge a response against evaluation criteria.

        Args:
            input_prompt: The original input/prompt sent to the agent
            response: The agent's response to evaluate
            criteria: List of criteria strings to evaluate against

        Returns:
            JudgeResult with pass/fail, score, and reasoning
        """
        # Build judgment prompt
        judge_prompt = self._build_judge_prompt(input_prompt, response, criteria)

        try:
            # Build API call parameters
            call_params = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert evaluator assessing AI agent responses. "
                                   "Provide objective, detailed assessments based on the given criteria."
                    },
                    {
                        "role": "user",
                        "content": judge_prompt
                    }
                ],
                "response_format": {"type": "json_object"}
            }

            # Only add temperature if it's specified
            if self.temperature is not None:
                call_params["temperature"] = self.temperature

            # Call LLM to judge
            completion = self.client.chat.completions.create(**call_params)

            # Parse response
            result_text = completion.choices[0].message.content
            result_data = json.loads(result_text)

            # Extract fields
            passed = result_data.get("passed", False)
            score = result_data.get("score", 0.0)
            reasoning = result_data.get("reasoning", "")
            criteria_results = result_data.get("criteria_results", {})

            return JudgeResult(
                passed=passed,
                score=score,
                reasoning=reasoning,
                criteria_results=criteria_results
            )

        except Exception as e:
            # Return failure result on error
            return JudgeResult(
                passed=False,
                score=0.0,
                reasoning=f"Judge evaluation failed: {str(e)}",
                criteria_results={}
            )

    def _build_judge_prompt(
        self,
        input_prompt: str,
        response: str,
        criteria: List[str]
    ) -> str:
        """
        Build the judgment prompt for the LLM.

        Args:
            input_prompt: Original input
            response: Agent's response
            criteria: List of evaluation criteria

        Returns:
            Formatted prompt string
        """
        criteria_list = "\n".join([f"{i+1}. {c}" for i, c in enumerate(criteria)])

        prompt = f"""Evaluate the following AI agent response against the specified criteria.

## Original Input/Task
{input_prompt}

## Agent's Response
{response}

## Evaluation Criteria
{criteria_list}

## Your Task
Evaluate whether the agent's response satisfies each criterion. Provide your assessment in JSON format with the following structure:

{{
  "passed": true/false,  // Overall pass/fail
  "score": 0.0-1.0,     // Numerical score (0=complete failure, 1=perfect)
  "reasoning": "Detailed explanation of your assessment",
  "criteria_results": {{
    "Criterion 1 text": true/false,
    "Criterion 2 text": true/false,
    ...
  }}
}}

Be strict but fair in your evaluation. A response should only pass if it genuinely satisfies the criteria.
"""
        return prompt


class VisionJudge:
    """Vision-capable LLM judge for evaluating agent responses with screenshots."""

    def __init__(
        self,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = None,
        endpoint: str = None
    ):
        """
        Initialize Vision judge.

        Args:
            provider: Provider name ("openai", "litellm", "cerebras", "anthropic", "google", etc.)
            model_name: Model name (e.g., "gpt-4o", "gpt-4-vision-preview", "qwen3:14b-q8_0")
            api_key: API key for the provider
            temperature: Sampling temperature (optional, None uses model default)
            endpoint: Custom endpoint URL (optional, for LiteLLM or custom deployments)
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.endpoint = endpoint

        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif provider == "litellm":
            # LiteLLM uses OpenAI-compatible API
            if not endpoint:
                raise ValueError("LiteLLM provider requires 'endpoint' parameter")
            self.client = OpenAI(api_key=api_key, base_url=endpoint)
        elif provider in PROVIDER_ENDPOINTS:
            # Providers with known OpenAI-compatible endpoints (cerebras, anthropic, google)
            base_url = endpoint or PROVIDER_ENDPOINTS[provider]
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            # Try to initialize with custom endpoint if provided
            if endpoint:
                self.client = OpenAI(api_key=api_key, base_url=endpoint)
            else:
                raise ValueError(f"Unsupported judge provider: {provider}")

    def judge(
        self,
        input_prompt: str,
        response: str,
        criteria: List[str],
        screenshots: Dict[str, str] = None,
        verification_prompts: List[str] = None
    ) -> JudgeResult:
        """
        Judge a response against evaluation criteria with visual verification.

        Args:
            input_prompt: The original input/prompt sent to the agent
            response: The agent's response to evaluate
            criteria: List of criteria strings to evaluate against
            screenshots: Dict with 'before' and/or 'after' screenshot base64 data URLs
            verification_prompts: Optional list of visual verification prompts

        Returns:
            JudgeResult with pass/fail, score, and reasoning
        """
        # Build judgment prompt
        judge_prompt = self._build_judge_prompt(
            input_prompt,
            response,
            criteria,
            verification_prompts or []
        )

        # Build message content with text and images
        content = [{"type": "text", "text": judge_prompt}]

        # Add screenshots if provided
        if screenshots:
            if screenshots.get("before"):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": screenshots["before"], "detail": "auto"}
                })
                content.append({
                    "type": "text",
                    "text": "BEFORE Screenshot: The page state before the agent action"
                })

            if screenshots.get("after"):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": screenshots["after"], "detail": "auto"}
                })
                content.append({
                    "type": "text",
                    "text": "AFTER Screenshot: The page state after the agent action"
                })

        try:
            # Build API call parameters
            call_params = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert evaluator assessing AI agent responses with visual verification capabilities. "
                                   "Analyze both text responses and screenshots to provide objective, detailed assessments based on the given criteria."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "response_format": {"type": "json_object"}
            }

            # Only add temperature if it's specified
            if self.temperature is not None:
                call_params["temperature"] = self.temperature

            # Call LLM to judge
            completion = self.client.chat.completions.create(**call_params)

            # Parse response
            result_text = completion.choices[0].message.content
            result_data = json.loads(result_text)

            # Extract fields
            passed = result_data.get("passed", False)
            score = result_data.get("score", 0.0)
            reasoning = result_data.get("reasoning", "")
            criteria_results = result_data.get("criteria_results", {})

            return JudgeResult(
                passed=passed,
                score=score,
                reasoning=reasoning,
                criteria_results=criteria_results
            )

        except Exception as e:
            # Return failure result on error
            return JudgeResult(
                passed=False,
                score=0.0,
                reasoning=f"Vision judge evaluation failed: {str(e)}",
                criteria_results={}
            )

    def _build_judge_prompt(
        self,
        input_prompt: str,
        response: str,
        criteria: List[str],
        verification_prompts: List[str]
    ) -> str:
        """
        Build the judgment prompt for the vision LLM.

        Args:
            input_prompt: Original input
            response: Agent's response
            criteria: List of evaluation criteria
            verification_prompts: List of visual verification prompts

        Returns:
            Formatted prompt string
        """
        criteria_list = "\n".join([f"{i+1}. {c}" for i, c in enumerate(criteria)])

        prompt = f"""Evaluate the following AI agent response against the specified criteria.

## Original Input/Task
{input_prompt}

## Agent's Response
{response}
"""

        # Add visual verification prompts if provided
        if verification_prompts:
            verification_list = "\n".join([f"{i+1}. {p}" for i, p in enumerate(verification_prompts)])
            prompt += f"""
## Visual Verification Prompts
{verification_list}
"""

        prompt += f"""
## Evaluation Criteria
{criteria_list}

## Your Task
Evaluate whether the agent's response satisfies each criterion. Use the screenshots (if provided) to verify the visual state of the page before and after the agent's action. Provide your assessment in JSON format with the following structure:

{{
  "passed": true/false,  // Overall pass/fail
  "score": 0.0-1.0,     // Numerical score (0=complete failure, 1=perfect)
  "reasoning": "Detailed explanation of your assessment including visual analysis",
  "criteria_results": {{
    "Criterion 1 text": true/false,
    "Criterion 2 text": true/false,
    ...
  }}
}}

Be strict but fair in your evaluation. A response should only pass if it genuinely satisfies the criteria.
"""
        return prompt


class SimpleJudge:
    """Simple keyword-based judge for basic evaluations (fallback)."""

    def judge(
        self,
        input_prompt: str,
        response: str,
        criteria: List[str]
    ) -> JudgeResult:
        """
        Simple keyword-based judgment.

        Args:
            input_prompt: Original input
            response: Agent's response
            criteria: List of criteria (used as keywords)

        Returns:
            JudgeResult
        """
        if not response:
            return JudgeResult(
                passed=False,
                score=0.0,
                reasoning="No response provided",
                criteria_results={}
            )

        # Check if response contains keywords from criteria
        response_lower = response.lower()
        matches = 0
        total = len(criteria)

        criteria_results = {}
        for criterion in criteria:
            # Extract key terms from criterion
            words = criterion.lower().split()
            # Check if any significant words appear in response
            matched = any(word in response_lower for word in words if len(word) > 4)
            criteria_results[criterion] = matched
            if matched:
                matches += 1

        score = matches / total if total > 0 else 0.0
        passed = score >= 0.7  # 70% threshold

        return JudgeResult(
            passed=passed,
            score=score,
            reasoning=f"Keyword matching: {matches}/{total} criteria matched",
            criteria_results=criteria_results
        )


class JSEvalJudge:
    """JavaScript evaluation-based judge for deterministic validation."""

    def __init__(self, api_client, client_id: str, tab_id: str):
        """
        Initialize JS Eval judge.

        Args:
            api_client: APIClient instance for executing JavaScript
            client_id: Client ID for the browser tab
            tab_id: Tab ID for the browser tab
        """
        self.api_client = api_client
        self.client_id = client_id
        self.tab_id = tab_id

    def judge(
        self,
        script: str,
        expected_result: Any,
        timeout: int = 5000
    ) -> JudgeResult:
        """
        Judge by executing JavaScript and comparing with expected result.

        Args:
            script: JavaScript code to execute
            expected_result: Expected result to compare against
            timeout: Timeout in milliseconds (not used currently, for future)

        Returns:
            JudgeResult with pass/fail based on comparison
        """
        try:
            # Execute JavaScript
            result = self.api_client.execute_javascript(
                client_id=self.client_id,
                tab_id=self.tab_id,
                expression=script,
                return_by_value=True,
                await_promise=False
            )

            if not result["success"]:
                return JudgeResult(
                    passed=False,
                    score=0.0,
                    reasoning=f"JavaScript execution failed: {result.get('error', 'Unknown error')}",
                    criteria_results={}
                )

            # Check for exceptions
            if result.get("exceptionDetails"):
                return JudgeResult(
                    passed=False,
                    score=0.0,
                    reasoning=f"JavaScript threw exception: {result['exceptionDetails']}",
                    criteria_results={}
                )

            # Get the actual result
            actual_result = result["result"]

            # Compare with expected result
            passed = self._compare_results(actual_result, expected_result)

            if passed:
                reasoning = f"✓ JavaScript validation passed\n"
                reasoning += f"  Script: {script[:100]}{'...' if len(script) > 100 else ''}\n"
                reasoning += f"  Expected: {expected_result}\n"
                reasoning += f"  Actual: {actual_result}\n"
                reasoning += f"  Match: True"
                score = 1.0
            else:
                reasoning = f"✗ JavaScript validation failed\n"
                reasoning += f"  Script: {script[:100]}{'...' if len(script) > 100 else ''}\n"
                reasoning += f"  Expected: {expected_result}\n"
                reasoning += f"  Actual: {actual_result}\n"
                reasoning += f"  Match: False"
                score = 0.0

            return JudgeResult(
                passed=passed,
                score=score,
                reasoning=reasoning,
                criteria_results={"javascript_match": passed}
            )

        except Exception as e:
            return JudgeResult(
                passed=False,
                score=0.0,
                reasoning=f"JS Eval judge failed: {str(e)}",
                criteria_results={}
            )

    def _compare_results(self, actual, expected) -> bool:
        """
        Compare actual and expected results with type-aware logic.

        Args:
            actual: Actual result from JavaScript execution
            expected: Expected result from configuration

        Returns:
            True if results match, False otherwise
        """
        # Handle None/null
        if actual is None and expected is None:
            return True
        if actual is None or expected is None:
            return False

        # Handle boolean comparison
        if isinstance(expected, bool):
            # Convert actual to boolean for comparison
            return bool(actual) == expected

        # Handle string comparison (case-sensitive)
        if isinstance(expected, str):
            return str(actual) == expected

        # Handle numeric comparison
        if isinstance(expected, (int, float)):
            try:
                return float(actual) == float(expected)
            except (ValueError, TypeError):
                return False

        # Handle list/array comparison
        if isinstance(expected, list):
            if not isinstance(actual, list):
                return False
            if len(actual) != len(expected):
                return False
            return all(self._compare_results(a, e) for a, e in zip(actual, expected))

        # Handle dict/object comparison
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return False
            if set(actual.keys()) != set(expected.keys()):
                return False
            return all(self._compare_results(actual[k], expected[k]) for k in expected.keys())

        # Default: direct equality
        return actual == expected
