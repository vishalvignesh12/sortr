#!/bin/bash

echo "Waiting for database to be ready..."
sleep 2

echo "Initializing database schema (if needed)..."
python app/scripts/init_db.py 2>&1 || echo "Schema already exists or initialization failed"

echo "Seeding initial data (if needed)..."
python app/scripts/seed_slots.py 2>&1 || echo "Data seeding skipped or failed"

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
