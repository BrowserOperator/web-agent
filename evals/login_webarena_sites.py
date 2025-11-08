#!/usr/bin/env python3
"""
Login to WebArena sites using BrowserOperator.

This script uses the BrowserOperator API to login to WebArena sites.
Once logged in, the browser session persists, so subsequent tasks will
automatically be authenticated.

No need to capture/inject cookies - the browser maintains the session!
"""

import time
from typing import Dict, Any

from lib.api_client import APIClient
from lib.config_loader import ConfigLoader

# WebArena accounts from browser_env/env_config.py
ACCOUNTS = {
    'shopping': {
        'url': 'http://onestopmarket.com/customer/account/login/',
        'username': 'emma.lopez@gmail.com',
        'password': 'Password.123',
        'task': 'Navigate to http://onestopmarket.com/customer/account/login/. Fill in the email field with "emma.lopez@gmail.com". Fill in the password field with "Password.123". Click the "Sign In" button. Wait for the page to load.',
    },
    'shopping_admin': {
        'url': 'http://onestopmarket.com/admin',
        'username': 'admin',
        'password': 'admin1234',
        'task': 'Navigate to http://onestopmarket.com/admin. Fill in the username field with "admin". Fill in the password field with "admin1234". Click the "Sign in" button. Wait for the page to load.',
    },
    'gitlab': {
        'url': 'http://gitlab.com/users/sign_in',
        'username': 'byteblaze',
        'password': 'hello1234',
        'task': 'Navigate to http://gitlab.com/users/sign_in. Fill in the username field with "byteblaze". Fill in the password field with "hello1234". Click the "Sign in" button. Wait for the page to load.',
    },
    # Reddit and Wikipedia not functioning yet
    # 'reddit': {
    #     'url': 'http://reddit.com/login',
    #     'username': 'MarvelsGrantMan136',
    #     'password': 'test1234',
    #     'task': 'Navigate to http://reddit.com/login. Fill in the username field with "MarvelsGrantMan136". Fill in the password field with "test1234". Click the "Log in" button. Wait for the page to load.',
    # },
}


def login_to_site(
    site_name: str,
    config: Dict[str, Any],
    api_client: APIClient,
    model_config: Dict[str, Dict[str, str]]
) -> bool:
    """
    Login to a specific WebArena site.

    Args:
        site_name: Name of the site (e.g., 'shopping')
        config: Site configuration dict
        api_client: APIClient instance
        model_config: Model configuration for API requests

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"Logging in to: {site_name}")
    print(f"{'='*70}")

    url = config['url']
    task = config['task']

    print(f"URL: {url}")
    print(f"Username: {config['username']}")
    print(f"Password: {'*' * len(config['password'])}")
    print(f"\nTask: {task}")

    try:
        print(f"\nSending login task to BrowserOperator...")
        response = api_client.send_request(
            input_message=task,
            model_config=model_config,
            url=url,
            wait_timeout=60000  # 60 seconds
        )

        if not response['success']:
            print(f"❌ Login failed: {response.get('error', 'Unknown error')}")
            return False

        print(f"✅ Login completed")
        print(f"   Response: {response['response'][:200]}...")
        print(f"   Time: {response['execution_time_ms']}ms")

        return True

    except Exception as e:
        print(f"\n❌ Error logging in to {site_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    print("="*70)
    print("WebArena Site Login via BrowserOperator")
    print("="*70)
    print("\nThis script logs into WebArena sites using BrowserOperator.")
    print("The browser session persists, so subsequent tasks will be")
    print("automatically authenticated - no need to capture cookies!")

    # Initialize API client
    api_client = APIClient(base_url='http://localhost:8080')

    # Check if API is accessible
    if not api_client.check_health():
        print("\n❌ BrowserOperator API is not accessible at http://localhost:8080")
        print("   Please start the container with:")
        print("   cd /Users/olehluchkiv/Work/browser/web-agent && make compose-up")
        return 1

    print("\n✅ BrowserOperator API is accessible")

    # Load model configuration
    config_loader = ConfigLoader()
    model_config = config_loader.get_nested_model_config()

    print(f"\n📋 Model Configuration:")
    print(f"   Main: {model_config['main_model']['provider']}/{model_config['main_model']['model']}")
    print(f"   Mini: {model_config['mini_model']['provider']}/{model_config['mini_model']['model']}")
    print(f"   Nano: {model_config['nano_model']['provider']}/{model_config['nano_model']['model']}")

    # Login to each site
    results = {}
    for site_name, config in ACCOUNTS.items():
        success = login_to_site(site_name, config, api_client, model_config)
        results[site_name] = success

        # Small delay between logins
        if site_name != list(ACCOUNTS.keys())[-1]:
            print("\nWaiting 2 seconds before next login...")
            time.sleep(2)

    # Print summary
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}")

    for site_name, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {site_name:20s} {status}")

    success_count = sum(1 for s in results.values() if s)
    total_count = len(results)

    print(f"\n{success_count}/{total_count} sites logged in successfully")

    if success_count == total_count:
        print("\n🎉 All sites logged in successfully!")
        print("\nThe browser is now authenticated for all WebArena sites.")
        print("You can run authenticated tasks directly:")
        print("\n  cd evals")
        print("  python3 run_shopping_tasks.py --indices 0 --verbose")
        print("\nNote: The session will persist as long as the browser stays open.")
        return 0
    else:
        print("\n⚠️  Some logins failed. Check the errors above.")
        print("You may need to login manually via http://localhost:8000")
        return 1


if __name__ == '__main__':
    exit(main())
