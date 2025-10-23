#!/usr/bin/env python3
"""
Test script for VisionJudge functionality.
"""

import os
from lib.judge import VisionJudge, JudgeResult
from lib.api_client import APIClient

def test_vision_judge_creation():
    """Test that VisionJudge can be created."""
    print("Testing VisionJudge creation...")

    # Create judge with dummy API key (won't actually call API in this test)
    judge = VisionJudge(
        provider="openai",
        model_name="gpt-4o",
        api_key="test-key-12345"
    )

    print("✅ VisionJudge created successfully")
    print(f"   Provider: {judge.provider}")
    print(f"   Model: {judge.model_name}")
    return judge

def test_api_client_methods():
    """Test that APIClient has screenshot methods."""
    print("\nTesting APIClient methods...")

    client = APIClient("http://localhost:8081")

    # Check methods exist
    assert hasattr(client, 'capture_screenshot'), "Missing capture_screenshot method"
    assert hasattr(client, 'get_page_content'), "Missing get_page_content method"

    print("✅ APIClient has required methods:")
    print("   - capture_screenshot(client_id, tab_id, full_page)")
    print("   - get_page_content(client_id, tab_id, format)")

def test_vision_judge_signature():
    """Test VisionJudge.judge() method signature."""
    print("\nTesting VisionJudge.judge() signature...")

    # Get method signature
    import inspect
    judge = VisionJudge(provider="openai", model_name="gpt-4o", api_key="test")
    sig = inspect.signature(judge.judge)

    params = list(sig.parameters.keys())
    print(f"✅ VisionJudge.judge() parameters: {params}")

    # Verify expected parameters
    assert 'input_prompt' in params
    assert 'response' in params
    assert 'criteria' in params
    assert 'screenshots' in params
    assert 'verification_prompts' in params

    print("   All expected parameters present:")
    print("   - input_prompt: str")
    print("   - response: str")
    print("   - criteria: List[str]")
    print("   - screenshots: Dict[str, str] = None")
    print("   - verification_prompts: List[str] = None")

if __name__ == "__main__":
    print("=" * 60)
    print("Vision Judge Implementation Test")
    print("=" * 60)

    try:
        test_vision_judge_creation()
        test_api_client_methods()
        test_vision_judge_signature()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nNext steps to test with real API:")
        print("1. Start eval-server: cd ../eval-server/nodejs && npm start")
        print("2. Start browser with CDP: chromium --remote-debugging-port=9223")
        print("3. Connect an agent to eval-server")
        print("4. Use APIClient.capture_screenshot() to get screenshots")
        print("5. Use VisionJudge.judge() with screenshots for evaluation")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
