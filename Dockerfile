FROM python:3.14-slim

# Print log lines as they happen, so `docker compose logs -f` is live.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# A fixed UID, so the host's ./data folder can be chowned to match (see README).
RUN useradd --uid 1000 --no-create-home --shell /usr/sbin/nologin btw \
    && mkdir /data && chown btw:btw /data

WORKDIR /app
COPY btw_bot ./btw_bot

USER btw
CMD ["python", "-m", "btw_bot"]
