# WebArena Local Environment

This directory contains Docker Compose configuration for running WebArena benchmark websites locally.

## Overview

WebArena consists of 7 self-hosted websites that provide a realistic web automation testing environment:

| Service | Port | Description | Size |
|---------|------|-------------|------|
| Shopping (OneStopShop) | 7770 | E-commerce website (Magento) | ~10GB |
| Shopping Admin | 7780 | Magento CMS backend | ~10GB |
| Forum (Reddit clone) | 9999 | Postmill social forum | ~2GB |
| GitLab | 8023 | Self-hosted GitLab instance | ~5GB |
| Wikipedia (Kiwix) | 8888 | Offline Wikipedia | ~40GB |
| OpenStreetMap | 3000 | Map tile server | ~5GB |
| Homepage | 4399 | WebArena homepage/hub | <100MB |

**Total storage required:** ~75GB

## Quick Start

### Option 1: Quick Test Without Self-Hosted Environment

If you want to test WebArena integration without setting up the full environment:

```bash
cd evals

# Run only public site tasks (no self-hosted required)
python3 run_webarena.py --all --public-only --limit 10
```

This will run WebArena tasks that work on public websites (misc category).

### Option 2: Full Local Setup

#### Step 1: Download Docker Images

WebArena provides pre-built Docker images. Download them from these sources:

**Shopping Website:**
```bash
# Download from one of these mirrors:
# https://drive.google.com/file/d/1gxXalk9O0p9eu1YkIJcmZta1nvvyAJpA
# https://archive.org/download/webarena-env-shopping-image
wget http://metis.lti.cs.cmu.edu/webarena-images/shopping_final_0712.tar

# Load image
docker load --input shopping_final_0712.tar
```

**Shopping Admin:**
```bash
# Download from one of these mirrors:
# https://drive.google.com/file/d/1See0ZhJRw0WTTL9y8hFlgaduwPZ_nGfd
# https://archive.org/download/webarena-env-shopping-admin-image
wget http://metis.lti.cs.cmu.edu/webarena-images/shopping_admin_final_0719.tar

# Load image
docker load --input shopping_admin_final_0719.tar
```

**Forum (Reddit):**
```bash
# Download from one of these mirrors:
# https://drive.google.com/file/d/1L1LGxhm_GDtjWBjXv37w0UD4qZvJfEDq
# https://archive.org/download/webarena-env-reddit-image
wget http://metis.lti.cs.cmu.edu/webarena-images/postmill-populated-exposed-withimg.tar

# Load image
docker load --input postmill-populated-exposed-withimg.tar
```

**GitLab:**
```bash
# Download from one of these mirrors:
# https://drive.google.com/file/d/1a5DEf6h0DiY-Vwh1cnPXbOWjbJy1lnYd
# https://archive.org/download/webarena-env-gitlab-image
wget http://metis.lti.cs.cmu.edu/webarena-images/gitlab-populated-final-port8023.tar

# Load image
docker load --input gitlab-populated-final-port8023.tar
```

**Wikipedia (Kiwix):**
```bash
# Download from one of these mirrors:
# https://drive.google.com/file/d/1nQgAW_mCIBD_xvhVWk72HQx5mfJ5t0Ut
# https://archive.org/download/webarena-env-wikipedia-image
wget http://metis.lti.cs.cmu.edu/webarena-images/kiwix33.tar

# Load image
docker load --input kiwix33.tar
```

**OpenStreetMap:**
```bash
# See webarena/environment_docker/README.md for full OSM setup
# This is the most complex service to set up
```

#### Step 2: Start Services

```bash
cd evals/webarena-local

# Start all services (except OSM, which needs additional setup)
docker-compose up -d shopping shopping_admin forum gitlab kiwix homepage

# Or start everything including OSM (if you've set it up)
docker-compose up -d
```

Wait ~2 minutes for all services to initialize.

#### Step 3: Configure Services

Run these commands to configure each service for localhost:

```bash
# Configure shopping site
docker exec webarena-shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7770"
docker exec webarena-shopping mysql -u magentouser -pMyPassword magentodb -e 'UPDATE core_config_data SET value="http://localhost:7770/" WHERE path = "web/secure/base_url";'
docker exec webarena-shopping /var/www/magento2/bin/magento cache:flush

# Configure shopping admin
docker exec webarena-shopping-admin /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7780"
docker exec webarena-shopping-admin mysql -u magentouser -pMyPassword magentodb -e 'UPDATE core_config_data SET value="http://localhost:7780/" WHERE path = "web/secure/base_url";'
docker exec webarena-shopping-admin /var/www/magento2/bin/magento cache:flush

# Disable admin password reset requirements
docker exec webarena-shopping-admin php /var/www/magento2/bin/magento config:set admin/security/password_is_forced 0
docker exec webarena-shopping-admin php /var/www/magento2/bin/magento config:set admin/security/password_lifetime 0

# Configure GitLab
docker exec webarena-gitlab sed -i "s|^external_url.*|external_url 'http://localhost:8023'|" /etc/gitlab/gitlab.rb
docker exec webarena-gitlab gitlab-ctl reconfigure
```

**If GitLab shows 502 errors:**
```bash
docker exec webarena-gitlab rm -f /var/opt/gitlab/postgresql/data/postmaster.pid
docker exec webarena-gitlab /opt/gitlab/embedded/bin/pg_resetwal -f /var/opt/gitlab/postgresql/data
docker exec webarena-gitlab gitlab-ctl restart
```

