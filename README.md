# AI Resume Screening System

Streamlit app that:

1. Accepts a batch of resume files (PDF/DOCX) and a Job Description.
2. Extracts text from each document.
3. Sends each (Resume + JD) to Gemini and requires strict JSON output.
4. Ranks candidates in a Pandas DataFrame and allows CSV/Excel export.

## Setup

1. Create a Gemini API key and set it as `GEMINI_API_KEY`.
2. (Recommended) Copy `env.example` to `.env` and fill in the key.

## Run

From the project folder:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usage

1. Upload resumes (PDF/DOCX, multiple files).
2. Paste the Job Description.
3. Click **Run Screening**.
4. Download the ranked table as CSV or Excel.

# AI Resume Screening System

A Streamlit app that screens a batch of resumes against a Job Description using the Gemini API and returns a ranked table.

## Setup

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Set your Gemini API key as an environment variable:
   - Windows (PowerShell):  
     - `$env:GEMINI_API_KEY="YOUR_KEY_HERE"`
   - Or permanently:
     - `setx GEMINI_API_KEY "YOUR_KEY_HERE"`

## Run

- `streamlit run app.py`

## Output

The app displays a ranked table and lets you download it as CSV and Excel.

