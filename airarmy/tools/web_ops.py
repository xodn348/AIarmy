import httpx
from .registry import Tool, register


def _web_fetch(url: str, max_length: int = 10000) -> str:
    """Fetch content from a URL and return text up to max_length."""
    try:
        response = httpx.get(url, follow_redirects=True, timeout=15)
        response.raise_for_status()
        return response.text[:max_length]
    except httpx.HTTPError as e:
        return f"Error fetching {url}: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def _web_search(query: str, num_results: int = 5) -> str:
    """Search the web using DuckDuckGo and return formatted results."""
    try:
        from ddgs import DDGS

        results = DDGS().text(query, max_results=num_results)
        if not results:
            return f"No results found for: {query}"

        formatted = []
        for result in results:
            formatted.append(
                f"Title: {result.get('title', 'N/A')}\n"
                f"URL: {result.get('href', 'N/A')}\n"
                f"Snippet: {result.get('body', 'N/A')}\n"
            )
        return "\n".join(formatted)
    except ImportError:
        return "Error: ddgs package not installed. Install with: pip install ddgs"
    except Exception as e:
        return f"Error searching: {str(e)}"


register(
    Tool(
        name="web_fetch",
        description="Fetch content from a URL and return text",
        fn=_web_fetch,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "max_length": {
                    "type": "integer",
                    "description": "Maximum length of returned text (default: 10000)",
                    "default": 10000,
                },
            },
            "required": ["url"],
        },
    )
)

register(
    Tool(
        name="web_search",
        description="Search the web using DuckDuckGo",
        fn=_web_search,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    )
)
