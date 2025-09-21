# app.py
import streamlit as st
from db import SessionLocal, User, Job, Resume, Match
from parser_utils import parse_uploaded_file
from matcher import hard_keyword_match, compute_soft_similarity, compute_combined_score
import os
from sqlalchemy.orm import joinedload
import pandas as pd
from datetime import datetime
from io import BytesIO
import sqlite3

# Ensure uploads dir
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# Utility DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Session state helper for simple pseudo-auth (no secure auth)
if "user" not in st.session_state:
    st.session_state.user = None

st.set_page_config(page_title="Resume Matcher", layout="wide")

st.sidebar.title("Resume Matcher")
if st.session_state.user:
    st.sidebar.markdown(f"**Signed in as:** {st.session_state.user['name']} ({st.session_state.user['role']})")
    if st.sidebar.button("Sign out"):
        st.session_state.user = None
        st.experimental_rerun()
else:
    st.sidebar.header("Sign in / Register (demo)")
    with st.sidebar.form("login_form"):
        name = st.text_input("Name", value="")
        email = st.text_input("Email", value="")
        role = st.selectbox("Role", ["candidate", "company", "admin"])
        submitted = st.form_submit_button("Sign in")
        if submitted:
            # Create or fetch user in DB
            db = next(get_db())
            usr = db.query(User).filter(User.email == email).first()
            if not usr:
                usr = User(name=name or "Anonymous", email=email, role=role)
                db.add(usr); db.commit(); db.refresh(usr)
            st.session_state.user = {"id": usr.id, "name": usr.name, "email": usr.email, "role": usr.role}
            st.experimental_rerun()

st.title("Automated Resume — Job Matching System")

# High-level nav
if st.session_state.user:
    role = st.session_state.user["role"]
else:
    role = None

nav_options = []
if role == "candidate":
    nav_options = ["Home", "Upload Resume", "My Matches", "All Jobs"]
elif role == "company":
    nav_options = ["Home", "Post Job", "View Matches"]
elif role == "admin":
    nav_options = ["Home", "Jobs", "Resumes", "Matches", "Export"]
else:
    nav_options = ["Home", "About"]

choice = st.sidebar.selectbox("Navigation", nav_options)

# Helpers
def save_file_to_disk(uploaded_file):
    ext = uploaded_file.name
    unique = f"{int(datetime.utcnow().timestamp())}_{uploaded_file.name}"
    path = os.path.join(UPLOAD_DIR, unique)
    with open(path, "wb") as f:
        f.write(uploaded_file.read())
    return path

def recompute_matches_for_job(db, job):
    """
    Compute matches between this job and all resumes in DB.
    Stores records in Match table (deletes old for this job)
    """
    # Delete existing matches for job
    db.query(Match).filter(Match.job_id == job.id).delete()
    db.commit()

    resumes = db.query(Resume).all()
    for res in resumes:
        # compute hard and soft
        hard, missing_must, missing_nice, matched_must, matched_nice = hard_keyword_match(
            job.jd_text or job.title or "",
            res.parsed_text or "",
            job.must_skills or "",
            job.nice_skills or ""
        )
        soft = compute_soft_similarity(job.jd_text or job.title or "", res.parsed_text or "")
        total = compute_combined_score(hard, soft)
        if total >= 70:
            verdict = "High"
        elif total >= 40:
            verdict = "Medium"
        else:
            verdict = "Low"
        # Simple feedback based on missing skills and semantic score
        feedback_parts = []
        if missing_must:
            feedback_parts.append("Missing must-have: " + ", ".join(missing_must))
        if missing_nice:
            feedback_parts.append("Missing nice-to-have: " + ", ".join(missing_nice))
        feedback_parts.append(f"Semantic similarity: {round(soft*100,2)}%")
        if total < 40:
            feedback_parts.append("Consider adding relevant projects, keywords, and detailed bullet points with metrics.")
        feedback = " | ".join(feedback_parts)

        match = Match(
            job_id=job.id,
            resume_id=res.id,
            hard_score=round(hard*100,2),
            soft_score=round(soft*100,2),
            total_score=total,
            verdict=verdict,
            missing_must=",".join(missing_must),
            missing_nice=",".join(missing_nice),
            feedback=feedback
        )
        db.add(match)
    db.commit()

def recompute_all_matches(db):
    jobs = db.query(Job).all()
    for job in jobs:
        recompute_matches_for_job(db, job)

