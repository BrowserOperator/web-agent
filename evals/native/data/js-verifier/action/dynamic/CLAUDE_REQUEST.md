# Claude Code: Generate Validation JavaScript

## Objective
Click the "Start" button to trigger dynamic content loading

## Task
Analyze the BEFORE and AFTER snapshots and generate JavaScript validation code.

## Files to Analyze
- BEFORE: native/data/js-verifier/action/dynamic/before.html
- AFTER: native/data/js-verifier/action/dynamic/after.html
- DIFF: native/data/js-verifier/action/dynamic/diff.txt

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
- **Client ID:** 4af9762d-c210-4c82-b5ff-a261c1167c04
- **Tab ID (AFTER - task completed):** DA823E525F671B595F4C7D13BCBB461B
- **Tab ID (BEFORE - initial state):** 72717EC9480BA1610DA260E917C14E63

**Test 1: AFTER Tab (Should Return TRUE):**
```bash
curl -X POST http://localhost:8080/page/execute \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "4af9762d-c210-4c82-b5ff-a261c1167c04",
    "tabId": "DA823E525F671B595F4C7D13BCBB461B",
    "expression": "YOUR_JAVASCRIPT_CODE_HERE",
    "returnByValue": true,
    "awaitPromise": false
  }'
```

**Expected Response:** `{"result": {"value": true}}`

**Test 2: BEFORE Tab (Should Return FALSE):**
```bash
curl -X POST http://localhost:8080/page/execute \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "4af9762d-c210-4c82-b5ff-a261c1167c04",
    "tabId": "72717EC9480BA1610DA260E917C14E63",
    "expression": "YOUR_JAVASCRIPT_CODE_HERE",
    "returnByValue": true,
    "awaitPromise": false
  }'
```

**Expected Response:** `{"result": {"value": false}}`

**CRITICAL:** Your validation MUST:
- Return TRUE on the AFTER tab (task completed)
- Return FALSE on the BEFORE tab (task not done)
- This proves your validation correctly detects the change

**Error Response:**
```json
{
  "exceptionDetails": { "text": "Error message here" }
}
```

## Workflow

1. Write validation code to: native/data/js-verifier/action/dynamic/verify.js
2. Test it on the AFTER tab (should return TRUE)
3. Test it on the BEFORE tab (should return FALSE)
4. If you get errors or wrong results:
   - Read the existing native/data/js-verifier/action/dynamic/verify.js
   - Identify the issue from the API error response
   - Edit and fix the file
   - Save the improved version
   - Test BOTH tabs again
5. Iterate until:
   - AFTER tab returns {"result": {"value": true}}
   - BEFORE tab returns {"result": {"value": false}}
6. Only then is your code complete

## Save Your Response
When you generate WORKING validation JavaScript (tested via API), save it to:
native/data/js-verifier/action/dynamic/verify.js

The orchestrator will automatically pick it up and test it again for confirmation.

**IMPORTANT:** The file will NOT be deleted between iterations. You can read it,
learn from previous attempts, and improve it iteratively.
