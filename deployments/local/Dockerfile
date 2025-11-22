# Extended Dockerfile combining kernel-images with DevTools frontend
# This extends the kernel-images base with Browser Operator DevTools static files
#
# NOTE: DevTools are built separately using Dockerfile.devtools
# Run 'make build-devtools' first to build the DevTools image

# ============================================================================
# DevTools stage - Copy from pre-built devtools image
# ============================================================================
FROM browser-operator-devtools:latest AS devtools-source

# ============================================================================
# Eval Server build stage
# ============================================================================
FROM --platform=linux/arm64 node:18-alpine AS browser-agent-server-builder

WORKDIR /workspace

# Copy agent server from browser-operator-core submodule
COPY submodules/browser-operator-core/agent-server/nodejs /workspace/browser-agent-server

WORKDIR /workspace/browser-agent-server

# Install dependencies
RUN npm install

# ============================================================================
# Use kernel-images base with DevTools integration
# ============================================================================
FROM --platform=linux/arm64 docker.io/golang:1.25.0 AS server-builder
WORKDIR /workspace/server

ARG TARGETOS
ARG TARGETARCH
ENV CGO_ENABLED=0

COPY submodules/kernel-images/server/go.mod ./
COPY submodules/kernel-images/server/go.sum ./
RUN go mod download

COPY submodules/kernel-images/server/ .
RUN GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-arm64} \
    go build -ldflags="-s -w" -o /out/kernel-images-api ./cmd/api

# webrtc client
FROM --platform=linux/arm64 node:22-bullseye-slim AS client
WORKDIR /src
COPY submodules/kernel-images/images/chromium-headful/client/package*.json ./
RUN npm install
COPY submodules/kernel-images/images/chromium-headful/client/ .
RUN npm run build

# xorg dependencies
FROM --platform=linux/arm64 docker.io/ubuntu:22.04 AS xorg-deps
WORKDIR /xorg
ENV DEBIAN_FRONTEND=noninteractive
RUN set -eux; \
    apt-get update; \
    apt-get install -y \
    git gcc pkgconf autoconf automake libtool make xorg-dev xutils-dev \
    && rm -rf /var/lib/apt/lists/*;
COPY submodules/kernel-images/images/chromium-headful/xorg-deps/ /xorg/
# build xf86-video-dummy v0.3.8 with RandR support
RUN set -eux; \
    cd xf86-video-dummy/v0.3.8; \
    patch -p1 < ../01_v0.3.8_xdummy-randr.patch; \
    autoreconf -v --install; \
    ./configure; \
    make -j$(nproc); \
    make install;
# build custom input driver
RUN set -eux; \
    cd xf86-input-neko; \
    ./autogen.sh --prefix=/usr; \
    ./configure; \
    make -j$(nproc); \
    make install;

FROM --platform=linux/arm64 ghcr.io/onkernel/neko/base:3.0.6-v1.0.1 AS neko
# ^--- now has event.SYSTEM_PONG with legacy support to keepalive

# Final stage: kernel-images base + DevTools static files
FROM --platform=linux/arm64 docker.io/ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_PRIORITY=high

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install \
    # UI Requirements
    xvfb \
    xterm \
    xdotool \
    scrot \
    imagemagick \
    sudo \
    mutter \
    # Python/pyenv reqs
    build-essential \
    libssl-dev  \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    curl \
    git \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    # Network tools
    net-tools \
    netcat \
    # PPA req
    software-properties-common \
    # Add nginx for DevTools serving
    nginx \
    # Userland apps
    && apt-get install -y --no-install-recommends \
    libreoffice \
    x11-apps \
    xpdf \
    gedit \
    xpaint \
    tint2 \
    galculator \
    pcmanfm \
    wget \
    xdg-utils \
    libvulkan1 \
    fonts-liberation \
    unzip && \
    apt-get clean

# install ffmpeg manually since the version available in apt is from the 4.x branch due to #drama.
# as of writing these static builds will be the latest 7.0.x release.
RUN set -eux; \
    URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"; \
    echo "Downloading FFmpeg static build from $URL"; \
    curl -fsSL "$URL" -o /tmp/ffmpeg.tar.xz; \
    tar -xJf /tmp/ffmpeg.tar.xz -C /tmp; \
    install -m755 /tmp/ffmpeg-*/ffmpeg  /usr/local/bin/ffmpeg; \
    install -m755 /tmp/ffmpeg-*/ffprobe /usr/local/bin/ffprobe; \
    rm -rf /tmp/ffmpeg*

# runtime
ENV USERNAME=root
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
    wget ca-certificates python2 supervisor xclip xdotool \
    pulseaudio dbus-x11 xserver-xorg-video-dummy \
    libcairo2 libxcb1 libxrandr2 libxv1 libopus0 libvpx7 \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gstreamer1.0-pulseaudio gstreamer1.0-omx; \
    #
    # install libxcvt0 (not available in debian:bullseye)
    ARCH=$(dpkg --print-architecture); \
    wget http://ftp.de.debian.org/debian/pool/main/libx/libxcvt/libxcvt0_0.1.2-1_${ARCH}.deb; \
    apt-get install --no-install-recommends ./libxcvt0_0.1.2-1_${ARCH}.deb; \
    rm ./libxcvt0_0.1.2-1_${ARCH}.deb; \
    #
    # workaround for an X11 problem: http://blog.tigerteufel.de/?p=476
    mkdir /tmp/.X11-unix; \
    chmod 1777 /tmp/.X11-unix; \
    chown $USERNAME /tmp/.X11-unix/; \
    #
    # make directories for neko
    mkdir -p /etc/neko /var/www /var/log/neko \
    /tmp/runtime-$USERNAME \
    /home/$USERNAME/.config/pulse  \
    /home/$USERNAME/.local/share/xorg; \
    chmod 1777 /var/log/neko; \
    chown $USERNAME /var/log/neko/ /tmp/runtime-$USERNAME; \
    chown -R $USERNAME:$USERNAME /home/$USERNAME; \
    # clean up
    apt-get clean -y; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/

