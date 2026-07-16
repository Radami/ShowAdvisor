# Single image for all backend services (spec §7): the same build is run as
# `web` now, and later as `worker` and `beat` with different start commands.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Test tooling is opt-in so the production image stays lean; docker-compose
# builds with INSTALL_DEV=true.
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

COPY . .

EXPOSE 8000

# Production default; docker-compose overrides this with the dev server.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
