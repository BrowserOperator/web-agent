# WebArena Login Tasks

This directory contains YAML-based login tasks for WebArena sites. Each task is a self-contained evaluation that can be run individually or as part of a batch login process.

## Task Files

- **shopping-001.yaml** - Login to OneStopMarket (shopping site)
- **shopping-admin-001.yaml** - Login to OneStopMarket admin panel
- **gitlab-001.yaml** - Login to GitLab instance
- **reddit-001.yaml** - Login to Reddit clone (currently disabled)

## Task Structure

Each YAML file follows the standard evaluation format:

```yaml
id: "login-shopping-001"
name: "Login to Shopping Site"
description: "Login to WebArena shopping site"
enabled: true

target:
  url: "${SHOPPING:-http://onestopmarket.com}/customer/account/login/"
  wait_for: "domcontentloaded"
  wait_timeout: 10000

tool: "action_agent"
timeout: 60000

input:
  objective: |
    Fill in the email field with "emma.lopez@gmail.com".
    Fill in the password field with "Password.123".
    Click the "Sign In" button.

validation:
  type: "llm-judge"
  llm_judge:
    model: "gpt-4.1-mini"
    criteria:
      - "Successfully filled in login form"
      - "Login was successful"
    visual_verification:
      enabled: true
      prompts:
        - "Verify user is logged in"

metadata:
  tags: ["webarena", "login", "shopping"]
  site: "shopping"
  account:
    username: "emma.lopez@gmail.com"
```

## Environment Variables

The tasks use environment variables for site URLs, allowing easy configuration for different deployments:

- `SHOPPING` - Shopping site URL (default: http://onestopmarket.com)
- `SHOPPING_ADMIN` - Shopping admin URL (default: http://onestopmarket.com/admin)
- `GITLAB` - GitLab URL (default: http://gitlab.com)
- `REDDIT` - Reddit URL (default: http://reddit.com)

Set these in `evals/.env` or export them before running tasks.

**📖 See [ENV_VARS.md](ENV_VARS.md) for detailed configuration guide including:**
- How to set environment variables
- Deployment-specific configurations
- Troubleshooting guide
- Examples for local, staging, and production

## Usage

### Run All Login Tasks

```bash
cd evals/webarena
python3 login_webarena_sites_v2.py
```

### Run Specific Site Login

```bash
# Login to shopping site only
python3 login_webarena_sites_v2.py --site shopping

# Login to GitLab only
python3 login_webarena_sites_v2.py --site gitlab
```

### List Available Tasks

```bash
python3 login_webarena_sites_v2.py --list
```

### Verbose Output

```bash
python3 login_webarena_sites_v2.py --verbose
```

## Running Individual Tasks with Native Runner

Since these are standard YAML tasks, you can also run them with the native evaluation runner:

```bash
cd evals/native
python3 run.py --path ../webarena/data/login/shopping-001.yaml --verbose
```

This is useful for:
- Testing individual logins
- Debugging login issues
- Capturing screenshots of login process
- Getting detailed evaluation reports

## Adding New Login Tasks

1. Create a new YAML file in this directory (e.g., `wikipedia-001.yaml`)
2. Follow the structure of existing tasks
3. Set `enabled: true` to include in batch login
4. Add account credentials in `metadata.account`
5. Test with: `python3 login_webarena_sites_v2.py --site <site_name>`

## Credentials

All WebArena test credentials are defined in the YAML files. These are the default test accounts from the WebArena benchmark:

- **Shopping**: emma.lopez@gmail.com / Password.123
- **Shopping Admin**: admin / admin1234
- **GitLab**: byteblaze / hello1234
- **Reddit**: MarvelsGrantMan136 / test1234 (currently not working)

## Session Persistence

Once logged in, the browser session persists for the lifetime of the container. Subsequent tasks will be automatically authenticated, so you don't need to login again unless you restart the container.

## Troubleshooting

**Task fails with "API not accessible"**
- Ensure the browser-agent-server is running: `make compose-up`
- Check API endpoint: `curl http://localhost:8080/status`

**Login succeeds but task marked as failed**
- Check visual verification with `--verbose` flag
- Review screenshots in `evals/screenshots/`
- Adjust validation criteria in YAML file

**Environment variable not expanding**
- Set variables in `evals/.env` file
- Or export before running: `export SHOPPING=http://localhost:7770`
- Check with: `python3 login_webarena_sites_v2.py --list`

**Site-specific login issues**
- Verify site is accessible: `curl <site_url>`
- Check WebArena infrastructure is running
- Review site-specific notes in YAML files