# --- Pages ---
if choice == "Home":
    st.header("Overview")
    st.markdown("""
    This is a demo two-sided job-resume matching system.
    - **Companies** (role: company) can post Job Descriptions (JDs).
    - **Candidates** (role: candidate) can upload resumes.
    - The system computes both hard (keyword) and soft (semantic) matches and ranks candidates for each job.
    """)
    db = next(get_db())
    jobs_count = db.query(Job).count()
    resumes_count = db.query(Resume).count()
    matches_count = db.query(Match).count()
    cols = st.columns(3)
    cols[0].metric("Jobs", jobs_count)
    cols[1].metric("Resumes", resumes_count)
    cols[2].metric("Matches", matches_count)

# Candidate pages
if role == "candidate" and choice == "Upload Resume":
    st.header("Upload Resume")
    st.markdown("Upload your resume (PDF / DOCX). The system will parse it and compute matches with posted jobs.")
    uploaded_files = st.file_uploader("Upload one or more resumes", type=["pdf","docx"], accept_multiple_files=True)
    if uploaded_files:
        db = next(get_db())
        for up in uploaded_files:
            text = parse_uploaded_file(up)
            # save file to disk
            up.seek(0)
            path = save_file_to_disk(up)
            # create resume record
            res = Resume(user_id=st.session_state.user["id"], filename=up.name, filepath=path, parsed_text=text)
            db.add(res)
            db.commit()
            db.refresh(res)
        st.success("Uploaded and saved. Recomputing matches ...")
        recompute_all_matches(db)
        st.success("Matches recomputed. Go to My Matches to view.")

if role == "candidate" and choice == "My Matches":
    st.header("My Matches (All Jobs)")
    db = next(get_db())
    # get user's resumes and matches
    resumes = db.query(Resume).filter(Resume.user_id == st.session_state.user["id"]).all()
    if not resumes:
        st.info("You have no uploaded resumes. Upload one first.")
    else:
        # build a dataframe of matches for user's resumes across all jobs
        rows = []
        for res in resumes:
            matches = db.query(Match).filter(Match.resume_id == res.id).all()
            for m in matches:
                job = db.query(Job).filter(Job.id == m.job_id).first()
                rows.append({
                    "Resume": res.filename,
                    "Job Title": job.title if job else "",
                    "Company": job.company_name if job else "",
                    "Score": m.total_score,
                    "Verdict": m.verdict,
                    "Missing Must": m.missing_must,
                    "Feedback": m.feedback
                })
        df = pd.DataFrame(rows)
        if df.empty:
            st.info("No matches found yet. Make sure jobs are posted and try again.")
        else:
            st.dataframe(df.sort_values(by="Score", ascending=False), use_container_width=True)
            # allow download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download my matches CSV", data=csv, file_name="my_matches.csv", mime="text/csv")

if role == "candidate" and choice == "All Jobs":
    st.header("All Jobs (apply or check match)")
    db = next(get_db())
    jobs = db.query(Job).all()
    if not jobs:
        st.info("No jobs posted yet.")
    else:
        for j in jobs:
            st.subheader(f"{j.title} — {j.company_name}")
            st.write("Location:", j.location)
            st.write("Must-have:", j.must_skills)
            st.write("Nice-to-have:", j.nice_skills)
            if st.button(f"Check my best match for '{j.title}'", key=f"checkjob-{j.id}"):
                # find user's best resume for this job
                db = next(get_db())
                resumes = db.query(Resume).filter(Resume.user_id == st.session_state.user["id"]).all()
                best = None
                for r in resumes:
                    m = db.query(Match).filter(Match.job_id==j.id, Match.resume_id==r.id).first()
                    if m:
                        if not best or m.total_score > best.total_score:
                            best = m
                if best:
                    st.info(f"Best score: {best.total_score} ({best.verdict}) - Missing must: {best.missing_must}")
                else:
                    st.warning("No match yet. Upload resume or wait until matches are recomputed.")

# Company pages
if role == "company" and choice == "Post Job":
    st.header("Post a Job Description")
    st.markdown("Fill details and upload JD file (optional). Provide must-have and nice-to-have skills as comma-separated values.")
    with st.form("jobform"):
        title = st.text_input("Job title")
        company_name = st.text_input("Company name")
        location = st.text_input("Location")
        must = st.text_area("Must-have skills (comma-separated)", help="e.g., python, sql, machine learning")
        nice = st.text_area("Nice-to-have skills (comma-separated)", help="e.g., tableau, power bi")
        jd_file = st.file_uploader("Optional JD file (pdf/docx)")
        submitted = st.form_submit_button("Create Job")
        if submitted:
            db = next(get_db())
            jd_text = ""
            if jd_file:
                jd_file.seek(0)
                jd_text = parse_uploaded_file(jd_file)
                # save file for records
                jd_file.seek(0)
                save_file_to_disk(jd_file)
            job = Job(title=title, company_name=company_name, location=location, jd_text=jd_text, must_skills=must, nice_skills=nice)
            db.add(job); db.commit(); db.refresh(job)
            st.success("Job created. Recomputing matches for this job...")
            recompute_matches_for_job(db, job)
            st.success("Matches computed. Check View Matches to see ranked candidates.")

