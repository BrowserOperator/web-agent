#!/usr/bin/env python3
"""
Eval Builder with Snapshot-Based Validation Generation

This script follows the CORRECT workflow:
1. Load/create eval file with basic info
2. Open URL in BrowserOperator
3. Capture BEFORE snapshot
4. Wait for user to perform action
5. Capture AFTER snapshot
6. Compare snapshots to find differences
7. Generate validation JS based on ACTUAL differences
8. Save complete eval file

NO HALLUCINATION - validation is based on real observed changes.
"""

import asyncio
import argparse
import os
import sys
import yaml
import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional
from difflib import unified_diff


class SnapshotBasedEvalBuilder:
    """Build eval files using before/after snapshots."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path
        self.eval_data: Dict[str, Any] = {}
        self.client_id: Optional[str] = None
        self.tab_id: Optional[str] = None
        self.tab_id_before: Optional[str] = None  # Second tab with BEFORE state
        self.api_base = "http://localhost:8080"
        self.snapshot_before: Optional[str] = None
        self.snapshot_after: Optional[str] = None

    async def run(self):
        """Main workflow."""
        print("🚀 Snapshot-Based Eval Builder\n")
        print("This workflow:")
        print("1. Loads your eval file (or creates new)")
        print("2. Opens the URL in browser")
        print("3. Captures BEFORE snapshot")
        print("4. Waits for YOU to perform the action")
        print("5. Captures AFTER snapshot")
        print("6. Generates validation from REAL differences")
        print("7. Saves complete eval file\n")

        # Step 1: Load or create eval file
        await self.step_1_load_file()

        # Step 2: Collect basic info (if needed)
        await self.step_2_collect_basic_info()

        # Step 3: Open URL in browser
        await self.step_3_open_browser()

        # Step 4: Capture BEFORE snapshot
        await self.step_4_capture_before()

        # Step 5: Wait for user action
        await self.step_5_wait_for_action()

        # Step 6: Capture AFTER snapshot
        await self.step_6_capture_after()

        # Step 6.5: Open second tab with BEFORE state
        await self.step_6_5_open_before_tab()

        # Step 7: Compare and generate validation
        await self.step_7_generate_validation()

        # Step 8: Save file
        await self.step_8_save_file()

        print("\n✅ Complete!")
        print(f"📄 Saved to: {self.file_path}")

    async def step_1_load_file(self):
        """Step 1: Load existing file or create new."""
        print("📋 Step 1: Load Eval File\n")

        if self.file_path and os.path.exists(self.file_path):
            print(f"📖 Loading: {self.file_path}")
            with open(self.file_path, 'r') as f:
                self.eval_data = yaml.safe_load(f)
            print("✅ Loaded")
        else:
            if not self.file_path:
                path = input("Enter file path: ").strip()
                self.file_path = path or "evals/native/data/builder/new-test.yaml"

            print(f"📝 Creating new: {self.file_path}")
            self.eval_data = self._empty_template()
            print("✅ Ready")

    async def step_2_collect_basic_info(self):
        """Step 2: Collect basic info (only what's needed to open browser)."""
        print("\n📝 Step 2: Basic Info\n")

        # Only collect what we need to proceed
        required = {
            'id': 'Unique ID (e.g., test-001)',
            'name': 'Test name',
            'description': 'What this tests',
            'url': 'Target URL',
            'objective': 'What action to perform'
        }

        for key, prompt in required.items():
            if key == 'url':
                current = self.eval_data.get('target', {}).get('url', '')
            elif key == 'objective':
                current = self.eval_data.get('input', {}).get('objective', '')
            else:
                current = self.eval_data.get(key, '')

            value = self._prompt_field(prompt, current)

            if key == 'url':
                if 'target' not in self.eval_data:
                    self.eval_data['target'] = {}
                self.eval_data['target']['url'] = value
            elif key == 'objective':
                if 'input' not in self.eval_data:
                    self.eval_data['input'] = {}
                self.eval_data['input']['objective'] = value
            else:
                self.eval_data[key] = value

        print("\n✅ Basic info collected")

    async def step_3_open_browser(self):
        """Step 3: Open URL in BrowserOperator."""
        print("\n🌐 Step 3: Open in Browser\n")

        url = self.eval_data['target']['url']

        try:
            # Get client
            print("🔍 Getting browser client...")
            resp = requests.get(f"{self.api_base}/clients", timeout=5)
            resp.raise_for_status()
            clients = resp.json()

            if not clients:
                print("❌ No browser clients. Is BrowserOperator running?")
                print("   Start it: cd deployments/local && make compose-up")
                sys.exit(1)

            self.client_id = clients[0]['id']
            print(f"✅ Client: {self.client_id}")

            # Open tab
            print(f"🌐 Opening: {url}")
            resp = requests.post(
                f"{self.api_base}/tabs/open",
                json={
                    "clientId": self.client_id,
                    "url": url,
                    "background": False
                },
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json()

            self.tab_id = result['tabId']
            print(f"✅ Tab opened: {self.tab_id}")

            # Wait for page load
            print("⏳ Waiting for page to load...")
            await asyncio.sleep(3)
            print("✅ Page loaded")

        except requests.exceptions.RequestException as e:
            print(f"❌ Browser error: {e}")
            print("   Make sure BrowserOperator is running at http://localhost:8080")
            sys.exit(1)

    async def step_4_capture_before(self):
        """Step 4: Capture BEFORE snapshot."""
        print("\n📸 Step 4: Capture BEFORE Snapshot\n")

        try:
            print("📸 Capturing page state BEFORE action (including iframes)...")
            resp = requests.post(
                f"{self.api_base}/page/content",
                json={
                    "clientId": self.client_id,
                    "tabId": self.tab_id,
                    "format": "html",
                    "includeIframes": True
                },
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json()

            self.snapshot_before = result['content']
            frame_count = result.get('frameCount', 1)
            print(f"✅ Captured BEFORE state ({len(self.snapshot_before)} bytes, {frame_count} frames)")

        except requests.exceptions.RequestException as e:
            print(f"❌ Snapshot error: {e}")
            sys.exit(1)

    async def step_5_wait_for_action(self):
        """Step 5: Wait for user to perform action."""
        print("\n⏸️  Step 5: Perform the Action\n")

        objective = self.eval_data['input']['objective']
        print(f"📋 Objective: {objective}\n")
        print("👉 Now manually perform this action in the browser")
        print("   The browser should be visible at http://localhost:8000")
        print()

        input("Press Enter when you've completed the action...")
        print("✅ Action completed")

    async def step_6_capture_after(self):
        """Step 6: Capture AFTER snapshot."""
        print("\n📸 Step 6: Capture AFTER Snapshot\n")

        try:
            print("📸 Capturing page state AFTER action (including iframes)...")
            resp = requests.post(
                f"{self.api_base}/page/content",
                json={
                    "clientId": self.client_id,
                    "tabId": self.tab_id,
                    "format": "html",
                    "includeIframes": True
                },
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json()

            self.snapshot_after = result['content']
            frame_count = result.get('frameCount', 1)
            print(f"✅ Captured AFTER state ({len(self.snapshot_after)} bytes, {frame_count} frames)")

        except requests.exceptions.RequestException as e:
            print(f"❌ Snapshot error: {e}")
            sys.exit(1)

    async def step_6_5_open_before_tab(self):
        """Step 6.5: Open second tab with BEFORE state for validation testing."""
        print("\n🔄 Step 6.5: Open BEFORE State Tab for Validation\n")

        try:
            url = self.eval_data['target']['url']
            print(f"🌐 Opening fresh tab with URL: {url}")
            print("   This tab will have the BEFORE state (no action performed)")
            print("   It will be used to verify validation returns FALSE\n")

            resp = requests.post(
                f"{self.api_base}/tabs/open",
                json={
                    "clientId": self.client_id,
                    "url": url,
                    "background": False
                },
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json()

            self.tab_id_before = result['tabId']
            print(f"✅ Opened BEFORE state tab")
            print(f"   Tab ID (BEFORE): {self.tab_id_before}")
            print(f"   Tab ID (AFTER):  {self.tab_id}")
            print()
            print("💡 Claude Code will test validation on BOTH tabs:")
            print("   - AFTER tab should return TRUE (task completed)")
            print("   - BEFORE tab should return FALSE (task not done)")

            # Wait for page to load
            await asyncio.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to open BEFORE tab: {e}")
            print("   Continuing without second tab (validation will only test AFTER state)")
            self.tab_id_before = None

    async def step_7_generate_validation(self):
        """Step 7: Compare snapshots and generate validation using Claude Code."""
        print("\n🔍 Step 7: Generate Validation from Differences\n")

        print("🔍 Analyzing differences...")

        # Find differences
        before_lines = self.snapshot_before.split('\n')
        after_lines = self.snapshot_after.split('\n')

        diff = list(unified_diff(
            before_lines,
            after_lines,
            lineterm='',
            n=3  # 3 lines of context
        ))

        # Extract actual changes
        added_lines = [line[1:] for line in diff if line.startswith('+') and not line.startswith('+++')]
        removed_lines = [line[1:] for line in diff if line.startswith('-') and not line.startswith('---')]

        print(f"📊 Found {len(added_lines)} additions, {len(removed_lines)} removals")

        # Save snapshots to files for Claude to analyze
        snapshot_dir = "/tmp/eval_builder_snapshots"
        os.makedirs(snapshot_dir, exist_ok=True)

        before_file = f"{snapshot_dir}/before.html"
        after_file = f"{snapshot_dir}/after.html"
        diff_file = f"{snapshot_dir}/diff.txt"

        with open(before_file, 'w') as f:
            f.write(self.snapshot_before)

        with open(after_file, 'w') as f:
            f.write(self.snapshot_after)

        with open(diff_file, 'w') as f:
            f.write('\n'.join(diff))

        print(f"\n📁 Snapshots saved:")
        print(f"   BEFORE: {before_file}")
        print(f"   AFTER:  {after_file}")
        print(f"   DIFF:   {diff_file}")

        # Show sample of changes
        if added_lines:
            print("\n📝 Sample additions:")
            for line in added_lines[:5]:
                print(f"   + {line[:100]}...")

        if removed_lines:
            print("\n📝 Sample removals:")
            for line in removed_lines[:5]:
                print(f"   - {line[:100]}...")

        print("\n" + "=" * 80)
        print("🤖 CALLING CLAUDE CODE TO ANALYZE SNAPSHOTS")
        print("=" * 80)
        print()

        # Create a marker file that Claude Code can detect
        marker_file = f"{snapshot_dir}/CLAUDE_REQUEST.md"
        with open(marker_file, 'w') as f:
            f.write(f"""# Claude Code: Generate Validation JavaScript

## Objective
{self.eval_data['input']['objective']}

## Task
Analyze the BEFORE and AFTER snapshots and generate JavaScript validation code.

## Files to Analyze
- BEFORE: {before_file}
- AFTER: {after_file}
- DIFF: {diff_file}

## Instructions
1. Read the BEFORE and AFTER HTML files
2. Read the DIFF file to see what actually changed
3. Identify the specific DOM changes that indicate the objective was completed
4. Generate JavaScript code that:
   - Checks if the objective was completed successfully
   - **CRITICAL: DO NOT use `return` statements - end with a boolean expression**
   - Is based on ACTUAL observed changes (not assumptions)
   - Works in the browser context

## CRITICAL: Output Format

**DO NOT USE RETURN STATEMENTS!** The code is evaluated as an expression, not a function.

❌ WRONG:
```javascript
return document.querySelector('#success') !== null;
```

✅ CORRECT:
```javascript
// Check for the specific change
const element = document.querySelector('...');
element && element.value === 'expected'
```

The last line should be a boolean expression (no return keyword).

## Testing Your Code

**YOU MUST TEST YOUR CODE ON BOTH TABS** before declaring it complete.

**Endpoint:** POST http://localhost:8080/page/execute

**Browser State Information:**
- **Client ID:** {self.client_id}
- **Tab ID (AFTER - task completed):** {self.tab_id}
- **Tab ID (BEFORE - initial state):** {self.tab_id_before}

**Test 1: AFTER Tab (Should Return TRUE):**
```bash
curl -X POST http://localhost:8080/page/execute \\
  -H "Content-Type: application/json" \\
  -d '{{
    "clientId": "{self.client_id}",
    "tabId": "{self.tab_id}",
    "expression": "YOUR_JAVASCRIPT_CODE_HERE",
    "returnByValue": true,
    "awaitPromise": false
  }}'
```

**Expected Response:** `{{"result": {{"value": true}}}}`

**Test 2: BEFORE Tab (Should Return FALSE):**
```bash
curl -X POST http://localhost:8080/page/execute \\
  -H "Content-Type: application/json" \\
  -d '{{
    "clientId": "{self.client_id}",
    "tabId": "{self.tab_id_before}",
    "expression": "YOUR_JAVASCRIPT_CODE_HERE",
    "returnByValue": true,
    "awaitPromise": false
  }}'
```

**Expected Response:** `{{"result": {{"value": false}}}}`

**CRITICAL:** Your validation MUST:
- Return TRUE on the AFTER tab (task completed)
- Return FALSE on the BEFORE tab (task not done)
- This proves your validation correctly detects the change

**Error Response:**
```json
{{
  "exceptionDetails": {{ "text": "Error message here" }}
}}
```

## Workflow

1. Write validation code to: {snapshot_dir}/validation.js
2. Test it on the AFTER tab (should return TRUE)
3. Test it on the BEFORE tab (should return FALSE)
4. If you get errors or wrong results:
   - Read the existing {snapshot_dir}/validation.js
   - Identify the issue from the API error response
   - Edit and fix the file
   - Save the improved version
   - Test BOTH tabs again
5. Iterate until:
   - AFTER tab returns {{"result": {{"value": true}}}}
   - BEFORE tab returns {{"result": {{"value": false}}}}
6. Only then is your code complete

## Save Your Response
When you generate WORKING validation JavaScript (tested via API), save it to:
{snapshot_dir}/validation.js

The orchestrator will automatically pick it up and test it again for confirmation.

**IMPORTANT:** The file will NOT be deleted between iterations. You can read it,
learn from previous attempts, and improve it iteratively.
""")

        print(f"📝 Created request file: {marker_file}")
        print()
        print("=" * 80)
        print("🤖 CLAUDE CODE: Generate and Test Validation JavaScript")
        print("=" * 80)
        print()
        print("📋 API Testing Information:")
        print(f"   Endpoint:     POST http://localhost:8080/page/execute")
        print(f"   Client ID:    {self.client_id}")
        print(f"   Tab ID (AFTER - task completed):  {self.tab_id}")
        if self.tab_id_before:
            print(f"   Tab ID (BEFORE - initial state): {self.tab_id_before}")
        print()
        print("📝 Instructions for Claude Code:")
        print(f"   1. Read @{marker_file}")
        print(f"   2. Analyze the snapshots and generate validation code")
        print(f"   3. TEST on BOTH tabs using /page/execute endpoint:")
        if self.tab_id_before:
            print(f"      - AFTER tab ({self.tab_id}) should return TRUE")
            print(f"      - BEFORE tab ({self.tab_id_before}) should return FALSE")
        else:
            print(f"      - Test on AFTER tab ({self.tab_id}) should return TRUE")
        print(f"   4. Fix any errors (especially 'Illegal return statement')")
        print(f"   5. Iterate until both tests pass correctly")
        print(f"   6. Save working code to: {snapshot_dir}/validation.js")
        print()
        print("⚠️  CRITICAL: NO return statements! End with boolean expression.")
        if self.tab_id_before:
            print("⚠️  MUST TEST BOTH TABS: TRUE on AFTER, FALSE on BEFORE")
        print()
        print("=" * 80)
        print()

        # Wait for Claude to create the validation file
        validation_file = f"{snapshot_dir}/validation.js"

        print("Options:")
        print("1. Wait for Claude Code to create validation.js (recommended)")
        print("2. Enter validation JavaScript manually")
        print()

        choice = input("Choice (1/2): ").strip()

        lines = []

        if choice == '1':
            print(f"\n⏳ Waiting for {validation_file} to be created...")
            print("   (Claude Code will create this file)")
            print()

            # Poll for file creation
            max_wait = 300  # 5 minutes
            waited = 0
            while waited < max_wait:
                if os.path.exists(validation_file):
                    print("✅ Validation file detected!")
                    with open(validation_file, 'r') as f:
                        js_code = f.read().strip()

                    # Clean up if it has markdown code blocks
                    if js_code.startswith('```'):
                        # Remove markdown code fences
                        lines_raw = js_code.split('\n')
                        if lines_raw[0].startswith('```'):
                            lines_raw = lines_raw[1:]
                        if lines_raw[-1].startswith('```'):
                            lines_raw = lines_raw[:-1]
                        js_code = '\n'.join(lines_raw).strip()

                    print()
                    print("📝 Loaded validation code:")
                    print("─" * 60)
                    print(js_code[:300] + "..." if len(js_code) > 300 else js_code)
                    print("─" * 60)

                    lines = js_code.split('\n')
                    break

                time.sleep(2)
                waited += 2
                if waited % 10 == 0:
                    print(f"   Still waiting... ({waited}s)")

            if not lines:
                print("⏱️  Timeout waiting for validation file")
                print("   Falling back to manual entry...")
                choice = '2'

        if choice == '2':
            print("\nEnter validation JavaScript (type 'END' on new line when done):\n")
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)

        if lines:
            js_code = '\n'.join(lines)

            # Test it with retry loop
            validation_saved = False
            max_retries = 3
            retry_count = 0

            while retry_count <= max_retries and not validation_saved:
                print(f"\n🧪 Testing validation... (attempt {retry_count + 1}/{max_retries + 1})")

                if await self._test_validation(js_code):
                    if 'validation' not in self.eval_data:
                        self.eval_data['validation'] = {'type': 'js-eval', 'js-eval': {}}

                    self.eval_data['validation']['js-eval']['script'] = js_code
                    self.eval_data['validation']['js-eval']['expected_result'] = True
                    self.eval_data['validation']['js-eval']['timeout'] = 5000
                    print("✅ Validation saved")
                    validation_saved = True
                else:
                    # Test failed
                    if retry_count < max_retries:
                        print(f"\n⚠️  Validation test failed. You have {max_retries - retry_count} retries remaining.")
                        print("\nOptions:")
                        print("1. Let Claude Code fix it (updates validation.js)")
                        print("2. Enter new validation manually")
                        print("3. Save anyway (not recommended)")
                        print("4. Skip validation for now")

                        retry_choice = input("\nChoice (1/2/3/4): ").strip()

                        if retry_choice == '1':
                            # Wait for Claude Code to update the file
                            print()
                            print("=" * 80)
                            print("🔧 CLAUDE CODE: Fix the Validation JavaScript")
                            print("=" * 80)
                            print()
                            print("📋 API Testing Information:")
                            print(f"   Endpoint:     POST http://localhost:8080/page/execute")
                            print(f"   Client ID:    {self.client_id}")
                            print(f"   Tab ID (AFTER - task completed):  {self.tab_id}")
                            if self.tab_id_before:
                                print(f"   Tab ID (BEFORE - initial state): {self.tab_id_before}")
                            print()
                            print("📝 What to do in Claude Code:")
                            print(f"   1. Edit and fix the JavaScript in: {validation_file}")
                            print("   2. Remove any 'return' statements")
                            print("   3. Test on BOTH tabs using /page/execute endpoint:")
                            if self.tab_id_before:
                                print(f"      - AFTER tab ({self.tab_id}) → should return TRUE")
                                print(f"      - BEFORE tab ({self.tab_id_before}) → should return FALSE")
                            else:
                                print(f"      - AFTER tab ({self.tab_id}) → should return TRUE")
                            print(f"   4. Iterate until both tests pass correctly")
                            print(f"   5. Save your fixes back to: {validation_file}")
                            print()
                            print("   💡 Claude Code can read the existing file and improve it iteratively")
                            if self.tab_id_before:
                                print("   ⚠️  Validation MUST return TRUE on AFTER, FALSE on BEFORE")
                            print()
                            print("=" * 80)
                            print()

                            input("Press Enter when Claude Code has updated the file...")
                            print()

                            if os.path.exists(validation_file):
                                print("✅ Updated file detected!")
                                with open(validation_file, 'r') as f:
                                    js_code = f.read().strip()

                                # Clean up markdown if present
                                if js_code.startswith('```'):
                                    lines_raw = js_code.split('\n')
                                    if lines_raw[0].startswith('```'):
                                        lines_raw = lines_raw[1:]
                                    if lines_raw[-1].startswith('```'):
                                        lines_raw = lines_raw[:-1]
                                    js_code = '\n'.join(lines_raw).strip()

                                print()
                                print("📝 Loaded updated validation code:")
                                print("─" * 60)
                                print(js_code[:200] + "..." if len(js_code) > 200 else js_code)
                                print("─" * 60)
                                print()
                                print("🔄 Re-testing with updated code...")

                                retry_count += 1
                                # Continue to top of loop to re-test
                                continue
                            else:
                                print("❌ File not found. Please try again.")
                                retry_count += 1
                                continue

                        elif retry_choice == '2':
                            # Manual entry
                            print("\nEnter validation JavaScript (type 'END' on new line when done):\n")
                            new_lines = []
                            while True:
                                line = input()
                                if line.strip() == 'END':
                                    break
                                new_lines.append(line)
                            js_code = '\n'.join(new_lines)
                            retry_count += 1
                            continue

                        elif retry_choice == '3':
                            # Save anyway
                            if 'validation' not in self.eval_data:
                                self.eval_data['validation'] = {'type': 'js-eval', 'js-eval': {}}
                            self.eval_data['validation']['js-eval']['script'] = js_code
                            self.eval_data['validation']['js-eval']['expected_result'] = True
                            self.eval_data['validation']['js-eval']['timeout'] = 5000
                            print("⚠️  Validation saved (with errors - use caution!)")
                            validation_saved = True

                        else:  # Choice 4 or anything else
                            print("⏭️  Skipping validation")
                            break
                    else:
                        # Out of retries
                        print(f"\n❌ Maximum retries ({max_retries}) reached.")
                        save_anyway = input("Save validation anyway? (y/n): ").strip().lower()
                        if save_anyway == 'y':
                            if 'validation' not in self.eval_data:
                                self.eval_data['validation'] = {'type': 'js-eval', 'js-eval': {}}
                            self.eval_data['validation']['js-eval']['script'] = js_code
                            self.eval_data['validation']['js-eval']['expected_result'] = True
                            self.eval_data['validation']['js-eval']['timeout'] = 5000
                            print("⚠️  Validation saved (with errors)")
                            validation_saved = True
                        break
        else:
            print("⚠️  No validation code entered")

    async def _test_validation(self, js_code: str) -> bool:
        """Test validation JavaScript."""
        try:
            resp = requests.post(
                f"{self.api_base}/page/execute",
                json={
                    "clientId": self.client_id,
                    "tabId": self.tab_id,
                    "expression": js_code,
                    "returnByValue": True
                },
                timeout=5
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get('exceptionDetails'):
                print(f"❌ JS Error: {result['exceptionDetails']}")
                return False

            # Handle different response formats
            # Format 1: {"result": true/false}
            # Format 2: {"result": {"value": true/false}}
            if 'result' in result:
                if isinstance(result['result'], dict):
                    value = result['result'].get('value')
                else:
                    value = result['result']
                print(f"✅ Returned: {value}")
                return True
            else:
                print(f"❌ Unexpected response format: {result}")
                return False

        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False

    def _auto_generate_validation(self, added: list, removed: list) -> str:
        """Auto-generate validation based on changes."""
        # Simple heuristics for common patterns

        # Check for input value changes
        for line in added:
            if 'value=' in line and 'input' in line.lower():
                return """// Check if input value was set
const input = document.querySelector('input[type="text"], input[type="date"]');
return input && input.value !== '';"""

        # Check for new elements
        if len(added) > len(removed):
            return """// Check if new content appeared
return document.body.innerHTML.length > 1000; // Adjust as needed"""

        # Default
        return """// TODO: Customize this validation
return true;"""

    async def step_8_save_file(self):
        """Step 8: Save complete eval file."""
        print("\n💾 Step 8: Save File\n")

        # Fill in defaults
        if 'enabled' not in self.eval_data:
            self.eval_data['enabled'] = True
        if 'tool' not in self.eval_data:
            self.eval_data['tool'] = 'action_agent'
        if 'timeout' not in self.eval_data:
            self.eval_data['timeout'] = 60000
        if 'target' not in self.eval_data:
            self.eval_data['target'] = {}
        if 'wait_for' not in self.eval_data['target']:
            self.eval_data['target']['wait_for'] = 'networkidle'
        if 'wait_timeout' not in self.eval_data['target']:
            self.eval_data['target']['wait_timeout'] = 5000

        # Preview
        print("Preview:")
        print("─" * 60)
        preview = yaml.dump(self.eval_data, default_flow_style=False, sort_keys=False)
        print(preview)
        print("─" * 60)

        confirm = input("\nSave? (y/n): ").strip().lower()
        if confirm == 'y':
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as f:
                yaml.dump(self.eval_data, f, default_flow_style=False, sort_keys=False)
            print(f"✅ Saved: {self.file_path}")
        else:
            print("❌ Not saved")

    def _prompt_field(self, prompt: str, current: str) -> str:
        """Prompt for field value."""
        if current:
            print(f"{prompt}")
            print(f"  Current: {current}")
            value = input("  New (Enter to keep): ").strip()
            return value if value else current
        else:
            return input(f"{prompt}: ").strip()

    def _empty_template(self) -> dict:
        """Empty template."""
        return {
            'id': '',
            'name': '',
            'description': '',
            'enabled': True,
            'target': {'url': '', 'wait_for': 'networkidle', 'wait_timeout': 5000},
            'tool': 'action_agent',
            'timeout': 60000,
            'input': {'objective': ''},
            'validation': {'type': 'js-eval', 'js-eval': {'script': '', 'expected_result': True, 'timeout': 5000}}
        }


async def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Snapshot-based eval builder")
    parser.add_argument('--file', '-f', help='Eval file path')
    args = parser.parse_args()

    builder = SnapshotBasedEvalBuilder(file_path=args.file)
    await builder.run()


if __name__ == '__main__':
    asyncio.run(main())