#### Step 4: Test Services

```bash
# Test all services (should return HTTP 200)
curl -s -o /dev/null -w "Shopping (7770): %{http_code}\n" http://localhost:7770
curl -s -o /dev/null -w "Shopping Admin (7780): %{http_code}\n" http://localhost:7780
curl -s -o /dev/null -w "Forum (9999): %{http_code}\n" http://localhost:9999
curl -s -o /dev/null -w "GitLab (8023): %{http_code}\n" http://localhost:8023
curl -s -o /dev/null -w "Wikipedia (8888): %{http_code}\n" http://localhost:8888
curl -s -o /dev/null -w "Homepage (4399): %{http_code}\n" http://localhost:4399
```

You can also visit these URLs in your browser:
- Shopping: http://localhost:7770
- Shopping Admin: http://localhost:7780
- Forum: http://localhost:9999
- GitLab: http://localhost:8023
- Wikipedia: http://localhost:8888
- Homepage: http://localhost:4399

#### Step 5: Generate Auth Cookies

WebArena tasks require authentication cookies for certain sites. Generate them:

```bash
cd evals/webarena

# Create .auth directory
mkdir -p .auth

# Generate cookies (you'll need to run the WebArena setup scripts)
# See webarena/README.md for auth cookie generation
```

## Running WebArena Evaluations

Once your local environment is running:

### Run Specific Task

```bash
cd evals

# Run task 1 (Reddit task)
python3 run_webarena.py --task-id 1

# Run with verbose output
python3 run_webarena.py --task-id 1 --verbose
```

### Run Multiple Tasks

```bash
# Run first 10 tasks
python3 run_webarena.py --all --limit 10

# Run only public site tasks (no self-hosted required)
python3 run_webarena.py --all --public-only --limit 20

# Run all available example tasks
python3 run_webarena.py --all
```

### View Results

Results are saved to `evals/reports/` as CSV files:

```bash
# View latest report
ls -lh evals/reports/webarena-*.csv

# View report contents
cat evals/reports/webarena-batch_2025-10-29_14-30-45.csv
```

## Task Configuration Files

WebArena tasks are defined in JSON format in `evals/webarena/config_files/`:

- `examples/` - Sample tasks (4-5 examples)
- `test.raw.json` - Full benchmark (812 tasks)

## Updating Task URLs for Local Environment

If you're running locally, you'll need to update task configuration files to use localhost URLs instead of the default `http://metis.lti.cs.cmu.edu:*` URLs.

Create a script to update URLs:

```bash
# Replace metis.lti.cs.cmu.edu with localhost in task configs
find webarena/config_files/examples -name "*.json" -exec sed -i '' 's/metis\.lti\.cs\.cmu\.edu/localhost/g' {} \;
```

## Stopping Services

```bash
cd evals/webarena-local

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Troubleshooting

### Services Not Starting

Check Docker logs:
```bash
docker-compose logs shopping
docker-compose logs gitlab
docker-compose logs forum
```

### Out of Disk Space

WebArena images are very large (~75GB total). Ensure you have enough disk space:

```bash
df -h
docker system df
```

Clean up unused Docker resources:
```bash
docker system prune -a
```

### Services Not Accessible

Ensure ports are not already in use:
```bash
lsof -i :7770
lsof -i :7780
lsof -i :9999
lsof -i :8023
```

### Task Execution Failures

1. Verify eval-server is running:
   ```bash
   curl http://localhost:8080/status
   ```

2. Check task configuration file exists:
   ```bash
   ls evals/webarena/config_files/examples/1.json
   ```

3. Run with verbose mode to see detailed error:
   ```bash
   python3 run_webarena.py --task-id 1 --verbose
   ```

## Environment Reset

After running many evaluations, reset the environment to initial state:

```bash
cd evals/webarena-local

# Stop and remove containers
docker-compose down

# Remove containers (keeps images)
docker rm webarena-shopping webarena-shopping-admin webarena-forum webarena-gitlab webarena-kiwix

# Restart
docker-compose up -d

# Re-run configuration commands from Step 3
```

## Alternative: AWS EC2 Setup

For production use or running the full 812-task benchmark, we recommend using the official AWS AMI:

- **AMI ID:** ami-08a862bf98e3bd7aa
- **Region:** us-east-2 (Ohio)
- **Instance Type:** t3a.xlarge
- **Storage:** 1000GB EBS

See `evals/webarena/environment_docker/README.md` for complete AWS setup instructions.

## Resources

- **WebArena GitHub:** https://github.com/web-arena-x/webarena
- **WebArena Paper:** https://arxiv.org/abs/2307.13854
- **Docker Images:** http://metis.lti.cs.cmu.edu/webarena-images/
- **Archive.org Mirrors:** https://archive.org/details/@cmu_metis

## Support

For WebArena-specific issues, refer to:
- WebArena documentation: `evals/webarena/README.md`
- Docker environment docs: `evals/webarena/environment_docker/README.md`
- GitHub issues: https://github.com/web-arena-x/webarena/issues

For integration issues with this eval framework, check:
- Main documentation: `evals/CLAUDE.md`
- Runner script: `evals/run_webarena.py --help`
