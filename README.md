# 🧠 Automated Resume Relevance Checker 
# (Two way Portal - For Candidates & Companies)

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python&logoColor=white) 
![Streamlit](https://img.shields.io/badge/Streamlit-1.27.0-orange?style=flat-square&logo=streamlit&logoColor=white) 
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=flat-square&logo=sqlite&logoColor=white) 
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visuals-purple?style=flat-square&logo=matplotlib&logoColor=white) 

### Key Features
![Candidate](https://img.shields.io/badge/👤-Candidate-blue?style=flat-square) 
![Company](https://img.shields.io/badge/🏢-Company-green?style=flat-square) 
![Security](https://img.shields.io/badge/🔐-Secure-red?style=flat-square) 
![Visuals](https://img.shields.io/badge/📊-Visuals-yellow?style=flat-square) 
![Feedback](https://img.shields.io/badge/💡-Feedback-purple?style=flat-square) 
![Batch](https://img.shields.io/badge/📂-Batch_Analysis-orange?style=flat-square) 

---

> **Quick Start / Demo** 🚀  
> Get the app running in under 2 minutes:  
> 1️⃣ Clone repo: `git clone https://github.com/your-username/resume-matcher.git && cd resume-matcher`  
> 2️⃣ Create virtual environment: `python -m venv venv && source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)  
> 3️⃣ Install dependencies: `pip install -r requirements.txt`  
> 4️⃣ Run the app: `streamlit run app.py`  
> Open `http://localhost:8501` in your browser and start using the dashboard!

---

This project is a **multi-role web dashboard** that automatically matches resumes to job descriptions (JD), provides AI-driven feedback to candidates, and allows companies to perform batch resume analysis. It combines **text similarity**, **keyword matching**, and visual dashboards to make recruitment and self-assessment smarter and easier.

---

## 🚀 Features

### **Candidate Features**
✅ Upload and parse resumes (PDF, DOCX, TXT)  
✅ Auto-match resumes against available job descriptions  
✅ Compute **Overall Match Score**, **Text Similarity**, and **Skill Match Score**  
✅ Receive actionable **AI-powered feedback** highlighting strengths and areas to improve  
✅ View **past uploads and match history** in a clean, interactive table  
✅ Visual **pie charts** for matched vs missing skills  

### **Company Features**
✅ Upload job descriptions (PDF, DOCX, TXT)  
✅ Batch match a job description against all uploaded resumes  
✅ Quickly identify **best-fitting resumes**  
✅ View all matches with **score metrics** and small visual indicators  
✅ Extract **top keywords** from job descriptions  

### **Account & Security**
✅ Multi-role dashboards for candidates and companies  
✅ Login and Sign-Up with secure password hashing  
✅ Role-based access ensures candidates see detailed feedback while companies see only match scores  

---

## ⚙️ Tech Stack

| Category           | Tools & Libraries                         |
|-------------------|------------------------------------------|
| Frontend           | Streamlit                                |
| Backend / ORM      | Python + SQLAlchemy                       |
| Database           | SQLite                                   |
| File Parsing       | python-docx, PyPDF2, plain text          |
| Matching & Scoring | Text similarity, keyword matching logic  |
| Visualization      | Matplotlib (pie charts)                   |

---

## 🧠 Logic Breakdown

1. **Resume & JD Parsing**  
   - Supports PDF, DOCX, and TXT formats  
   - Extracts clean text from uploaded files  

2. **Skill Extraction & Matching**  
   - Extracts keywords and skills from JD  
   - Matches resume content with required skills  
   - Computes **matched** and **missing** skills  

3. **Scoring**  
   - **Overall Score** combines text similarity and skill match  
   - **Text Similarity** → measures semantic similarity between resume and JD  
   - **Skill Match** → calculates percentage of matched vs missing skills  

4. **AI Feedback (for Candidates)**  
   - Generates actionable feedback highlighting strengths and areas to improve  
   - Feedback displayed in bullet points along with visual pie charts  

5. **Company Batch Analysis**  
   - Match a JD against multiple resumes  
   - Display best-fit resumes with scores and small visual indicators  

6. **Storage & Dashboard**  
   - Results stored in **SQLite** database  
   - Interactive Streamlit dashboard: upload, view metrics, history, and charts  

---

## 🛠 Local Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/resume-matcher.git
cd resume-matcher
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the App
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser to access the dashboard.

---

## 📁 Directory Structure
```
resume-matcher/
│
├── app.py                 # Main Streamlit app
├── db.py                  # Database models & session setup
├── utils.py               # Resume/JD parsing and scoring logic
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── .venv/                 # Virtual environment (optional)
```

---

## 🌐 Deployment Instructions
- Push code to GitHub  
- Deploy on Streamlit Cloud or any Python web server  
- Ensure `app.py`, database (`SQLite`) and dependencies are included  
- Access the dashboard via browser  

---

## 🎨 Theme & UI
- Clean and professional layout with **columns and cards**  
- Visual **pie charts** for skill match metrics  
- Dashboard supports **multi-role navigation** with sidebar  

---

## 🧹 Optional: Clear Database
```python
from db import SessionLocal, Resume, Match, Job

db = SessionLocal()
db.query(Match).delete()
db.query(Resume).delete()
db.commit()
```

---

## 🔐 Security & Best Practices
- Use `.gitignore` to avoid committing the virtual environment or sensitive files  
- Store uploaded files and database in controlled directories  
- Use virtual environments for isolated dependencies  

---

## 📌 Future Enhancements
- Advanced NLP scoring for semantic understanding  
- Export candidate reports as PDF  
- Mini-charts in candidate history for visual performance tracking  
- Email notifications for new job postings



