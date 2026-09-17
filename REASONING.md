# Architectural Reasoning & Design Decisions

## 1. Monolithic Architecture & Technology Stack Selection
Given the compressed 2.5-hour development timeframe and the requirement for rapid feature expansion, architectural simplicity and execution speed were prioritized over over-engineered microservices.
* **FastAPI (Python):** Chosen for its high performance, native asynchronous capabilities, automatic data validation via Pydantic, and self-documenting Swagger UI (`/docs`), which drastically cuts down frontend debugging time.
* **SQLite & SQLAlchemy:** A file-based SQL database provides robust relational integrity, foreign key support, and ACID compliance for inventory counts without requiring external database containerization or cloud setup.
* **Monolithic SPA Serving:** Having FastAPI serve the static frontend directory (`static/`) directly completely eliminates CORS configuration overhead and multi-service deployment friction.

## 2. Core Business Logic: The Dispensing Buffer
A naive FEFO system sorts by expiry date and blindly deducts stock. However, in a real medical context, dispensing a batch that expires in 5 days for a 30-day medication course is dangerous and leads to patient harm. 
* **The Solution:** The backend accepts a `course_duration_days` parameter. It calculates a safety threshold date (`date.today() + course_duration_days`) and filters out any batches expiring before that threshold. This forces the system to cascade into longer-dated batches, prioritizing patient safety over raw inventory rotation.

## 3. Implementation of Evaluation Twists
* **Level 1 (`POST /clock`):** Designed as an idempotent daily cron simulation. It queries items past their expiry date, updates their database status column to `"quarantined"` (removing them from sellable inventory calculations), and queries short-term items for proactive alerting.
* **Level 2 (`POST /import`):** Real-world data ingestion is messy. The import pipeline employs Python regular expressions (`re.search`) to isolate digits from messy strings (e.g., converting `"50 boxes"` or `"10 units"` into clean integers), dual-format date parsing to accommodate both ISO and European date standards (`DD/MM/YYYY`), null validators, and composite deduplication checking against both the incoming batch payload and the active database state.
* **Level 3 (`GET /outbox`):** Implements an event-driven notification pattern. When a dispense operation reduces a medicine's sellable stock below the configured threshold (20 units), an alert payload is appended to an in-memory outbox array, complete with a deduplication check to prevent alert spamming during multiple rapid dispensations.

## 4. Stability & Compatibility Fixes
* **The Passlib/Bcrypt Issue:** During initial setup, password hashing triggered a backend crash due to a known version mismatch between modern `bcrypt` libraries and `passlib` handling 72-byte password limits. This was cleanly resolved by pinning `bcrypt<4.0.0` in the dependency configuration.