if role == "company" and choice == "View Matches":
    st.header("Jobs and Matched Candidates")
    db = next(get_db())
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    if not jobs:
        st.info("No jobs yet. Post a job first.")
    for job in jobs:
        with st.expander(f"{job.title} — {job.company_name} (Posted: {job.created_at.date()})"):
            st.write("Location:", job.location)
            st.write("Must:", job.must_skills)
            st.write("Nice:", job.nice_skills)
            # list matches sorted
            matches = db.query(Match).filter(Match.job_id==job.id).order_by(Match.total_score.desc()).all()
            if not matches:
                st.info("No candidates matched yet.")
            else:
                rows = []
                for m in matches:
                    res = db.query(Resume).filter(Resume.id==m.resume_id).first()
                    usr = db.query(User).filter(User.id==res.user_id).first() if res else None
                    rows.append({
                        "Candidate": usr.name if usr else "Unknown",
                        "Email": usr.email if usr else "",
                        "Resume": res.filename if res else "",
                        "Hard%": m.hard_score,
                        "Soft%": m.soft_score,
                        "Total%": m.total_score,
                        "Verdict": m.verdict,
                        "Missing Must": m.missing_must,
                        "Feedback": m.feedback
                    })
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)
                # Download
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(f"Download matches CSV for {job.title}", data=csv, file_name=f"matches_job_{job.id}.csv", mime="text/csv")

# Admin pages
if role == "admin" and choice == "Jobs":
    st.header("All Jobs (Admin)")
    db = next(get_db())
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    rows = []
    for j in jobs:
        rows.append({"ID": j.id, "Title": j.title, "Company": j.company_name, "Location": j.location, "Posted": j.created_at})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

if role == "admin" and choice == "Resumes":
    st.header("All Resumes (Admin)")
    db = next(get_db())
    resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
    rows = []
    for r in resumes:
        usr = db.query(User).filter(User.id==r.user_id).first() if r.user_id else None
        rows.append({"ID": r.id, "File": r.filename, "User": usr.name if usr else "", "Uploaded": r.created_at})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

if role == "admin" and choice == "Matches":
    st.header("All Matches (Admin)")
    db = next(get_db())
    matches = db.query(Match).order_by(Match.total_score.desc()).all()
    rows = []
    for m in matches:
        job = db.query(Job).filter(Job.id==m.job_id).first()
        res = db.query(Resume).filter(Resume.id==m.resume_id).first()
        rows.append({"Job": job.title if job else "", "Resume": res.filename if res else "", "Score": m.total_score, "Verdict": m.verdict})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    if st.button("Recompute all matches (slow)"):
        recompute_all_matches(next(get_db()))
        st.success("Recomputed all matches.")

if role == "admin" and choice == "Export":
    st.header("Export DB (Admin)")
    # simple export of matches
    db = next(get_db())
    matches = db.query(Match).all()
    rows = []
    for m in matches:
        job = db.query(Job).filter(Job.id==m.job_id).first()
        res = db.query(Resume).filter(Resume.id==m.resume_id).first()
        rows.append({
            "job_id": m.job_id,
            "job_title": job.title if job else "",
            "resume_id": m.resume_id,
            "resume_file": res.filename if res else "",
            "score": m.total_score,
            "verdict": m.verdict,
            "feedback": m.feedback
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        st.download_button("Download Full Matches CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="all_matches.csv", mime="text/csv")
    else:
        st.info("No matches to export.")

# About page for non-logged users
if role is None and choice == "About":
    st.header("About this Demo")
    st.markdown("""
    This demo matches resumes to job descriptions using:
    - **Hard keyword presence** (must-have / nice-to-have)
    - **Soft semantic similarity** (sentence-transformers embeddings)
    Scores are combined (default weights: 60% hard, 40% soft).
    """)
    st.markdown("**How to use:** Sign in as `company` to post jobs; sign in as `candidate` to upload resumes and view matches.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ — Streamlit demo for resume ↔ job matching")
