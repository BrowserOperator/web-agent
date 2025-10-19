"""
LLM-as-a-judge implementation for evaluating agent responses.
"""

import json
from typing import Dict, Any, List
from openai import OpenAI


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
        temperature: float = None
    ):
        """
        Initialize LLM judge.

        Args:
            provider: Provider name (currently only "openai" supported)
            model_name: Model name (e.g., "gpt-4")
            api_key: API key for the provider
            temperature: Sampling temperature (optional, None uses model default)
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature

        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
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
        temperature: float = None
    ):
        """
        Initialize Vision judge.

        Args:
            provider: Provider name (currently only "openai" supported)
            model_name: Model name (e.g., "gpt-4o", "gpt-4-vision-preview")
            api_key: API key for the provider
            temperature: Sampling temperature (optional, None uses model default)
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature

        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
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
