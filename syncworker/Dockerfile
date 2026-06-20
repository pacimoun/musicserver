FROM alpine:3.23

RUN apk add --no-cache \
    bash \
    curl \
    gettext \
    jq \
    python3 \
    py3-pip \
    py3-mutagen \
    ffmpeg \
    tzdata \
    yt-dlp

ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.44/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=6eb0a8e1e6673675dc67668c1a9b6409f79c37bc \
    SUPERCRONIC=supercronic-linux-amd64

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

WORKDIR /app

COPY crontab.template /app/crontab.template
COPY scripts/ /app/scripts/

RUN chmod +x /app/scripts/*.sh && \
    chown -R 1000:1000 /app

ENTRYPOINT ["/app/scripts/entrypoint.sh"]