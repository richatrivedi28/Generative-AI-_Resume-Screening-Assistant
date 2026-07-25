
# Import all the libraries

import json

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate

import pandas as pd
from pathlib import Path
import os

# Load the API key from .env

load_dotenv()


# Set up the LLM and the embedding model

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")



# Load a resume pdf and split it into chunks

def load_and_split_pdf(pdf_path, chunk_size=1000, chunk_overlap=150):
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(pages)
    return chunks

# Build the vector store and retriever for a resume's chunks

def build_vectorstore(chunks):
    return FAISS.from_documents(chunks, embeddings)

def get_retriever(vectorstore, k=6):
    return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": k})



# Prompt template used to evaluate a resume against a JD
# The LLM is told exactly what JSON keys to return, no schema class needed

FORMAT_INSTRUCTIONS = """Return ONLY a valid JSON object with these keys:
- candidate_name (string)
- match_score (integer between 0 and 100)
- matching_skills (list of strings)
- missing_skills (list of strings)
- summary (string, 3-4 sentences)
- strengths (list of 3-5 strings)
- weaknesses (list of 2-4 strings)
- recommendation (one of: Strongly Recommend, Recommend, Consider, Not Recommended)
- justification (string, 2-3 sentences)

Do not include any text outside the JSON object."""

eval_prompt = PromptTemplate(
    template="""You are an expert technical recruiter. Evaluate the candidate's resume
excerpts below against the given Job Description. Only use information present in the
resume excerpts, do not invent facts.

JOB DESCRIPTION:
{jd_text}

RELEVANT RESUME EXCERPTS:
{context}

{format_instructions}
""",
    input_variables=["jd_text", "context"],
    partial_variables={"format_instructions": FORMAT_INSTRUCTIONS},
)

# Small helper to pull JSON out of the LLM response
# (models sometimes wrap JSON in ```json ... ``` fences, so strip those first)

def parse_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1)
    return json.loads(text)


# Full pipeline for one resume: load -> split -> embed -> retrieve -> prompt -> LLM -> parse

def evaluate_resume(pdf_path, jd_text, k=6):
    # Resolve pdf_path: if it doesn't exist, try to locate by basename in workspace
    if not os.path.exists(pdf_path):
        basename = os.path.basename(pdf_path)
        matches = list(Path('.').rglob(basename))
        if len(matches) == 1:
            pdf_path = str(matches[0])
        elif len(matches) > 1:
            # pick the first match but inform in logs
            pdf_path = str(matches[0])
        else:
            # No matches — give a helpful error listing available sample PDFs
            sample_files = [p.name for p in Path('.').glob('*.pdf')]
            raise ValueError(
                f"File path {pdf_path} is not a valid file or url.\n"
                f"Searched for basename '{basename}' in the workspace and found none.\n"
                f"Available PDFs in the project root: {sample_files}"
            )

    chunks = load_and_split_pdf(pdf_path)
    vectorstore = build_vectorstore(chunks)
    retriever = get_retriever(vectorstore, k=k)

    retrieved_docs = retriever.invoke(jd_text)
    context = "\n\n".join(doc.page_content for doc in retrieved_docs)

    prompt = eval_prompt.format(jd_text=jd_text, context=context)
    response = llm.invoke(prompt)

    try:
        result = parse_json_response(response.content)
    except Exception as e:
        fix_prompt = f"""The output below was supposed to be valid JSON but failed to parse.

OUTPUT:
{response.content}

ERROR:
{e}

Return only the corrected, valid JSON. No extra text."""
        fixed_response = llm.invoke(fix_prompt)
        result = parse_json_response(fixed_response.content)

    return result


# Rank candidates and generate a final hiring recommendation

def rank_candidates(evaluations):
    return sorted(evaluations, key=lambda e: e["match_score"], reverse=True)

best_candidate_prompt = PromptTemplate(
    template="""You are a senior hiring manager. Below are evaluations of {n} candidates
for the same job description.

JOB DESCRIPTION:
{jd_text}

CANDIDATE EVALUATIONS:
{evaluations_text}

Write a short 5-6 sentence hiring recommendation naming the best candidate and why.
""",
    input_variables=["n", "jd_text", "evaluations_text"],
)

