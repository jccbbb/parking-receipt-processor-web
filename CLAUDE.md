# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask web application for processing Parkster parking receipts PDFs. The app removes duplicate receipts, sorts them by ticket number, and calculates total amounts in Swedish currency (SEK).

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Run with gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Build Docker image
docker build -t parking-receipt-processor .

# Run Docker container
docker run -p 5000:5000 parking-receipt-processor
```

## Architecture

### Core Components

- **app.py**: Flask application with routes for upload, processing, status checking, and file downloads. Uses session-based processing with unique IDs for concurrent users.

- **pdf_processor.py**: Main processing logic using pdfplumber and PyPDF2. Extracts ticket numbers and amounts, identifies duplicates, and generates sorted output PDFs.

- **utils.py**: Helper functions for Swedish currency formatting, ticket number extraction (9-digit patterns), and Brutto amount parsing from various text formats.

### Processing Flow

1. User uploads PDF via web interface
2. Server generates unique session ID and saves file to temp directory
3. ParkingReceiptProcessor extracts data from each page (ticket number, brutto amount, date)
4. Duplicates are identified and removed based on ticket numbers
5. Receipts are sorted by ticket number
6. New PDF is generated with only unique, sorted receipts
7. Summary text file is created with statistics and detailed receipt list
8. Files are available for download (processed PDF and summary text)

### Key Features

- Handles Swedish parking receipts with "Brutto" amounts in SEK/kr
- Extracts 9-digit ticket numbers using multiple regex patterns
- Progress tracking with callbacks during processing
- Session-based file management with cleanup endpoints
- 100MB file size limit
- Error handling and validation throughout