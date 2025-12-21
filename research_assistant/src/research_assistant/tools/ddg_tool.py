from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
from typing import Type
from pydantic import BaseModel, Field

class DuckDuckGoSearchInput(BaseModel):
    """Input schema for DuckDuckGoSearchTool."""
    search_query: str = Field(..., description="The search query to execute")

class DuckDuckGoSearchTool(BaseTool):
    """
    Search tool that uses DuckDuckGo to search the internet.
    Truly free and does not require an API key.
    """
    name: str = "duckduckgo_search"
    description: str = (
        "A search tool that uses DuckDuckGo to search the internet. "
        "Useful for finding current information, news, articles, and data. "
        "It is completely free and requires no API key."
    )
    args_schema: Type[BaseModel] = DuckDuckGoSearchInput
    
    def _run(self, search_query: str) -> str:
        """
        Execute search using DuckDuckGo.
        """
        ddg = DuckDuckGoSearchRun()
        try:
            return ddg.run(search_query)
        except Exception as e:
            return f"⚠️ DuckDuckGo search failed: {str(e)}"
