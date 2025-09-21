# matcher.py
from sentence_transformers import SentenceTransformer, util
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# Load a small model (downloads first time)
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

def compute_soft_similarity(text_a, text_b):
    """
    Use sentence-transformers embedding cosine similarity
    Returns a float 0..1
    """
    try:
        emb = model.encode([text_a, text_b], convert_to_tensor=True)
        sim = util.cos_sim(emb[0], emb[1]).item()
        # clamp
        if sim < 0:
            sim = 0.0
        if sim > 1:
            sim = 1.0
        return float(sim)
    except Exception:
        # Fallback to TF-IDF cosine if embedding fails
        try:
            vect = TfidfVectorizer(stop_words="english", max_features=5000)
            tfidf = vect.fit_transform([text_a or "", text_b or ""])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            return float(sim)
        except Exception:
            return 0.0

def hard_keyword_match(jd_text, resume_text, must_skills_csv, nice_skills_csv):
    """
    jd_text, resume_text: strings
    must_skills_csv, nice_skills_csv: comma-separated strings
    returns: hard_score (0..1), missing_must_list, missing_nice_list, matched_must_list, matched_nice_list
    """
    must = [s.strip().lower() for s in (must_skills_csv or "").split(",") if s.strip()]
    nice = [s.strip().lower() for s in (nice_skills_csv or "").split(",") if s.strip()]
    resume_lower = (resume_text or "").lower()

    matched_must = [s for s in must if s in resume_lower]
    missing_must = [s for s in must if s not in resume_lower]

    matched_nice = [s for s in nice if s in resume_lower]
    missing_nice = [s for s in nice if s not in resume_lower]

    hard_score = 1.0
    if must:
        hard_score = len(matched_must) / len(must)
    else:
        # If no must skills provided, compute partial hard score from nice skills presence
        if nice:
            hard_score = len(matched_nice) / len(nice)
        else:
            hard_score = 0.0

    return hard_score, missing_must, missing_nice, matched_must, matched_nice

def compute_combined_score(hard_score, soft_score, hard_weight=0.6, soft_weight=0.4):
    """
    hard_score and soft_score are 0..1
    Returns 0..100 scaled
    """
    total = hard_score * hard_weight + soft_score * soft_weight
    return round(total * 100, 2)
