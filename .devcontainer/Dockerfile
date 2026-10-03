FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG RGBDS_VERSION=v1.0.4
ARG SAMEBOY_VERSION=v1.0.1
ARG NOVNC_VERSION=v1.7.0
ARG MGBDIS_COMMIT=95d951a9881a0d7ff1a42a94d1be175da92b1777

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential clang cmake pkg-config bison flex git ca-certificates curl wget unzip \
    python3 python3-pip python3-venv python3-pil python3-yaml \
    libpng-dev libsdl2-dev libzstd-dev \
    xxd jq ripgrep file bc less vim-tiny \
    xvfb x11vnc openbox xterm dbus-x11 x11-utils websockify supervisor \
 && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${RGBDS_VERSION}" https://github.com/gbdev/rgbds.git /tmp/rgbds \
 && make -C /tmp/rgbds -j"$(nproc)" \
 && make -C /tmp/rgbds install \
 && rm -rf /tmp/rgbds

RUN git clone --depth 1 --branch "${SAMEBOY_VERSION}" https://github.com/LIJI32/SameBoy.git /tmp/SameBoy \
 && make -C /tmp/SameBoy -j"$(nproc)" CONF=release \
 && test -x /tmp/SameBoy/build/bin/SDL/sameboy \
 && mkdir -p /opt/sameboy \
 && cp -a /tmp/SameBoy/build/bin/SDL/. /opt/sameboy/ \
 && printf '#!/bin/sh\nexec /opt/sameboy/sameboy "$@"\n' > /usr/local/bin/sameboy \
 && chmod 0755 /usr/local/bin/sameboy /opt/sameboy/sameboy \
 && rm -rf /tmp/SameBoy

RUN git init /opt/mgbdis \
 && cd /opt/mgbdis \
 && git remote add origin https://github.com/mattcurrie/mgbdis.git \
 && git fetch --depth 1 origin "${MGBDIS_COMMIT}" \
 && git checkout --detach FETCH_HEAD \
 && test "$(git rev-parse HEAD)" = "${MGBDIS_COMMIT}" \
 && ln -s /opt/mgbdis/mgbdis.py /usr/local/bin/mgbdis \
 && chmod 0755 /opt/mgbdis/mgbdis.py \
 && mgbdis --help >/dev/null

RUN git clone --depth 1 --branch "${NOVNC_VERSION}" https://github.com/novnc/noVNC.git /opt/novnc \
 && ln -s /opt/novnc/vnc.html /opt/novnc/index.html

WORKDIR /workspaces
