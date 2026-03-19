import os
from io import BytesIO

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.pipeline.screening import screen_batch


def _bytes_to_excel(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()


def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def main() -> None:
    load_dotenv()

    st.set_page_config(page_title="AI Resume Screening", layout="wide")
    st.title("AI Resume Screening System")

    st.markdown(
        "Upload a batch of resumes (PDF/DOCX) and provide a Job Description. "
        "The system extracts text, asks Gemini to return strict JSON, "
        "validates it, and ranks candidates."
    )

    jd_text = st.text_area("Job Description", height=220)
    uploaded = st.file_uploader(
        "Upload Resumes (PDF/DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        run_button = st.button("Run Screening", type="primary", disabled=not uploaded or not jd_text)
    with col2:
        max_candidates = st.number_input(
            "Max candidates to process",
            min_value=1,
            max_value=50,
            value=min(10, len(uploaded) if uploaded else 10),
        )

    if run_button:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("Missing `GEMINI_API_KEY`. Set it in `env.example` -> `.env`, then restart.")
            return

        if not uploaded:
            st.error("Please upload at least one resume.")
            return

        files = list(uploaded)[: int(max_candidates)]

        with st.status("Screening candidates..."):
            df = screen_batch(job_description=jd_text, files=files)

        st.success("Done.")

        if df.empty:
            st.warning("No results to display.")
            return

        st.subheader("Ranked Results")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Download")
        csv_bytes = _to_csv_bytes(df)
        excel_bytes = _bytes_to_excel(df)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("Download CSV", csv_bytes, file_name="ranked_resumes.csv", mime="text/csv")
        with d2:
            st.download_button(
                "Download Excel",
                excel_bytes,
                file_name="ranked_resumes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


if __name__ == "__main__":
    main()

import io
import os
from typing import Optional

import pandas as pd
import streamlit as st

from src.screening.pipeline import screen_resumes_batch


st.set_page_config(page_title="AI Resume Screening", layout="wide")
st.title("AI Resume Screening System")


def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    # Use an in-memory buffer so Streamlit can serve the file directly.
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Ranked Resumes", index=False)
        return buffer.getvalue()


def _maybe_get_api_key() -> Optional[str]:
    # Prefer env var. Streamlit secrets can also work if you set them.
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return None


job_description = st.text_area(
    "Job Description",
    height=220,
    placeholder="Paste the job description here...",
)

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF or DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)

col1, col2 = st.columns(2)
with col1:
    temperature = st.slider("Model temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
with col2:
    model_name = st.text_input("Gemini Model Name", value="gemini-1.5-pro")


run_btn = st.button("Run Screening", type="primary", use_container_width=True)

if run_btn:
    api_key = _maybe_get_api_key()
    if not api_key:
        st.error("Missing `GEMINI_API_KEY`. Set it as an environment variable or in `st.secrets`.")
        st.stop()

    if not uploaded_files:
        st.warning("Upload at least one resume.")
        st.stop()

    if not job_description.strip():
        st.warning("Job Description cannot be empty.")
        st.stop()

    with st.spinner("Extracting text + screening resumes with Gemini..."):
        df = screen_resumes_batch(
            api_key=api_key,
            model_name=model_name,
            job_description=job_description,
            files=uploaded_files,
            temperature=temperature,
        )

    st.success("Screening complete.")

    st.subheader("Ranked Results")
    st.dataframe(df, use_container_width=True, height=420)

    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download CSV",
        data=csv_bytes,
        file_name="ranked_resumes.csv",
        mime="text/csv",
        use_container_width=True,
    )

    excel_bytes = _df_to_excel_bytes(df)
    st.download_button(
        "Download Excel",
        data=excel_bytes,
        file_name="ranked_resumes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

