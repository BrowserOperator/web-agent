# DevTools Build System - Implementation Plan & Usage

## Overview

This document describes the 2-stage build system for Browser Operator DevTools that enables fast local development and iteration.

## Problem Statement

The original build process had several issues:
1. **Slow builds**: Every build fetched ~2GB of DevTools source from scratch (~30 minutes)
2. **No caching**: Expensive operations (depot_tools, fetch, gclient sync) weren't cached
3. **Submodule conflicts**: `browser-operator-core` was orphaned, causing git errors
4. **Poor iteration**: Small code changes required full 30-minute rebuilds

## Solution Architecture

### Two-Stage Build System

**Stage 1: DevTools Build** (Dockerfile.devtools)
- Caches expensive operations in `devtools-base` layer
- Enables fast rebuilds when Browser Operator code changes
- Produces `browser-operator-devtools:latest` image

**Stage 2: Browser Image** (Dockerfile.local)
- Copies pre-built DevTools from Stage 1
- Combines with kernel-browser runtime
- Fast final image build (~2-5 minutes)

### Directory Structure

```
web-agent/
├── .gitmodules                      # Submodule config (restored browser-operator-core)
├── .gitignore                       # Ignores DevTools build artifacts
├── Dockerfile.devtools              # NEW: DevTools builder (3 stages)
├── Dockerfile.local                 # UPDATED: Uses pre-built DevTools
├── Makefile                         # UPDATED: DevTools management targets
├── build-local.sh                   # UPDATED: Smart DevTools checks
├── run-local.sh                     # Lock file cleanup
├── docs/
│   └── devtools-build-system.md     # This file
├── DEVTOOLS-DEVELOPMENT.md          # Developer workflow guide
└── browser-operator-core/           # Submodule (shallow clone)
    ├── front_end/                   # DevTools source (modify here)
    ├── eval-server/                 # Eval server source
    └── docker/                      # Upstream Docker files
```

## Implementation Details

### 1. Submodule Configuration (.gitmodules)

```ini
[submodule "browser-operator-core"]
    path = browser-operator-core
    url = git@github.com:BrowserOperator/browser-operator-core.git
    shallow = true
```

**Key features:**
- Shallow clone (no deep recursion into Chromium submodules)
- SSH URL for authenticated access
- Separate from kernel-images submodule

### 2. DevTools Builder (Dockerfile.devtools)

**Stage 1: devtools-base (cached, ~30 min)**
```dockerfile
FROM ubuntu:22.04 AS devtools-base
# Install deps, depot_tools
# fetch devtools-frontend (~2GB)
# gclient sync
# npm run build
# Creates marker: /workspace/.devtools-base-built
```

**Stage 2: devtools-local (fast, ~5-10 min)**
```dockerfile
FROM devtools-base AS devtools-local
# Add BrowserOperator remote
# Checkout upstream/main
# (Optional: COPY local changes)
# npm run build
# Creates marker: /workspace/.devtools-built
```

**Stage 3: devtools-server (nginx)**
```dockerfile
FROM nginx:alpine AS devtools-server
# Copy built DevTools
# Configure nginx on port 8001
# Health check endpoint
```

**Build strategy:**
- Expensive operations in Stage 1 (rarely changes)
- Code changes trigger only Stage 2+ rebuild
- Docker layer caching dramatically speeds up rebuilds

### 3. Final Browser Image (Dockerfile.local)

**Before:**
```dockerfile
# DevTools builder stage (lines 4-64)
FROM ubuntu:22.04 AS devtools-builder
RUN fetch devtools-frontend  # ~2GB download every build!
...
```

**After:**
```dockerfile
# Copy from pre-built image
FROM browser-operator-devtools:latest AS devtools-source

# Final stage
COPY --from=devtools-source /usr/share/nginx/html /usr/share/nginx/devtools
```

**Benefits:**
- No expensive fetch operations
- Reuses cached DevTools build
- Fast final image assembly

### 4. Makefile Targets

**New targets:**
```makefile
init-devtools          # Initialize browser-operator-core submodule
build-devtools-base    # Build base layer (rare)
build-devtools         # Build DevTools (smart, checks cache)
rebuild-devtools       # Force rebuild after code changes
clean-devtools         # Remove DevTools images
```

