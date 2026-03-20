import io
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv


from src.screening.pipeline import screen_resumes_batch
from src.screening.extractors import extract_text_from_upload
from src.screening.gemini_client import generate_gemini_text
from src.screening.prompting import build_strict_resume_chat_prompt
from src.utils.text_cleaning import normalize_text


st.set_page_config(page_title="AI Resume Screening", layout="wide", page_icon="📄")

st.session_state.setdefault("ranked_df", None)
st.session_state.setdefault("resume_text_by_file", {})
st.session_state.setdefault("chat_messages_by_candidate", {})
st.session_state.setdefault("selected_candidate_file", None)
st.session_state.setdefault("api_key", None)
st.session_state.setdefault("model_name", None)
st.session_state.setdefault("job_description", "")


def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Converts DataFrame to Excel bytes for download."""
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Ranked Resumes", index=False)
        return buffer.getvalue()

def _maybe_get_api_key() -> str:
    """Retrieves API key from environment or Streamlit secrets."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key and hasattr(st, "secrets"):
        api_key = st.secrets.get("GEMINI_API_KEY")
    return api_key


with st.sidebar:
    st.header("Model Settings")
    model_name = st.selectbox("Gemini Model", ["gemini-2.5-flash", "gemini-1.5-pro"])
    temperature = st.slider("Strictness (Temperature)", 0.0, 1.0, 0.2, 0.1)
    st.info("Lower temperature results in more consistent, objective scoring.")


st.title("🚀 AI Resume Screening System")
st.markdown("""
Upload a batch of resumes and provide a Job Description. 
The system uses AI to rank candidates based on fit, strengths, and gaps.
""")

job_description = st.text_area(
    "Job Description",
    height=250,
    placeholder="Paste the job requirements here...",
)

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF or DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)

st.divider()

# 4. Execution
if st.button("Run Screening", type="primary", use_container_width=True):
    api_key = _maybe_get_api_key()
    
    if not api_key:
        st.error("Missing `GEMINI_API_KEY`. Please set it in your .env file.")
        st.stop()
    if not uploaded_files:
        st.warning("Please upload at least one resume.")
        st.stop()
    if not job_description.strip():
        st.warning("Job Description cannot be empty.")
        st.stop()

    with st.status("Processing: Extracting text & analyzing with Gemini...", expanded=True) as status:
        try:
            max_job_desc_chars = int(os.getenv("RESUME_SCREENING_MAX_JOB_DESC_CHARS", "4000"))
            max_resume_chars = int(os.getenv("RESUME_SCREENING_MAX_RESUME_CHARS", "25000"))
            max_pdf_pages = int(os.getenv("RESUME_SCREENING_MAX_PDF_PAGES", "8"))
            max_docx_paragraphs = int(os.getenv("RESUME_SCREENING_MAX_DOCX_PARAGRAPHS", "80"))

            # Step 1: Extract once, store raw resume text in session state.
            resume_text_by_file = {}
            for uploaded_file in uploaded_files:
                file_name = getattr(uploaded_file, "name", "") or "resume"
                text = extract_text_from_upload(
                    uploaded_file,
                    max_pages=max_pdf_pages,
                    max_paragraphs=max_docx_paragraphs,
                    max_chars=max_resume_chars,
                )
                text = normalize_text(text)
                if len(text) > max_resume_chars:
                    text = text[:max_resume_chars]
                resume_text_by_file[file_name] = text

            df = screen_resumes_batch(
                api_key=api_key,
                model_name=model_name,
                job_description=job_description[:max_job_desc_chars],
                files=uploaded_files,
                temperature=temperature,
                resume_texts=resume_text_by_file,
            )
            status.update(label="Screening complete!", state="complete", expanded=False)

            st.session_state["ranked_df"] = df
            st.session_state["resume_text_by_file"] = resume_text_by_file
            st.session_state["chat_messages_by_candidate"] = {}
            st.session_state["api_key"] = api_key
            st.session_state["model_name"] = model_name
            st.session_state["job_description"] = normalize_text(job_description)[:max_job_desc_chars]

            if not df.empty and "FileName" in df.columns:
                st.session_state["selected_candidate_file"] = df.iloc[0]["FileName"]
            else:
                st.session_state["selected_candidate_file"] = next(iter(resume_text_by_file.keys()), None)
        except Exception as e:
            st.error(f"An error occurred during screening: {e}")
            st.stop()

# 5. Results Display (persist from session state)
df = st.session_state.get("ranked_df")
if isinstance(df, pd.DataFrame) and not df.empty:
    st.subheader("📊 Ranked Results")
    st.dataframe(df, use_container_width=True, height=400, hide_index=True)

    st.subheader("Export Data")
    col_csv, col_excel = st.columns(2)

    with col_csv:
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name="ranked_resumes.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_excel:
        excel_bytes = _df_to_excel_bytes(df)
        st.download_button(
            "Download Excel",
            data=excel_bytes,
            file_name="ranked_resumes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# 6. Candidate Chat (Step 2-4)
st.divider()
st.subheader("🧑‍💼 Candidate Chatbot")

resume_text_by_file = st.session_state.get("resume_text_by_file", {}) or {}
candidate_files = list(resume_text_by_file.keys())

if not candidate_files:
    st.info("Run Screening to enable candidate chat.")
    st.stop()

file_to_label: dict[str, str] = {}
if isinstance(df, pd.DataFrame) and not df.empty and "FileName" in df.columns and "CandidateName" in df.columns:
    for _, row in df.iterrows():
        file_name = row["FileName"]
        candidate_name = (row.get("CandidateName") or "").strip()
        file_to_label[file_name] = candidate_name if candidate_name else file_name
else:
    file_to_label = {fn: fn for fn in candidate_files}


def _format_candidate(fn: str) -> str:
    return file_to_label.get(fn, fn)


selected_candidate_file = st.selectbox(
    "Selected Candidate",
    options=candidate_files,
    index=max(0, candidate_files.index(st.session_state["selected_candidate_file"]))
    if st.session_state.get("selected_candidate_file") in candidate_files
    else 0,
    format_func=_format_candidate,
)
st.session_state["selected_candidate_file"] = selected_candidate_file

chat_messages_by_candidate = st.session_state.get("chat_messages_by_candidate", {})
messages = chat_messages_by_candidate.get(selected_candidate_file, [])

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Ask about this candidate...")

if question:
    api_key = st.session_state.get("api_key")
    model_name = st.session_state.get("model_name") or "gemini-1.5-flash"
    if not api_key:
        st.error("Missing API key. Please run Screening again.")
        st.stop()

    resume_text = resume_text_by_file.get(selected_candidate_file, "")
    if not resume_text.strip():
        assistant_text = "Not found in resume."
    else:
        prompt = build_strict_resume_chat_prompt(
            job_description=st.session_state.get("job_description", ""),
            resume_text=resume_text,
            question=question,
        )

        assistant_text = generate_gemini_text(
            api_key=api_key,
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
            timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", "60")),
            response_mime_type="text/plain",
        )

    messages.append({"role": "user", "content": question})
    messages.append({"role": "assistant", "content": assistant_text})

    chat_messages_by_candidate[selected_candidate_file] = messages
    st.session_state["chat_messages_by_candidate"] = chat_messages_by_candidate
    st.rerun()