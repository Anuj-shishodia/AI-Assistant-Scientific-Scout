# agent_host/main.py

import requests
import time
import logging
import os
from dotenv import load_dotenv

# Load environment variables for server URLs
load_dotenv()

# --- Configuration ---
PAPER_SEARCH_SERVER_URL = os.getenv("PAPER_SEARCH_SERVER_URL", "http://127.0.0.1:8000")
PDF_SUMMARIZE_SERVER_URL = os.getenv("PDF_SUMMARIZE_SERVER_URL", "http://127.0.0.1:8001")

# --- Logging Setup ---
# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Tool Call Logging Function ---
def log_tool_call(tool_name: str, args: dict, start_time: float, outcome: str, latency: float = None):
    """Logs details about a tool call."""
    log_message = f"Tool Call: {tool_name}(args={args})"
    if latency is not None:
        log_message += f", Latency: {latency:.2f}s"
    log_message += f", Outcome: {outcome}"
    logger.info(log_message)

class PaperScoutAgent:
    def search_papers(self, query: str, max_results: int = 5) -> list:
        """Calls the paper_search MCP server to find papers."""
        tool_name = "paper_search"
        args = {"query": query, "max_results": max_results}
        start_time = time.time()
        try:
            response = requests.post(
                f"{PAPER_SEARCH_SERVER_URL}/search_papers",
                json=args,
                timeout=30 # Add a timeout for HTTP requests
            )
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            papers = response.json()
            latency = time.time() - start_time
            log_tool_call(tool_name, args, start_time, "Success", latency)
            return papers
        except requests.exceptions.ConnectionError:
            latency = time.time() - start_time
            log_tool_call(tool_name, args, start_time, "Connection Failed", latency)
            print(f"Error: Could not connect to Paper Search Server at {PAPER_SEARCH_SERVER_URL}.")
            print("Please ensure the 'paper_search_server' is running.")
            return []
        except requests.exceptions.RequestException as e:
            latency = time.time() - start_time
            log_tool_call(tool_name, args, start_time, f"Request Failed: {e}", latency)
            print(f"Error calling Paper Search Server: {e}")
            return []
        except Exception as e:
            latency = time.time() - start_time
            log_tool_call(tool_name, args, start_time, f"Unexpected Error: {e}", latency)
            print(f"An unexpected error occurred during paper search: {e}")
            return []

    def summarize_pdf(self, pdf_url: str) -> str:
        """Calls the pdf_summarize MCP server to summarize a PDF."""
        tool_name = "pdf_summarize"
        args = {"pdf_url": pdf_url}
        start_time = time.time()
        try:
            response = requests.post(
                f"{PDF_SUMMARIZE_SERVER_URL}/summarize_pdf",
                json=args,
                timeout=120 # PDF download and LLM can take longer
            )
            response.raise_for_status()
            summary = response.json().get("summary", "No summary received.")
            latency = time.time() - start_time
            log_tool_call(tool_name, args, start_time, "Success", latency)
            return summary
        except requests.exceptions.ConnectionError:
            latency = time.time() - start_time
            log_tool_call(tool_name, args, start_time, "Connection Failed", latency)
            print(f"Error: Could not connect to PDF Summarize Server at {PDF_SUMMARIZE_SERVER_URL}.")
            print("Please ensure the 'pdf_summarize_server' is running.")
            return "Failed to connect to summarization service."
        except requests.exceptions.RequestException as e:
            latency = time.time() - start_time
            log_tool_call(tool_name, args, start_time, f"Request Failed: {e}", latency)
            print(f"Error calling PDF Summarize Server: {e}")
            return f"Failed to summarize PDF: {e}"
        except Exception as e:
            latency = time.time() - start_time
            log_tool_call(tool_name, args, start_time, f"Unexpected Error: {e}", latency)
            print(f"An unexpected error occurred during PDF summarization: {e}")
            return f"An unexpected error occurred during summarization: {e}"

    def discover_and_summarize_papers(self, topic: str, num_papers: int = 3):
        """Orchestrates paper discovery and summarization."""
        print(f"\nAI Scout: Searching for recent papers on '{topic}'...")

        papers = self.search_papers(topic, num_papers)

        if not papers:
            print("AI Scout: No papers found for your topic.")
            return

        print(f"AI Scout: Found {len(papers)} paper(s). Now summarizing...")

        for i, paper in enumerate(papers):
            print(f"\n--- Paper {i+1}/{len(papers)} ---")
            print(f"Title: {paper.get('title', 'N/A')}")
            print(f"Authors: {', '.join(paper.get('authors', ['N/A']))}")
            print(f"Published: {paper.get('published_date', 'N/A')}")
            print(f"URL: {paper.get('url', 'N/A')}")

            pdf_url = paper.get('url')
            if pdf_url and '.pdf' in pdf_url: # Basic check for PDF URL
                print("AI Scout: Requesting PDF summary...")
                summary = self.summarize_pdf(pdf_url)
                print(f"AI Scout Summary:\n{summary}")
            else:
                print("AI Scout: No direct PDF URL found or URL is not a PDF. Cannot summarize.")
                # Fallback to abstract if no PDF and if you want to use a LLM here.
                # For this architecture, abstract summarization would also need to go through an MCP server.
                # For now, stick to PDF summarization.
                if paper.get('summary'):
                     print(f"Original Abstract:\n{paper.get('summary')}")


def main():
    print("Welcome to the AI Scientific Paper Scout (Kairos Edition)!")
    print("This agent discovers and summarizes recent research papers.")
    print("Before starting, ensure both MCP servers are running:")
    print(f"  - Paper Search Server: {PAPER_SEARCH_SERVER_URL}")
    print(f"  - PDF Summarize Server: {PDF_SUMMARIZE_SERVER_URL}")
    print("Type 'exit' or 'quit' to end the session.")

    agent = PaperScoutAgent()

    while True:
        topic = input("\nEnter a research topic (e.g., 'causal inference in AI'): ").strip()
        if topic.lower() in ['exit', 'quit']:
            print("Exiting Paper Scout. Goodbye!")
            break

        try:
            num_papers_str = input("How many papers to scout? (default: 3): ").strip()
            num_papers = int(num_papers_str) if num_papers_str else 3
            if num_papers <= 0:
                print("Please enter a positive number.")
                continue
        except ValueError:
            print("Invalid number. Please enter a whole number.")
            continue

        agent.discover_and_summarize_papers(topic, num_papers)

if __name__ == "__main__":
    main()