# install chromium and sqlite3 for debugging the cookies file
RUN add-apt-repository -y ppa:xtradeb/apps
RUN apt update -y && apt install -y chromium sqlite3

# setup desktop env & app
ENV DISPLAY_NUM=1
ENV HEIGHT=768
ENV WIDTH=1024
ENV WITHDOCKER=true

# Copy kernel-images configuration and binaries
COPY submodules/kernel-images/images/chromium-headful/xorg.conf /etc/neko/xorg.conf
COPY submodules/kernel-images/images/chromium-headful/neko.yaml /etc/neko/neko.yaml
COPY --from=neko /usr/bin/neko /usr/bin/neko
COPY --from=client /src/dist/ /var/www
COPY --from=xorg-deps /usr/local/lib/xorg/modules/drivers/dummy_drv.so /usr/lib/xorg/modules/drivers/dummy_drv.so
COPY --from=xorg-deps /usr/local/lib/xorg/modules/input/neko_drv.so /usr/lib/xorg/modules/input/neko_drv.so

COPY submodules/kernel-images/images/chromium-headful/image-chromium/ /
COPY submodules/kernel-images/images/chromium-headful/wrapper.sh /wrapper.sh
COPY submodules/kernel-images/images/chromium-headful/supervisord.conf /etc/supervisor/supervisord.conf
COPY submodules/kernel-images/images/chromium-headful/supervisor/services/ /etc/supervisor/conf.d/services/

# Override chromium.conf with local version that includes auto-open-devtools
COPY deployments/commons/supervisor/services/chromium.conf /etc/supervisor/conf.d/services/chromium.conf

# copy the kernel-images API binary built in the builder stage
COPY --from=server-builder /out/kernel-images-api /usr/local/bin/kernel-images-api

# ============================================================================
# DevTools Integration
# ============================================================================

# Copy DevTools static files from pre-built devtools image
COPY --from=devtools-source /usr/share/nginx/html /usr/share/nginx/devtools

# Create DevTools nginx configuration
COPY deployments/commons/nginx/nginx-devtools.conf /etc/nginx/sites-available/devtools
RUN ln -s /etc/nginx/sites-available/devtools /etc/nginx/sites-enabled/devtools && \
    rm /etc/nginx/sites-enabled/default

# Add DevTools nginx service to supervisor
COPY deployments/commons/supervisor/services/nginx-devtools.conf /etc/supervisor/conf.d/services/nginx-devtools.conf

# Add eval server service to supervisor
COPY deployments/commons/supervisor/services/browser-agent-server.conf /etc/supervisor/conf.d/services/browser-agent-server.conf

# Add neko service to supervisor (configured for port 8000)
COPY deployments/commons/supervisor/services/neko.conf /etc/supervisor/conf.d/services/neko.conf

# Create nginx temp directories and set permissions
RUN mkdir -p /var/lib/nginx/body \
             /var/lib/nginx/proxy \
             /var/lib/nginx/fastcgi \
             /var/lib/nginx/uwsgi \
             /var/lib/nginx/scgi && \
    chown -R www-data:www-data /var/lib/nginx && \
    chown -R www-data:www-data /usr/share/nginx/devtools

RUN useradd -m -s /bin/bash kernel

# ============================================================================
# Eval Server Integration
# ============================================================================

# Copy eval server from builder
COPY --from=browser-agent-server-builder /workspace/browser-agent-server /opt/browser-agent-server

# Install Node.js in final image for eval server
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create eval server startup script
RUN echo '#!/bin/bash\ncd /opt/browser-agent-server && node start.js' > /usr/local/bin/start-browser-agent-server.sh && \
    chmod +x /usr/local/bin/start-browser-agent-server.sh

# ============================================================================
# Chromium Data Directory Configuration
# ============================================================================

# Environment variable for configurable data directory
ENV CHROMIUM_DATA_DIR=/data

# Create data directory structure for optional volume mounting
RUN mkdir -p /data/user-data /data/config /data/cache && \
    chown -R kernel:kernel /data && \
    chmod -R 755 /data

# Declare volume for optional mounting of Chromium profiles and data
VOLUME ["/data"]

# ============================================================================
# Container Initialization Script
# ============================================================================

# Copy container initialization script that cleans up lock files
COPY deployments/local/scripts/init-container.sh /usr/local/bin/init-container.sh
RUN chmod +x /usr/local/bin/init-container.sh

# Copy patched start-chromium.sh that properly quotes CHROMIUM_FLAGS
COPY deployments/local/scripts/start-chromium.sh /images/chromium-headful/start-chromium.sh
RUN chmod +x /images/chromium-headful/start-chromium.sh

# Create a wrapper entrypoint that runs init script before main wrapper
RUN echo '#!/bin/bash\n\
set -e\n\
# Run initialization script\n\
/usr/local/bin/init-container.sh\n\
# Execute main wrapper\n\
exec /wrapper.sh "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Expose ports
EXPOSE 8000 8001 8080 8081 8082

ENTRYPOINT [ "/entrypoint.sh" ]