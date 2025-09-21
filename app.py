import streamlit as st
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import json

from db import SessionLocal, Job, Resume, Match, User
from utils import parse_uploaded_file, compute_match_and_feedback, extract_keywords
from werkzeug.security import generate_password_hash, check_password_hash

st.set_page_config(page_title="Automated Resume Relevance Checker", page_icon="🧠", layout="wide")

# -------------------- CSS --------------------
st.markdown("""
<style>
.header { background: linear-gradient(90deg, #7b2ff7, #f107a3); padding: 18px; border-radius: 12px; color: white; }
.card { border-radius: 12px; padding: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); background: linear-gradient(180deg, #ffffff, #f7f7ff); }
.big-score { font-size: 48px; font-weight: 700; margin: 6px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><h1>🧠 Automated Resume Relevance Checker</h1></div>', unsafe_allow_html=True)

# -------------------- DB session --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db = next(get_db())

# -------------------- Login / Sign Up --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

def login():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = db.query(User).filter(User.username==username).first()
        if user and user.check_password(password):
            st.session_state.logged_in = True
            st.session_state.role = user.role
            st.session_state.username = username
            st.success(f"Logged in as {username} ({user.role})")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

def signup():
    st.subheader("Sign Up")
    username = st.text_input("Choose a username", key="su_username")
    password = st.text_input("Choose a password", type="password", key="su_password")
    role = st.selectbox("Select role", ["candidate","company"], key="su_role")
    if st.button("Sign Up"):
        if db.query(User).filter(User.username==username).first():
            st.error("Username already exists")
        else:
            user = User(username=username, role=role)
            user.set_password(password)
            db.add(user)
            db.commit()
            st.success(f"User {username} created. Please log in.")

if not st.session_state.logged_in:
    st.sidebar.title("Account")
    option = st.sidebar.radio("Choose", ["Login","Sign Up"])
    if option=="Login":
        login()
    else:
        signup()
else:
    st.sidebar.title(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.experimental_rerun()

# -------------------- Navigation --------------------
if st.session_state.logged_in:
    if st.session_state.role=="company":
        page = st.sidebar.radio("Go to", ["📄 Upload Job", "📊 View Matches"])
    else:
        page = st.sidebar.radio("Go to", ["🧾 Upload Resume & Auto-Match", "📊 My Match History"])

    # -------------------- Company Pages --------------------
    if st.session_state.role=="company":

        if page=="📄 Upload Job":
            st.header("📄 Upload Job Description")
            with st.form("job_form"):
                jd_title = st.text_input("Job title", placeholder="e.g. Senior Data Scientist")
                jd_file = st.file_uploader("Upload JD (pdf/docx/txt)", type=["pdf","docx","txt"])
                submit = st.form_submit_button("➕ Add Job")
            if submit:
                if not jd_title:
                    st.error("Enter job title")
                else:
                    jd_text = parse_uploaded_file(jd_file) if jd_file else ""
                    job = Job(title=jd_title, description_text=jd_text, created_at=datetime.utcnow())
                    db.add(job); db.commit(); db.refresh(job)
                    st.success(f"Job '{jd_title}' saved ✅")
                    kw = extract_keywords(jd_text or jd_title, top_n=10)
                    if kw:
                        st.markdown("**🔑 Top JD keywords:** " + ", ".join(kw))

        elif page=="📊 View Matches":
            st.header("📊 Batch Resume Matching for Jobs")
            jobs = db.query(Job).order_by(Job.created_at.desc()).all()
            resumes = db.query(Resume).all()
            if not jobs:
                st.info("No jobs uploaded yet")
            elif not resumes:
                st.info("No resumes uploaded yet")
            else:
                sel_job = st.selectbox("Select a Job to batch match", [j.title for j in jobs])
                job_obj = next(j for j in jobs if j.title==sel_job)
                if st.button("Run Batch Match"):
                    results=[]
                    for r in resumes:
                        match_result = compute_match_and_feedback(r.content_text, job_obj.description_text)
                        results.append({
                            "resume": r.filename,
                            "score": round(match_result["score"],1)
                        })
                    df = pd.DataFrame(results).sort_values(by="score", ascending=False)
                    st.markdown(f"### 🏆 Best Resume: {df.iloc[0]['resume']} ({df.iloc[0]['score']}%)")
                    st.dataframe(df)

    # -------------------- Candidate Pages --------------------
    else:
        if page=="🧾 Upload Resume & Auto-Match":
            st.header("🧾 Upload Resume — Automatic Matching")
            resume_file = st.file_uploader("Upload resume (pdf/docx/txt)", type=["pdf","docx","txt"])
            if st.button("🔍 Match Automatically"):
                if not resume_file:
                    st.error("Upload resume first")
                else:
                    resume_text = parse_uploaded_file(resume_file)
                    jobs = db.query(Job).all()
                    if not jobs:
                        st.info("No jobs available yet")
                    else:
                        best_score = -1
                        best_result = None
                        best_job = None
                        for job in jobs:
                            r = compute_match_and_feedback(resume_text, job.description_text)
                            if r["score"]>best_score:
                                best_score=r["score"]
                                best_result=r
                                best_job=job
                        # Save resume & match
                        new_resume=Resume(filename=resume_file.name, content_text=resume_text, uploaded_at=datetime.utcnow())
                        db.add(new_resume); db.commit(); db.refresh(new_resume)
                        new_match=Match(
                            resume_id=new_resume.id,
                            job_id=best_job.id,
                            score=best_result["score"],
                            feedback=json.dumps(best_result["feedback_lines"], ensure_ascii=False),
                            matched_skills=",".join(best_result["matched"]),
                            missing_skills=",".join(best_result["missing"]),
                            created_at=datetime.utcnow()
                        )
                        db.add(new_match); db.commit(); db.refresh(new_match)

                        # Display Candidate Best Match
                        st.markdown(f"### 🎯 Best Match: **{new_resume.filename}** ↔ **{best_job.title}**")
                        col1, col2 = st.columns([1,1])
                        with col1:
                            st.metric("🏆 Overall Score", f"{best_result['score']:.1f}%")
                            st.metric("📄 Text Similarity", f"{best_result['similarity']:.1f}%")
                            st.metric("💡 Skill Match", f"{best_result['skill_match_pct']:.1f}%")
                        with col2:
                            matched = best_result['matched']
                            missing = best_result['missing']
                            fig, ax = plt.subplots(figsize=(4,3))
                            ax.pie([len(matched), len(missing)],
                                   labels=["Matched","Missing"],
                                   autopct="%1.1f%%",
                                   colors=["#1f77b4","#ff7f0e"],
                                   startangle=90)
                            ax.set_title("Keyword Match")
                            st.pyplot(fig)
                        st.markdown("#### ✨ Feedback")
                        for line in best_result["feedback_lines"]:
                            st.markdown(f"- {line}")

        elif page=="📊 My Match History":
            st.header("📊 Your Past Matches")
            resumes = db.query(Resume).all()
            if not resumes:
                st.info("No past uploads")
            else:
                matches = db.query(Match).order_by(Match.created_at.desc()).all()
                if not matches:
                    st.info("No matches yet")
                else:
                    rows=[]
                    for m in matches:
                        job = db.query(Job).filter(Job.id==m.job_id).first()

