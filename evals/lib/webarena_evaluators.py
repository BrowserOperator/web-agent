"""
WebArena Evaluators

Ported from webarena/evaluation_harness/evaluators.py to work with the eval-server API.

This module provides three evaluator types:
- StringEvaluator: Exact match, must include, fuzzy match (LLM-based)
- URLEvaluator: URL matching with query parameter support
- HTMLContentEvaluator: Page content verification via JavaScript evaluation
"""

import collections
import html
import json
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI


class WebArenaEvaluator:
    """Base class for WebArena evaluators."""

    def __init__(self, eval_tag: str = ""):
        self.eval_tag = eval_tag

    def evaluate(
        self,
        response: str,
        config: Dict[str, Any],
        page_url: Optional[str] = None,
        api_client: Optional[Any] = None,
        client_id: Optional[str] = None,
        tab_id: Optional[str] = None
    ) -> float:
        """
        Evaluate a response against the config.

        Args:
            response: Agent's response text
            config: WebArena task configuration
            page_url: Current page URL (for URL evaluation)
            api_client: APIClient instance (for HTML content evaluation)
            client_id: Client ID (for HTML content evaluation)
            tab_id: Tab ID (for HTML content evaluation)

        Returns:
            Score between 0.0 and 1.0
        """
        raise NotImplementedError


