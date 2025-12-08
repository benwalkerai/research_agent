from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from typing import Type, Optional, Any
from pydantic import BaseModel, Field
import time


class SerperSearchInput(BaseModel):
    """Input schema for SerperSearchTool."""
    search_query: str = Field(..., description="The search query to execute")


class SerperSearchToolWithRetry(BaseTool):
    """
    Custom wrapper around SerperDevTool with retry limit.
    Prevents infinite retry loops when Serper API fails.
    """
    name: str = "serper_search"
    description: str = (
        "A search tool that uses Serper API to search the internet. "
        "Useful for finding current information, news, articles, and data. "
        "Limited to 3 retry attempts to prevent hanging on failures."
    )
    args_schema: Type[BaseModel] = SerperSearchInput
    
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds between retries
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._serper_tool = SerperDevTool()
        self._attempt_count = {}  # Track attempts per query
    
    def _run(self, search_query: str) -> str:
        """
        Execute search with retry limit.
        
        Args:
            search_query: The search query string
            
        Returns:
            Search results or error message if max retries exceeded
        """
        # Use query hash as key to track retries
        query_key = hash(search_query)
        
        # Initialize attempt counter for this query
        if query_key not in self._attempt_count:
            self._attempt_count[query_key] = 0
        
        attempt = self._attempt_count[query_key]
        
        # Check if we've exceeded max retries
        if attempt >= self.max_retries:
            error_msg = (
                f"⚠️ Search failed after {self.max_retries} attempts. "
                f"Query: '{search_query[:100]}...'. "
                f"Moving on without this search result."
            )
            print(error_msg)
            # Reset counter for potential future use
            del self._attempt_count[query_key]
            return error_msg
        
        try:
            # Increment attempt counter
            self._attempt_count[query_key] += 1
            
            if attempt > 0:
                print(f"🔄 Retry attempt {attempt + 1}/{self.max_retries} for query: {search_query[:50]}...")
                time.sleep(self.retry_delay)
            
            # Execute the actual search
            result = self._serper_tool._run(search_query=search_query)
            
            # Success - reset counter
            if query_key in self._attempt_count:
                del self._attempt_count[query_key]
            
            return result
            
        except Exception as e:
            error_msg = f"Search error (attempt {attempt + 1}/{self.max_retries}): {str(e)}"
            print(error_msg)
            
            # If this was the last attempt, clean up and return error
            if self._attempt_count[query_key] >= self.max_retries:
                del self._attempt_count[query_key]
                return f"⚠️ Search failed after {self.max_retries} attempts: {str(e)}"
            
            # Re-raise to trigger CrewAI's retry mechanism
            raise
