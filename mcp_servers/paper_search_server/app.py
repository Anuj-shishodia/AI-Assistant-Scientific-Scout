# mcp_servers/paper_search_server/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import arxiv

app = FastAPI(
    title="Paper Search MCP Server",
    description="Searches arXiv for recent research papers."
)

class SearchRequest(BaseModel):
    query: str = Field(..., example="large language models")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of results to return")

class PaperResult(BaseModel):
    title: str
    authors: list[str]
    summary: str
    url: str
    published_date: str

@app.post("/search_papers", response_model=list[PaperResult])
async def search_papers(request: SearchRequest):
    """
    Queries the public arXiv API for papers matching the given query.
    Returns a list of paper details.
    """
    try:
        search = arxiv.Search(
            query=request.query,
            max_results=request.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        papers = []
        for result in search.results():
            papers.append(PaperResult(
                title=result.title,
                authors=[author.name for author in result.authors],
                summary=result.summary,
                url=result.entry_id,
                published_date=result.published.strftime("%Y-%m-%d")
            ))
        return papers
    except Exception as e:
        print(f"Error searching arXiv: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search arXiv: {e}")

if __name__ == "__main__":
    import uvicorn
    # This will run the server on http://127.0.0.1:8000
    uvicorn.run(app, host="127.0.0.1", port=8000)