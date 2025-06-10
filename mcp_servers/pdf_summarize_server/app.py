# mcp_servers/pdf_summarize_server/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl
import requests
import PyPDF2
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="PDF Summarize MCP Server",
    description="Downloads a PDF, extracts text, and summarizes using a configurable cloud LLM."
)

class SummarizeRequest(BaseModel):
    pdf_url: HttpUrl = Field(..., description="URL of the PDF to summarize")

class SummarizeResponse(BaseModel):
    summary: str

# --- LLM Client Initialization (based on environment variable) ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
ANTHROPIC_MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-sonnet-20240229")
GOOGLE_MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME", "gemini-pro")

llm_client = None
llm_model = None

if LLM_PROVIDER == "openai":
    if not OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY not set in .env. OpenAI LLM will not work.")
    else:
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            llm_client = openai
            llm_model = OPENAI_MODEL_NAME
            print(f"Using OpenAI model: {llm_model}")
        except ImportError:
            print("Warning: 'openai' library not installed. Cannot use OpenAI LLM.")
elif LLM_PROVIDER == "anthropic":
    if not ANTHROPIC_API_KEY:
        print("Warning: ANTHROPIC_API_KEY not set in .env. Anthropic LLM will not work.")
    else:
        try:
            import anthropic
            llm_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            llm_model = ANTHROPIC_MODEL_NAME
            print(f"Using Anthropic model: {llm_model}")
        except ImportError:
            print("Warning: 'anthropic' library not installed. Cannot use Anthropic LLM.")
elif LLM_PROVIDER == "google":
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_API_KEY not set in .env. Google LLM will not work.")
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            llm_client = genai
            llm_model = GOOGLE_MODEL_NAME
            print(f"Using Google Generative AI model: {llm_model}")
        except ImportError:
            print("Warning: 'google-generativeai' library not installed. Cannot use Google LLM.")
else:
    print(f"Unsupported LLM_PROVIDER specified: {LLM_PROVIDER}. LLM summarization will be unavailable.")

# --- Helper Functions ---

def download_pdf(url: str) -> BytesIO:
    """Downloads a PDF from a URL and returns it as a BytesIO object."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        # Check content type to ensure it's a PDF
        if 'application/pdf' not in response.headers.get('Content-Type', ''):
            raise ValueError(f"URL does not point to a PDF: {response.headers.get('Content-Type')}")

        pdf_content = BytesIO(response.content)
        return pdf_content
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF from URL: {url} - {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def extract_text_from_pdf(pdf_file: BytesIO) -> str:
    """Extracts text from a PDF BytesIO object."""
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or "" # Handle pages with no extractable text
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {e}")

def summarize_text_with_llm(text: str) -> str:
    """Summarizes text using the configured LLM client."""
    if not llm_client:
        return "LLM summarization is not configured or failed to initialize."
    if not text.strip():
        return "No text provided for summarization."

    prompt = f"Summarize the following research paper content in a concise manner (max 200 words), highlighting its main objectives, methods, and key findings:\n\n{text}"

    try:
        if LLM_PROVIDER == "openai":
            response = llm_client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": "You are a research paper summarizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=250 # Adjust based on desired summary length and model context window
            )
            return response.choices[0].message.content.strip()
        elif LLM_PROVIDER == "anthropic":
            response = llm_client.messages.create(
                model=llm_model,
                max_tokens=250,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            return response.content[0].text.strip()
        elif LLM_PROVIDER == "google":
            model = llm_client.GenerativeModel(llm_model)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.1, max_output_tokens=250)
            )
            return response.text.strip()
        else:
            return "Unsupported LLM provider."
    except Exception as e:
        print(f"Error during LLM summarization with {LLM_PROVIDER}: {e}")
        raise HTTPException(status_code=500, detail=f"LLM summarization failed: {e}. Check API key and model availability.")

@app.post("/summarize_pdf", response_model=SummarizeResponse)
async def summarize_pdf(request: SummarizeRequest):
    """
    Downloads a PDF from the given URL, extracts its text,
    and provides an LLM-generated summary.
    """
    print(f"Received request to summarize PDF: {request.pdf_url}")
    pdf_file_content = download_pdf(str(request.pdf_url))
    extracted_text = extract_text_from_pdf(pdf_file_content)

    if not extracted_text.strip():
        # If the PDF is empty or text extraction failed for some reason
        return SummarizeResponse(summary="Could not extract readable text from PDF for summarization.")

    summary = summarize_text_with_llm(extracted_text)
    return SummarizeResponse(summary=summary)

if __name__ == "__main__":
    import uvicorn
    # This will run the server on http://127.0.0.1:8001
    uvicorn.run(app, host="127.0.0.1", port=8001)