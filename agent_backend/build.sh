#!/usr/bin/env bash
# Exit on error
set -o errexit

# Build script for Render deployment
# This script handles dependency installation with error recovery

echo "=== Starting build process ==="

# Upgrade pip, setuptools, and wheel first
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
# Use longer timeout and retries for network stability
echo "Installing Python dependencies (this may take several minutes)..."
echo "Note: Large packages like torch may take 5-10 minutes to download..."

# Install dependencies with retry logic
if ! pip install --default-timeout=300 --retries 5 -r requirements.txt; then
    echo "First install attempt failed, retrying with longer timeout..."
    sleep 10
    if ! pip install --default-timeout=600 --retries 10 -r requirements.txt; then
        echo "Second install attempt failed."
        echo "Trying to install core dependencies first..."
        
        # Install core dependencies first
        pip install --default-timeout=600 --retries 10 \
            Django==4.2.26 \
            django-ninja==1.4.5 \
            gunicorn==21.2.0 \
            whitenoise==6.7.0 \
            psycopg2-binary==2.9.9 \
            dj-database-url==2.1.0 \
            chromadb==1.3.3 \
            langchain==0.3.27 \
            langchain-community==0.3.31 \
            langchain-core==0.3.79 \
            langchain-text-splitters==0.3.11 \
            google-generativeai==0.8.5 \
            pdfplumber==0.11.7 \
            PyPDF2==3.0.1 \
            pandas==2.3.3 \
            openpyxl==3.1.5
        
        # Then install sentence-transformers (may pull in torch, transformers, etc.)
        echo "Installing sentence-transformers (this may take a while)..."
        pip install --default-timeout=600 --retries 10 sentence-transformers==5.1.2 || {
            echo "Warning: sentence-transformers installation failed, but continuing..."
        }
        
        # Install remaining dependencies
        echo "Installing remaining dependencies..."
        pip install --default-timeout=600 --retries 10 -r requirements.txt || {
            echo "Error: Some dependencies failed to install, but continuing with build..."
        }
    fi
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# Create necessary directories for ChromaDB and PDFs
echo "Creating directories for ChromaDB and PDFs..."
# On Render, use persistent disk mount
CHROMA_DIR="/opt/render/project/src/ragImplementation"
mkdir -p "$CHROMA_DIR/chroma_db"
mkdir -p "$CHROMA_DIR/pdfs"
mkdir -p "$CHROMA_DIR/temp_uploads"

# Also create locally for fallback (in case persistent disk is not mounted)
mkdir -p ../ragImplementation/chroma_db || true
mkdir -p ../ragImplementation/pdfs || true
mkdir -p ../ragImplementation/temp_uploads || true

# Verify critical packages are installed
echo "Verifying critical installations..."
python -c "import django; print(f'✓ Django {django.get_version()}')" || { echo "✗ Django not installed"; exit 1; }
python -c "import chromadb; print('✓ ChromaDB installed')" || { echo "✗ ChromaDB not installed"; exit 1; }

echo "=== Build completed successfully! ==="
