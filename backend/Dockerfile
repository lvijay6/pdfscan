FROM python:3.12-slim

# Install system dependencies including Tesseract OCR and OpenCV requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY backend/app /app/backend/app
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    redis \
    pytesseract \
    opencv-python-headless \
    Pillow \
    PyMuPDF \
    pyotp \
    qrcode \
    pydantic \
    python-jose \
    passlib \
    python-multipart \
    requests \
    httpx

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
