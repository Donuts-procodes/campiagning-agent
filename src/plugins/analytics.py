from langchain_core.tools import tool


@tool
def get_historical_cpa(channel: str, industry: str) -> float:
    """
    Retrieves the historical Cost Per Action (CPA) for a given marketing channel and industry.
    
    Args:
        channel: The marketing channel (e.g., 'meta', 'google', 'klaviyo', 'linkedin').
        industry: The industry of the brand (e.g., 'ecommerce', 'b2b SaaS').
        
    Returns:
        float: The estimated historical CPA.
    """
    # Mock data for demonstration purposes
    base_cpa = {
        "meta": 15.50,
        "google": 12.00,
        "linkedin": 45.00,
        "klaviyo": 5.00,
        "whatsapp": 2.50
    }
    return base_cpa.get(channel.lower(), 20.00)

@tool
def get_audience_engagement_metrics(segment_name: str) -> dict:
    """
    Retrieves historical engagement metrics for a specific target audience segment.
    
    Args:
        segment_name: The name or description of the audience segment.
        
    Returns:
        dict: A dictionary containing metrics like CTR (click-through rate) and conversion rate.
    """
    # Mock data for demonstration purposes
    return {
        "ctr": 0.025,
        "conversion_rate": 0.012,
        "avg_time_on_page_seconds": 45
    }
