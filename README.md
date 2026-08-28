# Modern PDF Scanner Application

An enterprise-grade document scanning, digitizing, and OCR application built with a **React + TypeScript** frontend, **FastAPI** backend, **OpenCV** image processing, **Tesseract OCR**, **PostgreSQL** permanent storage, and **Redis** temporary preview cache.

---

## Architecture Overview

```text
ReactJS Frontend (Vite + TypeScript + Material UI)
        │
        ▼
API Gateway / FastAPI Backend
        │
 ┌──────┼───────────┐
 ▼      ▼           ▼
Postgres  Redis      PDF & Image
 (DB)    Cache   Storage Engine
        │
        ▼
 Tesseract OCR Engine
```

---

## Functional Features

### 1. Document Scanning & Live Camera Feed
- **Live Camera Viewfinder**: `react-webcam` integration with real-time framing guide overlay.
- **Auto Document Edge Detection**: OpenCV Canny edge detection & contour detection.
- **Perspective Correction (Deskew)**: 4-point perspective warp transformation.
- **Image Filters & Tone**: Magic Color Boost (shadow removal + contrast boost), B&W Adaptive Thresholding, Grayscale, and Brightness/Contrast sliders.
- **Batch & Multi-Page Scanning**: Multi-page session capture and live thumbnail previews.

### 2. OCR Engine & Document Classification
- **Tesseract OCR Integration**: Full-text extraction and detailed bounding-box metadata.
- **Automated Classification**: Automatically tags documents as Invoice, GST Bill, Receipt, Passport, PAN Card, Aadhaar Card, ID Card, or Contract.

### 3. Output Formats & PDF Engine
- **Searchable PDF**: Embedded invisible OCR text layer over page images.
- **Standard PDF**: Single and multi-page PDF generation.
- **PDF Security & Compression**: AES 128-bit PDF encryption and stream deflate compression.
- **Image Exports**: High-quality exports in JPG, PNG, and WEBP formats.
- **Split & Merge**: Reorder, split, or merge multi-page documents.

### 4. Authentication & MFA
- **Manual Signup & Login**: Secure password hashing with `passlib[bcrypt]`.
- **Social Login**: Google OAuth single-sign-on integration.
- **MFA (TOTP)**: Google & Microsoft Authenticator QR code setup and 6-digit TOTP validation.

---

## Configuration & Deployment Guide

### Prerequisites
- Docker & Docker Compose
*or*
- Python 3.12+, Node.js 22+, Tesseract OCR, PostgreSQL, Redis

---

### Running via Docker Compose (Recommended)

To launch the full stack (PostgreSQL, Redis, FastAPI Backend, React Frontend):

```bash
docker-compose up --build -d
```

The application will be accessible at:
- **Frontend App**: `http://localhost`
- **Backend API Docs**: `http://localhost:8000/docs`

---

### Local Development Setup

#### 1. Backend Setup
```bash
# Install Tesseract OCR on Linux/macOS
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng

# Install Python dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis pytesseract opencv-python-headless Pillow PyMuPDF pyotp qrcode pydantic python-jose passlib python-multipart requests httpx

# Start local PostgreSQL & Redis
sudo service postgresql start
redis-server --daemonize yes

# Start FastAPI server
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:5173`.

---

## Environment Variables

| Variable | Default Value | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/pdfscanner` | PostgreSQL connection URL |
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `JWT_SECRET` | `pdfscanner_super_secret_jwt_key_2026` | Secret key for signing JWT tokens |
| `STORAGE_DIR` | `storage` | Permanent document storage directory |

---

## Running Tests

To run the automated backend unit & integration test suite:

```bash
PYTHONPATH=. pytest backend/tests
```
