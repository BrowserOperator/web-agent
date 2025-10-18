"""
API client for communicating with the evaluation server /v1/responses endpoint.
"""

import requests
import time
from typing import Dict, Any, Optional


class APIClient:
    """Client for interacting with /v1/responses API."""

    def __init__(self, base_url: str, timeout: int = 300):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the evaluation server (e.g., http://localhost:8080)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def send_request(
        self,
        input_message: str,
        model_config: Optional[Dict[str, Dict[str, str]]] = None,
        url: Optional[str] = None,
        wait_timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a request to /v1/responses API.

        Args:
            input_message: The input prompt/question for the agent
            model_config: Optional nested model configuration in format:
                {
                    "main_model": {"provider": "...", "model": "...", "api_key": "..."},
                    "mini_model": {"provider": "...", "model": "...", "api_key": "..."},
                    "nano_model": {"provider": "...", "model": "...", "api_key": "..."}
                }
            url: Optional target URL to open the tab at (defaults to about:blank)
            wait_timeout: Optional timeout in milliseconds to wait for page load (defaults to 5000)

        Returns:
            Response dictionary with:
            - success: bool
            - response: str (extracted response text)
            - raw_response: list (raw API response)
            - execution_time_ms: int
            - error: str (if any)

        Raises:
            requests.exceptions.RequestException: On API request failures
        """
        api_url = f"{self.base_url}/v1/responses"

        # Build request payload
        payload = {
            "input": input_message
        }

        if model_config:
            payload["model"] = model_config

        if url:
            payload["url"] = url

        if wait_timeout is not None:
            payload["wait_timeout"] = wait_timeout

        # Track execution time
        start_time = time.time()

        try:
            # Send POST request
            response = requests.post(
                api_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            response_data = response.json()

            # Extract text from OpenAI Responses API format
            response_text = self._extract_response_text(response_data)

            return {
                "success": True,
                "response": response_text,
                "raw_response": response_data,
                "execution_time_ms": execution_time_ms,
                "error": None
            }

        except requests.exceptions.Timeout:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "response": None,
                "raw_response": None,
                "execution_time_ms": execution_time_ms,
                "error": f"Request timed out after {self.timeout} seconds"
            }

        except requests.exceptions.HTTPError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"HTTP error: {e.response.status_code}"
            try:
                error_details = e.response.json()
                error_msg += f" - {error_details.get('error', str(error_details))}"
            except:
                error_msg += f" - {e.response.text[:200]}"

            return {
                "success": False,
                "response": None,
                "raw_response": None,
                "execution_time_ms": execution_time_ms,
                "error": error_msg
            }

        except requests.exceptions.RequestException as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "response": None,
                "raw_response": None,
                "execution_time_ms": execution_time_ms,
                "error": f"Request failed: {str(e)}"
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "response": None,
                "raw_response": None,
                "execution_time_ms": execution_time_ms,
                "error": f"Unexpected error: {str(e)}"
            }

    def _extract_response_text(self, response_data: Any) -> str:
        """
        Extract response text from OpenAI Responses API format.

        Expected format:
        [
          {
            "id": "msg_...",
            "type": "message",
            "role": "assistant",
            "content": [
              {
                "type": "output_text",
                "text": "Response text here",
                "annotations": []
              }
            ]
          }
        ]

        Args:
            response_data: Raw API response

        Returns:
            Extracted response text
        """
        try:
            if isinstance(response_data, list) and len(response_data) > 0:
                message = response_data[0]
                content = message.get('content', [])

                if isinstance(content, list) and len(content) > 0:
                    for item in content:
                        if item.get('type') == 'output_text':
                            return item.get('text', '')

                    # Fallback: return first content item text
                    return content[0].get('text', '')

            # Fallback: convert to string
            return str(response_data)

        except Exception as e:
            return f"[Error extracting response: {e}]"

    def check_health(self) -> bool:
        """
        Check if the API server is healthy.

        Returns:
            True if server is reachable, False otherwise
        """
        try:
            url = f"{self.base_url}/status"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
