# AI Resume Screening Assistant (LangChain)

## Overview

This project implements an AI-powered resume screening assistant using LangChain and RAG. Upload PDF resumes and a job description to get structured candidate evaluations (match score, matching/missing skills, summary, strengths, weaknesses, recommendation, and justification).

The repository's main runtime files are:
- `app.py` — Streamlit app entrypoint (imports and uses `code.py`).
- `code.py` — Converted logic from the demo notebook; provides the RAG evaluation functions.

## Quick Start

1. Open PowerShell in the project folder:
   ```powershell
   cd "c:\Users\richa\My Learnings\Practice_work\MLdeployment\Resume screening"
   ```
2. Activate the virtual environment:
   ```powershell
   .\myenv\Scripts\Activate.ps1
   ```
3. (Recommended) Set your API key in the environment so it is never shown in the UI:
   ```powershell
   $env:OPENAI_API_KEY = "sk-..."
   ```
   Or create a `.env` file with `OPENAI_API_KEY=sk-...` and ensure it is loaded by your shell.
4. Run the Streamlit app:
   ```powershell
   python -m streamlit run app.py
   ```

## Notes on API Key Handling

- If `OPENAI_API_KEY` is set in the environment the app loads it silently (no UI disclosure).
- If no environment key is present a masked `API Key` input will appear for one-time entry; the value is not printed or stored in the repo.

## Usage

1. Paste or edit the job description (a default Data Scientist JD is provided).
2. Upload one or more resume PDFs.
3. Choose the retriever `k` (how many chunks to retrieve per resume).
4. Click **Evaluate** to run the RAG-based evaluation.
5. Review candidate evaluations and the generated hiring recommendation.

## Example Test Cases

- Evaluate a single resume for a Data Scientist role.
- Compare multiple resumes against the same JD.
- Identify missing skills in a resume.
- Rank candidates and generate a hiring recommendation.

## Files

- `app.py` — Streamlit app entrypoint that imports `code.py`
- `code.py` — notebook code containing the RAG pipeline and helper functions
- `generate_sample_resumes.py` — Utility to create sample resume PDFs for testing
- `requirements.txt` — Python dependencies

## Run Tips

- Use the virtual environment `myenv` to ensure dependencies match the project.
- For production or sharing, prefer setting `OPENAI_API_KEY` in the host environment or use Streamlit secrets (`.streamlit/secrets.toml`) rather than typing keys into the UI.

