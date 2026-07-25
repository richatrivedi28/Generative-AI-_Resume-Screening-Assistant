import os
import sys
import tempfile
import importlib
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="AI Resume Screening Assistant",
    page_icon="🧾",
    layout="centered",
)


def recommendation_emoji_label(recommendation: str) -> str:
    mapping = {
        "Strongly Recommend": "✅ Strongly Recommend",
        "Recommend": "👍 Recommend",
        "Consider": "🤔 Consider",
        "Not Recommended": "❌ Not Recommended",
    }
    return mapping.get(recommendation, recommendation)


def ensure_notebook_module():
    # Ensure OPENAI_API_KEY is set in environment before importing the notebook code
    env_key = os.getenv("OPENAI_API_KEY", "")
    nb_module = None

    if not env_key:
        api_key = st.text_input("API Key", type="password", value="")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

    
    try:
        if "code" in sys.modules:
            nb_module = importlib.reload(sys.modules["code"])
        else:
            nb_module = importlib.import_module("code")
    except Exception as e:
        st.error(f"Failed to load notebook module: {e}")
        raise

    return nb_module


def main():
    st.markdown(
        """
        <style>
        .stApp h1 {
            color: #05668D;
            background-color: #E0F7FA;
            padding: 12px 16px;
            border-radius: 12px;
        }
        .stApp h2 {
            color: #028090;
        }
        .stApp .big-banner {
            background: #E0F7FA;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 16px;
        }
        .stApp .section-box {
            background: #F4FBFF;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("AI Resume Screening Assistant")
    st.markdown(
        """
        <style>
        .stApp h1 {
            color: #05668D;
            background-color: #E0F7FA;
            padding: 12px 16px;
            border-radius: 12px;
        }
        .stApp h2 {
            color: #028090;
        }
        .stApp .section-box {
            background: #F4FBFF;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='section-box'>
            <p>Upload candidate PDFs, paste the job description, and get structured matching scores plus hiring recommendations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nb = ensure_notebook_module()

    col1, col2 = st.columns([2, 1])

    with col1:
        jd_text = st.text_area("Job Description", value=nb.JD_DATA_SCIENTIST, height=240)
        k = st.slider(
            "Chunks retrieved per resume",
            1,
            10,
            6,
            help="How many document chunks to retrieve per resume (k). Higher values increase context and cost.",
        )

    with col2:
        uploaded = st.file_uploader("Upload PDF resumes", type=["pdf"], accept_multiple_files=True)
        st.info("Upload one or more PDF resumes on the right, then click Evaluate ⏳ below.")

    if st.button("Evaluate ⏳"):
        if not uploaded:
            st.warning("Please upload one or more PDF resumes.")
        else:
            if not os.getenv("OPENAI_API_KEY"):
                st.error("No API key available. Set `OPENAI_API_KEY` or enter it in the field above.")
            else:
                evaluations = []
                tmpdir = Path(tempfile.mkdtemp(prefix="resume_tmp_"))
                for f in uploaded:
                    out_path = tmpdir / f.name
                    with open(out_path, "wb") as wf:
                        wf.write(f.getbuffer())
                    try:
                        ev = nb.evaluate_resume(str(out_path), jd_text, k=k)
                    except Exception as e:
                        st.error(f"Evaluation failed for {f.name}: {e}")
                        continue
                    evaluations.append(ev)

                if evaluations:
                    ranked = nb.rank_candidates(evaluations)
                    st.header("Evaluations")
                    for ev in ranked:
                        st.subheader(ev.get("candidate_name", "Unknown"))
                        st.write(f"Score: {ev.get('match_score', 'N/A')}/100")
                        st.write("Matching skills: ", ", ".join(ev.get('matching_skills', [])))
                        st.write("Missing skills: ", ", ".join(ev.get('missing_skills', [])))
                        st.write("Summary:")
                        st.write(ev.get("summary", ""))
                        st.write("Recommendation: ", recommendation_emoji_label(ev.get("recommendation", "")))
                        st.write("Justification:")
                        st.write(ev.get("justification", ""))

                    st.header("Hiring Recommendation")
                    try:
                        rec = nb.generate_best_candidate_recommendation(evaluations, jd_text)
                        st.write(rec)
                    except Exception as e:
                        st.error(f"Failed to generate final recommendation: {e}")


if __name__ == "__main__":
    main()