**Updated targets:**
```makefile
init    # Now initializes both submodules with --depth 1
build   # Auto-calls build-devtools if needed
clean   # Preserved, separate clean-devtools for DevTools
```

### 5. Smart Build Script (build-local.sh)

**Before:**
- Removed orphaned submodules
- Full recursive submodule init

**After:**
```bash
# Shallow clone submodules
git submodule update --init --depth 1 kernel-images
git submodule update --init --depth 1 browser-operator-core

# Smart DevTools check
if ! docker images | grep -q "browser-operator-devtools.*latest"; then
    make build-devtools  # Only if missing
fi
```

**Benefits:**
- Shallow clones prevent deep recursion
- Automatic DevTools build if missing
- No orphaned submodule issues

### 6. Profile Persistence with Lock Cleanup (run-local.sh)

**Issue:** Chromium lock files persist after container crashes
**Solution:** Clean locks before each run

```bash
rm -f "$CHROMIUM_DATA_REAL/user-data/SingletonLock" \
      "$CHROMIUM_DATA_REAL/user-data/SingletonSocket" \
      "$CHROMIUM_DATA_REAL/user-data/SingletonCookie"
```

**Result:** Profile data persists, but locks don't block startup

---

## Quick Start Guide

### First Time Setup

```bash
# 1. Clone repository
git clone <your-repo>
cd web-agent

# 2. Initialize submodules
make init

# 3. Build DevTools (one-time, ~30 minutes)
make build-devtools

# 4. Build browser image (~5 minutes)
make build

# 5. Run
make run
```

**Access points:**
- WebRTC Client: http://localhost:8000
- Enhanced DevTools UI: http://localhost:8001
- Chrome DevTools: http://localhost:9222
- Eval Server: http://localhost:8080

### Daily Development Workflow

#### Editing Browser Operator Code

```bash
# 1. Edit code in browser-operator-core/
vim browser-operator-core/front_end/panels/ai_chat/AIChatPanel.ts

# 2. Rebuild DevTools (~5-10 minutes)
make rebuild-devtools

# 3. Rebuild browser image (~2-5 minutes)
make build

# 4. Run
make run
```

#### Quick Iteration (no DevTools changes)

```bash
# Just rebuild and run
make build  # Smart: skips DevTools if unchanged
make run
```

#### Switching Browser Operator Branches

```bash
cd browser-operator-core
git fetch origin
git checkout feature-branch
cd ..
make rebuild-devtools
make build
make run
```

---

## Performance Comparison

### Build Times

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| First build | ~30 min | ~30 min | Same (necessary) |
| Code change rebuild | ~30 min | ~5-10 min | **6-10x faster** |
| No DevTools change | ~30 min | ~2-5 min | **10-15x faster** |
| Submodule init | Variable | ~1 min | Faster (shallow) |

### Docker Layer Caching

**Before:**
```
RUN fetch devtools-frontend    # ❌ Always runs
RUN gclient sync               # ❌ Always runs
RUN npm run build              # ❌ Always runs
```

**After:**
```
devtools-base                  # ✅ Cached
devtools-local                 # ✅ Only rebuilds if code changed
devtools-server                # ✅ Quick nginx copy
```

---

## Troubleshooting

### Issue: "DevTools image not found"

**Solution:**
```bash
make build-devtools
```

### Issue: Submodule errors

**Solution:**
```bash
# Reset submodules
git submodule deinit -f browser-operator-core
git submodule update --init --depth 1 browser-operator-core
```

### Issue: Profile lock errors

**Solution:**
```bash
# Manual cleanup (run-local.sh does this automatically)
rm -f chromium-data/user-data/Singleton*
make run
```

### Issue: Force complete rebuild

**Solution:**
```bash
make clean-devtools
make build-devtools-base
make build-devtools
make build
```

### Issue: Out of disk space

**Solution:**
```bash
# Clean Docker cache
docker system prune -a
make clean-devtools
```

---

## Advanced Usage

### Test DevTools Standalone

```bash
docker run -p 8001:8001 browser-operator-devtools:latest
# Access at http://localhost:8001
```

### Build Only DevTools Base Layer

