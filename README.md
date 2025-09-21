# Resume Matcher (Streamlit) — Two-way Portal (Companies & Candidates)

This is a Streamlit single-app implementation of a two-sided resume ↔ job matching platform.
- Companies (recruiters) can post Job Descriptions (JDs) with must-have and nice-to-have skills.
- Candidates upload resumes (PDF/DOCX).
- The system computes hard (keyword) and soft (semantic) matches and generates a combined 0–100 score and verdict (High/Medium/Low).
- Candidates can see suggestions for improvement; companies can view ranked candidate lists and download CSV reports.

## Features
- Multi-company, multi-candidate matching
- Hard keyword matching and TF-IDF/fallback logic
- Sentence-transformers embeddings (all-MiniLM-L6-v2) for semantic similarity (no paid API)
- SQLite DB (single file) for ease of deployment
- CSV export of matches

## Setup (Windows)
1. Install Python 3.10+ and VS Code.
2. Open VS Code and open this project folder.
3. Create virtual environment and install dependencies:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