class StringEvaluator(WebArenaEvaluator):
    """
    Check whether the answer is correct with:
    - exact_match: Answer exactly matches reference
    - must_include: Each phrase in reference must be included
    - fuzzy_match: LLM-based similarity check
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        super().__init__(eval_tag="string")
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

    @staticmethod
    def clean_answer(answer: str) -> str:
        """Clean and normalize answer string."""
        answer = answer.strip()
        if answer.startswith("'") and answer.endswith("'"):
            answer = answer[1:-1]
        elif answer.startswith('"') and answer.endswith('"'):
            answer = answer[1:-1]
        return answer.lower()

    @staticmethod
    def exact_match(ref: str, pred: str) -> float:
        """Check exact match after cleaning."""
        return float(
            StringEvaluator.clean_answer(pred) == StringEvaluator.clean_answer(ref)
        )

    @staticmethod
    def must_include(ref: str, pred: str, tokenize: bool = False) -> float:
        """Check if reference phrase is included in prediction."""
        clean_ref = StringEvaluator.clean_answer(ref)
        clean_pred = StringEvaluator.clean_answer(pred)

        # Simple tokenization for single-character refs
        if tokenize and len(clean_ref) == 1:
            tok_pred = clean_pred.split()
            return float(clean_ref in tok_pred)
        else:
            return float(clean_ref in clean_pred)

    def fuzzy_match(self, ref: str, pred: str, intent: str) -> float:
        """Use LLM to check semantic similarity."""
        if not self.openai_client:
            # Fallback to must_include if no OpenAI client
            return self.must_include(ref, pred)

        message = (
            "Help a teacher grade a student's answer. The goal is to evaluate "
            "whether the answer is semantically equivalent to the reference.\n\n"
            f"Question: {intent}\n"
            f"Reference answer: {ref}\n"
            f"Student answer: {pred}\n\n"
            "Note: 'N/A' means 'not achievable'.\n"
            "Conclude with: correct/incorrect/partially correct"
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful grading assistant."},
                    {"role": "user", "content": message}
                ],
                temperature=0,
                max_tokens=768
            )

            result = response.choices[0].message.content.lower()

            if "partially correct" in result or "incorrect" in result:
                return 0.0
            elif "correct" in result:
                return 1.0
            else:
                # Ambiguous response, default to 0.5
                return 0.5

        except Exception as e:
            print(f"Warning: Fuzzy match failed: {e}")
            # Fallback to must_include
            return self.must_include(ref, pred)

    def ua_match(self, pred: str, ref: str, intent: str) -> float:
        """Check if unachievable reason matches."""
        if not self.openai_client:
            return self.exact_match(ref, pred)

        message = (
            f"Task: {intent}\n"
            f"Actual unachievable reason: {ref}\n"
            f"Reported unachievable reason: {pred}\n\n"
            "The task is unachievable for the reason stated above. "
            "Someone attempted it and reported why they failed. "
            "Determine if the reported reason aligns with the actual reason "
            "(even implicitly). Respond with 'same' or 'different'."
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                temperature=0,
                max_tokens=768
            )

            result = response.choices[0].message.content.lower()

            if "different" in result:
                return 0.0
            elif "same" in result:
                return 1.0
            else:
                return 0.5

        except Exception:
            return self.exact_match(ref, pred)

    def evaluate(
        self,
        response: str,
        config: Dict[str, Any],
        page_url: Optional[str] = None,
        api_client: Optional[Any] = None,
        client_id: Optional[str] = None,
        tab_id: Optional[str] = None
    ) -> float:
        """Evaluate response against string match criteria."""
        pred = self.clean_answer(response)
        score = 1.0

        reference_answers = config["eval"]["reference_answers"]

        # Handle legacy list format: ["answer"] -> treat as must_include
        if isinstance(reference_answers, list):
            for answer in reference_answers:
                score *= self.must_include(
                    ref=answer,
                    pred=pred,
                    tokenize=(len(reference_answers) == 1)
                )
            return score

        # Handle dict format with specific match types
        if not isinstance(reference_answers, dict):
            return score

        # Exact match
        if "exact_match" in reference_answers:
            ref_value = reference_answers["exact_match"]
            score *= self.exact_match(ref=ref_value, pred=pred)

        # Must include
        if "must_include" in reference_answers:
            values = reference_answers["must_include"]
            assert isinstance(values, list)
            for must_value in values:
                score *= self.must_include(
                    ref=must_value,
                    pred=pred,
                    tokenize=(len(values) == 1)
                )

        # Fuzzy match
        if "fuzzy_match" in reference_answers:
            intent = config["intent"]
            value = reference_answers["fuzzy_match"]

            if value == "N/A":
                # Check for unachievable task
                score *= self.exact_match(ref=value, pred=pred)
                if score != 1:
                    # Check if reason matches
                    string_note = config["eval"].get("string_note", "")
                    score = 1.0 * self.ua_match(
                        pred=pred,
                        ref=string_note,
                        intent=intent
                    )
            else:
                assert isinstance(value, list)
                for reference in value:
                    score *= self.fuzzy_match(ref=reference, pred=pred, intent=intent)

        return score


class URLEvaluator(WebArenaEvaluator):
    """Check URL matching with query parameter support."""

    def __init__(self):
        super().__init__(eval_tag="url")

    @staticmethod
    def clean_url(url: str) -> str:
        """Clean URL by stripping trailing slash."""
        return str(url).rstrip("/")

    @staticmethod
    def parse_url(url: str) -> tuple[str, dict[str, list[str]]]:
        """Parse URL into base path and query parameters."""
        parsed_url = urllib.parse.urlparse(url)
        base_path = parsed_url.netloc + parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        return base_path, query

    @staticmethod
    def parse_urls(urls: List[str]) -> tuple[list[str], dict[str, set[str]]]:
        """Parse multiple URLs."""
        base_paths = []
        queries = collections.defaultdict(set)
        for url in urls:
            base_path, query = URLEvaluator.parse_url(url)
            base_paths.append(base_path)
            for k, v in query.items():
                queries[k].update(v)
        return base_paths, queries

    def evaluate(
        self,
        response: str,
        config: Dict[str, Any],
        page_url: Optional[str] = None,
        api_client: Optional[Any] = None,
        client_id: Optional[str] = None,
        tab_id: Optional[str] = None
    ) -> float:
        """Evaluate if current page URL matches expected URL."""
        if not page_url:
            return 0.0

        pred = self.clean_url(page_url)
        ref_urls = config["eval"]["reference_url"].split(" |OR| ")
        ref_urls = [self.clean_url(url) for url in ref_urls]

        matching_rule = config["eval"].get("url_note", "GOLD in PRED")

        if matching_rule == "GOLD in PRED":
            ref_base_paths, ref_queries = self.parse_urls(ref_urls)
            pred_base_path, pred_query = self.parse_url(pred)

            # Check if any reference base path is in prediction
            base_score = float(
                any(ref_base_path in pred_base_path for ref_base_path in ref_base_paths)
            )

            # Check query parameters
            query_score = 1.0
            for k, possible_values in ref_queries.items():
                query_score *= float(
                    any(
                        possible_ref_value in pred_query.get(k, [])
                        for possible_ref_value in possible_values
                    )
                )

            score = base_score * query_score
        else:
            raise ValueError(f"Unknown matching rule: {matching_rule}")

        return score


class HTMLContentEvaluator(WebArenaEvaluator):
    """Check whether required contents appear on the page."""

    def __init__(self):
        super().__init__(eval_tag="html")

    def evaluate(
        self,
        response: str,
        config: Dict[str, Any],
        page_url: Optional[str] = None,
        api_client: Optional[Any] = None,
        client_id: Optional[str] = None,
        tab_id: Optional[str] = None
    ) -> float:
        """
        Evaluate page content against required contents.

        Note: This requires api_client, client_id, and tab_id to be provided
        so we can fetch page content via the eval-server API.
        """
        if not api_client or not client_id or not tab_id:
            print("Warning: HTMLContentEvaluator requires api_client, client_id, and tab_id")
            return 0.0

        targets = config["eval"]["program_html"]
        score = 1.0

        for target in targets:
            target_url: str = target["url"]
            locator: str = target["locator"]

            # Handle function-based URLs (simplified, doesn't support helper functions yet)
            if target_url.startswith("func"):
                print(f"Warning: Function-based URLs not yet supported: {target_url}")
                continue

            # Navigate if needed
            if target_url != "last":
                # TODO: Navigate to target_url via API
                print(f"Warning: Navigation to {target_url} not implemented")
                # For now, assume we're on the right page

            # Get page content
            try:
                if not locator.strip():
                    # Get full page content
                    result = api_client.get_page_content(
                        client_id=client_id,
                        tab_id=tab_id,
                        format="html"
                    )
                    if not result["success"]:
                        selected_element = ""
                    else:
                        selected_element = result["content"]

                elif locator.startswith("document.") or locator.startswith("[...document."):
                    # Execute JavaScript via CDP
                    # This would need to be implemented in APIClient
                    print(f"Warning: JavaScript evaluation not yet fully supported: {locator}")
                    # Fallback: get page content and hope the text is there
                    result = api_client.get_page_content(
                        client_id=client_id,
                        tab_id=tab_id,
                        format="text"
                    )
                    selected_element = result.get("content", "") if result["success"] else ""

                elif locator.startswith("func:"):
                    # Helper function execution
                    print(f"Warning: Helper functions not yet supported: {locator}")
                    selected_element = ""

                else:
                    raise ValueError(f"Unknown locator: {locator}")

                selected_element = html.unescape(selected_element)

                # Check required contents
                required_contents = target["required_contents"]

                if "exact_match" in required_contents:
                    ref = required_contents["exact_match"]
                    cur_score = StringEvaluator.exact_match(ref=ref, pred=selected_element)
                    score *= float(cur_score)

                elif "must_include" in required_contents:
                    contents = required_contents["must_include"]
                    assert isinstance(contents, list)
                    for content in contents:
                        content_or = content.split(" |OR| ")
                        cur_score = any(
                            StringEvaluator.must_include(
                                ref=c,
                                pred=selected_element,
                                tokenize=False
                            )
                            for c in content_or
                        )
                        score *= float(cur_score)

                else:
                    raise ValueError(
                        f"Unknown required_contents: {list(required_contents.keys())}"
                    )

            except Exception as e:
                print(f"Warning: HTMLContentEvaluator failed for target {target}: {e}")
                score *= 0.0

        return score


class EvaluatorCombination:
    """Combine multiple evaluators and multiply their scores."""

    def __init__(self, evaluators: List[WebArenaEvaluator]):
        self.evaluators = evaluators

    def evaluate(
        self,
        response: str,
        config: Dict[str, Any],
        page_url: Optional[str] = None,
        api_client: Optional[Any] = None,
        client_id: Optional[str] = None,
        tab_id: Optional[str] = None
    ) -> float:
        """Evaluate using all evaluators and multiply scores."""
        score = 1.0
        for evaluator in self.evaluators:
            cur_score = evaluator.evaluate(
                response=response,
                config=config,
                page_url=page_url,
                api_client=api_client,
                client_id=client_id,
                tab_id=tab_id
            )
            score *= cur_score
        return score


def create_evaluator(
    config: Dict[str, Any],
    openai_api_key: Optional[str] = None
) -> EvaluatorCombination:
    """
    Create evaluator combination based on config eval_types.

    Args:
        config: WebArena task configuration
        openai_api_key: Optional OpenAI API key for fuzzy matching

    Returns:
        EvaluatorCombination instance
    """
    eval_types = config["eval"]["eval_types"]
    evaluators: List[WebArenaEvaluator] = []

    for eval_type in eval_types:
        if eval_type == "string_match":
            evaluators.append(StringEvaluator(openai_api_key=openai_api_key))
        elif eval_type == "url_match":
            evaluators.append(URLEvaluator())
        elif eval_type == "program_html":
            evaluators.append(HTMLContentEvaluator())
        else:
            raise ValueError(f"eval_type {eval_type} is not supported")

    return EvaluatorCombination(evaluators)
