from langchain_core.tools import tool


@tool
def competitor_strategy_search(brand_name: str, industry: str) -> str:
    """
    Performs a web search to identify recent marketing strategies and ad campaigns 
    run by competitors in the given industry.
    
    Args:
        brand_name: The name of the brand.
        industry: The industry the brand operates in.
        
    Returns:
        str: A summary of competitor strategies found on the web.
    """
    # Mock search functionality for demonstration purposes
    # In a real implementation, this would call Tavily API, Serper, or DuckDuckGo
    return (
        f"Search results for competitors of {brand_name} in {industry}:\n"
        "- Competitor A is heavily investing in short-form video on Meta (Reels).\n"
        "- Competitor B recently launched a retargeting campaign on Google Display Network.\n"
        "- Industry trend shows a 15% shift towards WhatsApp conversational marketing."
    )
