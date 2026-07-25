from pathlib import Path


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(contents: str) -> bytes:
    header = b"%PDF-1.4\n"
    objs = []
    objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objs.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objs.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )

    text_lines = contents.splitlines()
    stream = []
    if text_lines:
        stream.append("BT\n/F1 12 Tf 50 760 Td (%s) Tj\n" % escape_pdf_text(text_lines[0]))
        for line in text_lines[1:]:
            stream.append("0 -18 Td (%s) Tj\n" % escape_pdf_text(line))
        stream.append("ET\n")

    content = "".join(stream).encode("latin1")
    objs.append(
        b"4 0 obj\n<< /Length %d >>\nstream\n" % len(content) + content + b"endstream\nendobj\n"
    )
    objs.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    offsets = []
    body = bytearray()
    for obj in objs:
        offsets.append(len(header) + len(body))
        body.extend(obj)

    xref_start = len(header) + len(body)
    xref = bytearray()
    xref.extend(b"xref\n0 %d\n" % (len(objs) + 1))
    xref.extend(b"0000000000 65535 f \n")
    for off in offsets:
        xref.extend(b"%010d 00000 n \n" % off)

    trailer = (
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % ((len(objs) + 1), xref_start)
    )
    return header + body + xref + trailer


candidates = {
    "sample_resume_candidate1.pdf": [
        "Candidate Name: Alex Johnson",
        "Applied Role: Data Scientist",
        "Summary: Experienced data scientist with strengths in Python, SQL, and statistical modeling.",
        "Skills: Python, SQL, pandas, scikit-learn, machine learning, data visualization",
        "Experience: Built predictive models for customer churn and sales forecasting.",
        "Education: M.S. in Data Science",
        "Tools: Jupyter, Tableau, Git",
        "Strengths: strong analytical skills, domain insight, model evaluation",
    ],
    "sample_resume_candidate2.pdf": [
        "Candidate Name: Priya Singh",
        "Applied Role: Business Intelligence / Data Engineer",
        "Summary: Data engineering specialist focused on ETL, dashboards, and business insights.",
        "Skills: SQL, Airflow, dbt, data warehousing, Tableau, Python",
        "Experience: Built ETL pipelines and operational dashboards for sales teams.",
        "Education: B.Tech in Computer Science",
        "Tools: Snowflake, AWS, Power BI",
        "Strengths: strong data pipeline knowledge, reporting, stakeholder communication",
    ],
    "sample_resume_candidate3.pdf": [
        "Candidate Name: Maria Lopez",
        "Applied Role: Machine Learning Engineer",
        "Summary: Machine learning engineer with production deployment and MLOps experience.",
        "Skills: Python, TensorFlow, PyTorch, Docker, AWS SageMaker",
        "Experience: Deployed models to production and automated training workflows.",
        "Education: M.S. in Computer Engineering",
        "Tools: Kubernetes, MLflow, GitHub Actions",
        "Strengths: model deployment, MLOps, software engineering rigor",
    ],
}

for filename, lines in candidates.items():
    pdf_bytes = build_pdf("\n".join(lines))
    Path(filename).write_bytes(pdf_bytes)
    print(f"Created {filename}")
