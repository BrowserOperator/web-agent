# WebArena Quick Start

Two simple scripts to set up and manage WebArena locally:

## 1. Initial Setup (One-Time)

Run this once to download images and set everything up:

```bash
cd evals/webarena-local
./setup-webarena.sh
```

**What it does:**
- Downloads all Docker images (~75GB)
- Loads images into Docker
- Starts all services
- Configures services for localhost
- Tests all services
- Updates task configs

**Time:** 1-2 hours (mostly downloading)

**Requirements:**
- 80GB+ free disk space
- Docker installed and running
- `wget` or `curl` installed

## 2. Daily Management

Use this script to manage services after initial setup:

```bash
./webarena.sh [command]
```

### Commands

**Start services:**
```bash
./webarena.sh start
```

**Check status:**
```bash
./webarena.sh status
```

**Stop services:**
```bash
./webarena.sh stop
```

**Restart services:**
```bash
./webarena.sh restart
```

**View logs:**
```bash
./webarena.sh logs              # All services
./webarena.sh logs gitlab       # Specific service
```

**Open in browser:**
```bash
./webarena.sh open
```

**Run a test:**
```bash
./webarena.sh test 3            # Run task 3
./webarena.sh test 1            # Run task 1
```

## Services & Ports

Once running, services are available at:

| Service | URL | Port |
|---------|-----|------|
| Shopping | http://localhost:7770 | 7770 |
| Shopping Admin | http://localhost:7780 | 7780 |
| Forum (Reddit) | http://localhost:9999 | 9999 |
| GitLab | http://localhost:8023 | 8023 |
| Wikipedia | http://localhost:8888 | 8888 |
| Homepage | http://localhost:4399 | 4399 |

## Running WebArena Tasks

After services are started:

```bash
cd evals

# Run specific task
python3 run_webarena.py --task-id 1 --verbose

# Run all tasks (limited)
python3 run_webarena.py --all --limit 10

# Run with custom timeout
python3 run_webarena.py --task-id 1 --verbose
```

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# Check logs
./webarena.sh logs

# Try restarting
./webarena.sh restart
```

### GitLab shows 502 errors
```bash
# Fix GitLab
docker exec webarena-gitlab rm -f /var/opt/gitlab/postgresql/data/postmaster.pid
docker exec webarena-gitlab gitlab-ctl restart
./webarena.sh status
```

### Out of disk space
```bash
# Clean up Docker
docker system prune -a

# Remove downloaded images after loading
rm -rf ./webarena-images/
```

### Port already in use
```bash
# Stop conflicting services
lsof -i :7770  # Find what's using the port
kill <PID>     # Stop it

# Or use different ports in docker-compose.yml
```

## Skip Full Setup (Manual)

If you already have the Docker images:

```bash
# Load images manually
docker load --input shopping_final_0712.tar
docker load --input shopping_admin_final_0719.tar
docker load --input postmill-populated-exposed-withimg.tar
docker load --input gitlab-populated-final-port8023.tar
docker load --input kiwix33.tar

# Start services
./webarena.sh start

# Configure (run once)
# Follow configuration steps in setup-webarena.sh
```

## Alternative: Use Docker Compose Directly

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart gitlab
```

## Uninstall

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi shopping_final_0712
docker rmi shopping_admin_final_0719
docker rmi postmill-populated-exposed-withimg
docker rmi gitlab-populated-final-port8023
docker rmi kiwix33

# Remove downloaded files
rm -rf ./webarena-images/

# Remove backup configs
rm -rf ../webarena/config_files/examples.backup
```

## Tips

- **First time:** Run `./setup-webarena.sh` once
- **Daily use:** Use `./webarena.sh` commands
- **Debugging:** Check `./webarena.sh logs`
- **Disk space:** Clean up with `docker system prune`
- **Performance:** GitLab uses most resources (~2GB RAM)

## Support

- **Setup issues:** Check `setup-webarena.sh` output
- **Service issues:** Run `./webarena.sh logs [service]`
- **Task issues:** Run with `--verbose` flag
- **Full docs:** See `README.md`
