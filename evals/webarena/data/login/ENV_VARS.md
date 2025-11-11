# Environment Variable Configuration

The login tasks use environment variables to support different WebArena deployments. This allows you to point to local, staging, or production instances without modifying the YAML files.

## Syntax

URLs in YAML files use the bash-style default value syntax:

```yaml
url: "${VAR_NAME:-default_value}"
```

- If `VAR_NAME` is set in the environment, its value is used
- If `VAR_NAME` is not set, `default_value` is used

## Supported Variables

| Variable | Default Value | Purpose |
|----------|--------------|---------|
| `SHOPPING` | `http://onestopmarket.com` | Shopping site base URL |
| `SHOPPING_ADMIN` | `http://onestopmarket.com/admin` | Shopping admin panel URL |
| `GITLAB` | `http://gitlab.com` | GitLab instance URL |
| `REDDIT` | `http://reddit.com` | Reddit clone URL |
| `WIKIPEDIA` | `http://wikipedia.org` | Wikipedia instance URL |
| `MAP` | `http://openstreetmap.org` | Map service URL |
| `HOMEPAGE` | `http://homepage.com` | Homepage URL |

## Setting Environment Variables

### Option 1: Export in Shell

```bash
export GITLAB=http://localhost:8023
export SHOPPING=http://localhost:7770
export SHOPPING_ADMIN=http://localhost:7780
```

### Option 2: Create .env File

Create or edit `evals/.env`:

```bash
# Local WebArena deployment
SHOPPING=http://localhost:7770
SHOPPING_ADMIN=http://localhost:7780
GITLAB=http://localhost:8023
REDDIT=http://localhost:9999
```

The ConfigLoader automatically loads this file.

### Option 3: Inline with Command

```bash
GITLAB=http://custom.gitlab.com python3 login_webarena_sites_v2.py --site gitlab
```

## Examples

### Default (No Environment Variables)

```bash
python3 login_webarena_sites_v2.py --list
```

Output shows default URLs:
- GitLab: `http://gitlab.com/users/sign_in`
- Shopping: `http://onestopmarket.com/customer/account/login/`

### Local Development

```bash
# Set local URLs
export SHOPPING=http://localhost:7770
export GITLAB=http://localhost:8023

python3 login_webarena_sites_v2.py --list
```

Output shows local URLs:
- GitLab: `http://localhost:8023/users/sign_in`
- Shopping: `http://localhost:7770/customer/account/login/`

### Production Deployment

```bash
# Set production URLs
export SHOPPING=https://shopping.example.com
export GITLAB=https://gitlab.example.com

python3 login_webarena_sites_v2.py --site shopping
```

Logs in to production shopping site.

## Verification

Check which URLs will be used:

```bash
python3 login_webarena_sites_v2.py --list
```

The output shows the expanded URLs for each site.

## Adding New Variables

1. Add the variable to your `.env` file or export it
2. Use it in YAML files with the default value syntax:

```yaml
target:
  url: "${MY_NEW_VAR:-http://default-url.com}/path"
```

3. Document it in this file

## Troubleshooting

**URLs not expanding correctly:**
- Check environment variables are set: `echo $GITLAB`
- Verify .env file is in `evals/.env`
- Ensure syntax is correct: `${VAR:-default}` (note the `:-`)

**Still using wrong URL:**
- Check for typos in variable names (case-sensitive)
- Verify no extra spaces in .env file
- Try inline export to debug: `GITLAB=http://test.com python3 login_webarena_sites_v2.py --list`

**Environment variables from .env not loading:**
- The ConfigLoader should load it automatically
- Check file location: `/Users/olehluchkiv/Work/browser/web-agent/evals/.env`
- Alternatively, export variables manually before running