```bash
make build-devtools-base
# Creates browser-operator-devtools:base
# Takes ~30 minutes
```

### Use Custom Browser Operator Branch

```bash
cd browser-operator-core
git remote add myfork git@github.com:myuser/browser-operator-core.git
git fetch myfork
git checkout myfork/my-feature
cd ..
make rebuild-devtools
```

### Skip DevTools Build (Use Existing)

```bash
# build-local.sh automatically checks if image exists
./build-local.sh
```

---

## Contributing Upstream

The `Dockerfile.devtools` can be contributed to BrowserOperator as `docker/Dockerfile.dev`:

**Benefits for upstream:**
- Faster local development for all contributors
- Better Docker layer caching
- Clear separation of base dependencies vs. code changes
- Enables CI/CD optimization

**Suggested upstream PR:**
1. Add `docker/Dockerfile.dev` based on our `Dockerfile.devtools`
2. Update `docker/README.md` with development workflow
3. Add Makefile targets for dev builds

---

## Technical Decisions

### Why Shallow Submodules?

**Problem:** Chromium DevTools has massive submodule tree
**Solution:** `shallow = true` and `--depth 1` prevents deep recursion
**Tradeoff:** Can't access full git history in submodule
**Verdict:** Acceptable - we rarely need full history for local dev

### Why Separate Dockerfile.devtools?

**Alternative:** Keep everything in Dockerfile.local
**Rationale:**
- Clear separation of concerns
- Easier to contribute upstream
- Can build DevTools independently
- Better mental model for developers

### Why Not Use Browser Operator's Existing Dockerfile?

**Existing:** `browser-operator-core/docker/Dockerfile`
**Issue:** Not optimized for fast iteration (always fetches from scratch)
**Solution:** Created dev-optimized version
**Future:** Contribute improvements back upstream

### Why Makefile Instead of Shell Scripts?

**Rationale:**
- Standardized build interface
- Parallel execution support
- Better dependency management
- Familiar to developers
- Self-documenting (make help)

---

## File Changes Summary

| File | Status | Description |
|------|--------|-------------|
| `.gitmodules` | UPDATED | Restored browser-operator-core submodule |
| `.gitignore` | UPDATED | Added DevTools build artifacts |
| `Dockerfile.devtools` | NEW | 3-stage DevTools builder |
| `Dockerfile.local` | UPDATED | Uses pre-built DevTools |
| `Makefile` | UPDATED | Added DevTools targets |
| `build-local.sh` | UPDATED | Smart DevTools checks |
| `run-local.sh` | UNCHANGED | Already has lock cleanup |
| `DEVTOOLS-DEVELOPMENT.md` | NEW | Developer guide |
| `docs/devtools-build-system.md` | NEW | This file |

---

## Future Improvements

### Potential Optimizations

1. **Multi-architecture support**
   - Currently: amd64 for DevTools, arm64 for final image
   - Future: Native builds for both architectures

2. **CI/CD integration**
   - Cache devtools-base layer in registry
   - Parallel builds for different stages
   - Automated DevTools updates

3. **Development hot-reload**
   - Mount browser-operator-core/front_end/ as volume
   - Watch mode for automatic rebuilds
   - Live reload in browser

4. **Build context optimization**
   - .dockerignore improvements
   - Selective file copying
   - BuildKit cache mounts

### Monitoring Build Performance

Track build times with:
```bash
time make build-devtools
time make build
```

Expected results:
- First devtools build: ~30 minutes
- Incremental rebuild: ~5-10 minutes
- Final image: ~2-5 minutes

---

## References

- Browser Operator Core: https://github.com/BrowserOperator/browser-operator-core
- DevTools Build Guide: https://github.com/BrowserOperator/browser-operator-core/blob/main/front_end/panels/ai_chat/Readme.md
- Docker Multi-stage Builds: https://docs.docker.com/build/building/multi-stage/
- Git Submodules: https://git-scm.com/book/en/v2/Git-Tools-Submodules

---

## Support

For issues or questions:
1. Check `DEVTOOLS-DEVELOPMENT.md` for workflow guide
2. Review troubleshooting section above
3. Check Docker logs: `docker logs kernel-browser-extended`
4. Verify submodules: `git submodule status`
5. Open issue in repository with build logs