def generate_best_candidate_recommendation(evaluations, jd_text):
    evaluations_text = "\n\n".join(
        f"- {e['candidate_name']} | Score: {e['match_score']}/100 | "
        f"Strengths: {', '.join(e['strengths'])} | Missing: {', '.join(e['missing_skills'])}"
        for e in evaluations
    )
    prompt = best_candidate_prompt.format(n=len(evaluations), jd_text=jd_text, evaluations_text=evaluations_text)
    response = llm.invoke(prompt)
    return response.content



# Job description and sample resumes

JD_DATA_SCIENTIST = """
Job Title: Data Scientist

We are looking for a Data Scientist with:
- Strong Python programming skills (pandas, NumPy, scikit-learn)
- Experience with machine learning model building and evaluation
- SQL for data querying
- Experience with deep learning frameworks (TensorFlow or PyTorch)
- Strong statistics and A/B testing background
- Experience deploying models to production (MLOps, Docker, cloud platforms)
- Excellent communication and stakeholder management skills
- Bachelor's/Master's degree in CS, Statistics, or related field
"""
RESUME_A = "sample_resumes/Amisha_Kulkarni_Final_Resume.pdf"
RESUME_B = "sample_resumes/Amisha_SQL_DBA_Resume.pdf"
RESUME_C = "sample_resumes/latest_resume.pdf"


if __name__ == "__main__":
    print(JD_DATA_SCIENTIST)

    # Check the loader and splitter on Resume A
    chunks = load_and_split_pdf(RESUME_A)
    print(f"Resume A split into {len(chunks)} chunks")
    print(chunks[0].page_content[:400])

    # Check the retriever on Resume A
    vectorstore = build_vectorstore(chunks)
    retriever = get_retriever(vectorstore, k=6)

    retrieved = retriever.invoke(JD_DATA_SCIENTIST)
    print(f"Retrieved {len(retrieved)} relevant chunks for the JD query")
    print(retrieved[0].page_content[:300])

    # Evaluate Resume A for the Data Scientist role
    result_a = evaluate_resume(RESUME_A, JD_DATA_SCIENTIST)
    print(f"Candidate: {result_a['candidate_name']}")
    print(f"Match Score: {result_a['match_score']}/100")
    print(f"Matching Skills: {result_a['matching_skills']}")
    print(f"Missing Skills: {result_a['missing_skills']}")
    print(f"\nSummary: {result_a['summary']}")
    print(f"\nStrengths: {result_a['strengths']}")
    print(f"Weaknesses: {result_a['weaknesses']}")
    print(f"\nRecommendation: {result_a['recommendation']}")
    print(f"Justification: {result_a['justification']}")

    # Evaluate Resume B and compare it against Resume A
    result_b = evaluate_resume(RESUME_B, JD_DATA_SCIENTIST)

    comparison_df = pd.DataFrame([
        {"Candidate": result_a["candidate_name"], "Score": result_a["match_score"], "Recommendation": result_a["recommendation"]},
        {"Candidate": result_b["candidate_name"], "Score": result_b["match_score"], "Recommendation": result_b["recommendation"]},
    ])
    comparison_df.sort_values("Score", ascending=False)

    # Evaluate Resume C and check its missing skills
    result_c = evaluate_resume(RESUME_C, JD_DATA_SCIENTIST)
    print(f"Candidate: {result_c['candidate_name']}")
    print("Missing Skills for this JD:")
    for skill in result_c["missing_skills"]:
        print(f"  - {skill}")

    # Rank all candidates by match score
    all_evaluations = [result_a, result_b, result_c]
    ranked = rank_candidates(all_evaluations)

    for rank, ev in enumerate(ranked, start=1):
        print(f"#{rank}: {ev['candidate_name']} - {ev['match_score']}/100 ({ev['recommendation']})")

    # Generate the final hiring recommendation
    final_recommendation = generate_best_candidate_recommendation(ranked, JD_DATA_SCIENTIST)
    print(final_recommendation)

