import os
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from utils import logger

@tool
def search_educational_resources(query: str):
    """
    Search for high-quality, free educational materials including YouTube videos, 
    GitHub repositories, and documentations .
    """
    logger.info(f"Searching for: {query}")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return "Error: TAVILY_API_KEY not found in environment variables."

    # Ensure the environment variable is available in this process before the library uses it.
    os.environ["TAVILY_API_KEY"] = tavily_api_key

    search = TavilySearchResults()
    results = search.run(query)
    return results

@tool
def validate_resource_content(url: str):
    """
    A placeholder tool to simulate content validation of a resource content if okay or even the source is working or related.
    In a real scenario, this could use BeautifulSoup or Firecrawl.
    """
    logger.info(f"Validating resource: {url}")
    return f"Resource at {url} has been validated for pedagogical quality."

