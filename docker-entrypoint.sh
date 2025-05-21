#!/bin/bash
set -e

# Run collectstatic only if STATIC_ROOT is set and we're in production mode
if [ -d "/app" ]; then
  cd /app
  
  # Create logs directory if it doesn't exist
  mkdir -p /app/logs
  touch /app/logs/query_performance.log
  chmod -R 777 /app/logs
  
  # Create static and media directories
  mkdir -p /app/staticfiles
  mkdir -p /app/media
  chmod -R 755 /app/staticfiles
  chmod -R 755 /app/media
  
  # Ensure Gunicorn config is accessible
  if [ -f "/app/gunicorn.conf.py" ]; then
    echo "Gunicorn configuration found."
    chmod 644 /app/gunicorn.conf.py
  else
    echo "Warning: gunicorn.conf.py not found. Using default settings."
  fi
  
  # Skip collectstatic unless explicitly requested to run it
  if [ "$DJANGO_SKIP_COLLECTSTATIC" != "1" ]; then
    echo "Running collectstatic..."
    python manage.py collectstatic --noinput --verbosity 1 || {
      echo "Warning: collectstatic failed, but continuing anyway..."
    }
  else
    echo "Skipping collectstatic (DJANGO_SKIP_COLLECTSTATIC=1)"
  fi
  
  # Apply database migrations
  echo "Applying database migrations..."
  python manage.py migrate --noinput || {
    echo "Warning: migrations failed, but continuing anyway..."
  }
fi

# Execute the command provided as arguments
exec "$@"
