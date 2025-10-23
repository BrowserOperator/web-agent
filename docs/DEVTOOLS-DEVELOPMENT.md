# DevTools Development Workflow

This document explains how to develop and iterate on Browser Operator DevTools locally.

## Architecture

The build system uses a 2-stage approach for fast iteration:

1. **Stage 1: DevTools Build** (`Dockerfile.devtools`) - Builds Browser Operator DevTools
   - Expensive operations (fetch, sync) are cached in `devtools-base` layer
   - Fast rebuilds when you modify BrowserOperator code

2. **Stage 2: Browser Image** (`Dockerfile.local`) - Combines DevTools with kernel-browser
   - Copies pre-built DevTools from Stage 1
   - Quick rebuilds (~2-5 min)

## Quick Start

### First Time Setup

```bash
# Initialize submodules and build everything
make init
make build-devtools  # ~30 minutes (one-time)
make build           # ~5 minutes
make run
```

### Daily Development Workflow

#### Editing Browser Operator Code

```bash
# 1. Make changes to browser-operator-core/front_end/
vim browser-operator-core/front_end/panels/ai_chat/...

# 2. Rebuild DevTools (fast, ~5-10 min)
make rebuild-devtools

# 3. Rebuild final image (fast, ~2-5 min)
make build

# 4. Run
make run
```

#### Quick Iteration (no DevTools changes)

```bash
# If you're only changing kernel-browser config
make build  # Smart: skips DevTools if already built
make run
```

## Makefile Commands

### DevTools Management
- `make init-devtools` - Initialize browser-operator-core submodule
- `make build-devtools-base` - Build base layer (rare, ~30min)
- `make build-devtools` - Build DevTools (smart, uses cache)
- `make rebuild-devtools` - Force rebuild (after code changes)
- `make clean-devtools` - Remove DevTools images

### Main Workflow
- `make init` - Initialize all submodules
- `make build` - Build everything (calls build-devtools automatically)
- `make run` - Run the container
- `make stop` - Stop containers
- `make clean` - Clean up everything

## Understanding the Build Stages

### Dockerfile.devtools

```
devtools-base (cached)
  ├─ Install system deps
  ├─ Clone depot_tools
  ├─ Fetch devtools-frontend (~2GB, cached!)
  ├─ gclient sync (cached!)
  └─ npm run build (cached!)

devtools-local (fast rebuild)
  ├─ Add BrowserOperator remote
  ├─ Checkout upstream/main
  ├─ (Optional: COPY local changes)
  └─ npm run build (~5-10 min)

devtools-server (nginx)
  └─ Serve built DevTools on port 8001
```

### Smart Caching

- **First build**: ~30 minutes (builds everything)
- **After code changes**: ~5-10 minutes (only rebuilds DevTools)
- **No changes**: <1 minute (uses cached layers)

## Troubleshooting

### "DevTools image not found"

```bash
make build-devtools
```

### Force complete rebuild

```bash
make clean-devtools
make build-devtools-base
make build-devtools
make build
```

### Submodule issues

```bash
git submodule deinit -f browser-operator-core
git submodule update --init --depth 1 browser-operator-core
```

### Profile lock errors

The `run-local.sh` script automatically cleans lock files. If you still see issues:

```bash
rm -f chromium-data/user-data/Singleton*
make run
```

## Development Tips

1. **Modify BrowserOperator locally**: Edit files in `browser-operator-core/`, then `make rebuild-devtools`

2. **Switch BrowserOperator branches**:
   ```bash
   cd browser-operator-core
   git fetch origin
   git checkout feature-branch
   cd ..
   make rebuild-devtools
   ```

3. **Test DevTools standalone**:
   ```bash
   docker run -p 8001:8001 browser-operator-devtools:latest
   # Access at http://localhost:8001
   ```

4. **Skip DevTools rebuild**: If you only change kernel-browser config, just run `make build`

## File Reference

- `.gitmodules` - Submodule configuration
- `Dockerfile.devtools` - DevTools build (2-stage)
- `Dockerfile.local` - Final browser image
- `Makefile` - Build orchestration
- `build-local.sh` - Build script with smart checks
- `run-local.sh` - Run script with lock file cleanup

## Contributing Back

If you make improvements to the DevTools build process, consider contributing them upstream to:
https://github.com/BrowserOperator/browser-operator-core

The `Dockerfile.devtools` in this repo can serve as the basis for a `docker/Dockerfile.dev` in the upstream repo.
