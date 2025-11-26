#!/bin/bash
set -e

echo "===== Pack-A-Mal Backend Starting ====="

echo "Waiting for database at $POSTGRES_HOST:$POSTGRES_PORT..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  echo "  Database not ready yet, waiting..."
  sleep 0.5
done
echo "Database is ready!"

echo "Running migrations..."
python manage.py migrate --noinput
echo "Migrations complete!"

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "Static files collected!"

echo "===== Starting Django development server ====="
exec "$@"
