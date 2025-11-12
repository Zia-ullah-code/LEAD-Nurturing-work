#!/usr/bin/env bash
# Exit on error
set -o errexit

# Build script for Render deployment

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install whitenoise for static files
pip install whitenoise

# Install psycopg2 for PostgreSQL
pip install psycopg2-binary

# Install dj-database-url for database configuration
pip install dj-database-url

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate --no-input

# Create necessary directories for ChromaDB and PDFs
# Note: On Render, these should be in the persistent disk mount
CHROMA_DIR="/opt/render/project/src/ragImplementation"
mkdir -p "$CHROMA_DIR/chroma_db"
mkdir -p "$CHROMA_DIR/pdfs"
mkdir -p "$CHROMA_DIR/temp_uploads"

# Also create locally for fallback
mkdir -p ../ragImplementation/chroma_db
mkdir -p ../ragImplementation/pdfs
mkdir -p ../ragImplementation/temp_uploads

# If you need to initialize ChromaDB with existing PDFs, uncomment the following:
# python -c "import sys; sys.path.append('../ragImplementation'); from rag_main import build_chroma_db; build_chroma_db()"

echo "Build completed successfully!"

