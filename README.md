# FEFO Pharmacy Inventory Manager

## Overview
The **FEFO Pharmacy Inventory Manager** is a production-ready, full-stack neighbourhood pharmacy management system engineered to enforce strict **First-Expiry-First-Out (FEFO)** dispensing principles. The application guarantees that expired batches are automatically quarantined, sellable stock is tracked dynamically in real-time, and impending stock shortages or expirations trigger automated notifications.

---

## Key Features & Architecture
- **Strict FEFO Dispensing Algorithm**: Automatically prioritizes and deducts inventory from batches expiring soonest, avoiding expired stock entirely.
- **Safety Buffer Validation (`course_duration_days`)**: Prevents medical errors by verifying that a batch will not expire before a patient's treatment course is completed.
- **Automated Expiry Clock (`/clock`)**: Daily simulation endpoint that automatically quarantines expired inventory and reports counts of batches expiring within a 7-day window.
- **Messy Data Import Engine (`/import`)**: Robust batch ingestion capable of sanitizing missing fields, stripping textual noise from quantities (e.g., `"10 units"`), handling mixed date formats (`YYYY-MM-DD` vs `DD/MM/YYYY`), and preventing duplicates.
- **Threshold Re-order Outbox (`/outbox`)**: Event-driven notification service that queues re-order alerts when a medicine's in-date stock drops below the safety threshold (20 units).
- **Secure Authentication**: Token-based security using JSON Web Tokens (JWT) and secure password hashing (`bcrypt`).

---

## Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic, Passlib, python-jose (JWT)
- **Database**: SQLite (`pharmacy.db`)
- **Frontend**: Single-Page Application (SPA) built with Vanilla JavaScript and Tailwind CSS

---

## Setup & Execution Guide

### 1. Prerequisites
Ensure you have Python 3.8+ installed along with `pip`.

### 2. Install Dependencies
Navigate to your project root directory and run:
```bash
pip install -r requirements.txt