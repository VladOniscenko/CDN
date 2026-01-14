# Simple Python CDN

A minimal CDN service built with FastAPI for securely uploading, managing, and serving static files.

## Features

- Public file delivery via /cdn/*
- Password-protected admin panel (HTTP Basic)
- File upload with type validation (images, PDF)
- Directory management (create, browse, delete)
- HTML admin UI (Jinja2)
- Docker-friendly

## Tech Stack

- Python 3
- FastAPI
- Jinja2
- dotenv

## Supported Files

- JPG / JPEG
- PNG
- GIF
- PDF

## Environment

ADMIN_PASSWORD=changeme

## Run

uvicorn app.main:app --host 0.0.0.0 --port 8000

## Endpoints

- /cdn/{path}        public file access
- /download/{path}   public download
- /                  admin browse (protected)
- /upload             upload files
- /mkdir              create directory
- /delete             delete file or empty directory

## Use Case

Private asset storage with public CDN-style delivery.

---

Developed by Vlad
