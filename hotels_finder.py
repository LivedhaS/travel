import os
from typing import Optional
from serpapi import GoogleSearch
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class HotelsInput(BaseModel):
    q: str = Field(description='City or location')
    check_in_date: str = Field(description='YYYY-MM-DD')
    check_out_date: str = Field(description='YYYY-MM-DD')
    sort_by: Optional[str] = Field(None)
    adults: Optional[int] = Field(1)
    children: Optional[int] = Field(0)
    rooms: Optional[int] = Field(1)
    hotel_class: Optional[str] = Field(None)


class HotelsInputSchema(BaseModel):
    params: HotelsInput


@tool(args_schema=HotelsInputSchema)
def hotels_finder(params: HotelsInput):
    """Find hotels using Google Hotels (SerpAPI)"""
    api_key = os.environ.get('SERPAPI_API_KEY')
    if not api_key:
        return "Error: SERPAPI_API_KEY not found"

    query = {
        'api_key': api_key,
        'engine': 'google_hotels',
        'hl': 'en',
        'gl': 'us',
        'q': params.q,
        'check_in_date': params.check_in_date,
        'check_out_date': params.check_out_date,
        'currency': 'USD',
        'adults': params.adults,
        'children': params.children,
        'rooms': params.rooms,
        'sort_by': params.sort_by,
        'hotel_class': params.hotel_class
    }

    try:
        search = GoogleSearch(query)
        results = search.get_dict()
        properties = results.get('properties', [])[:5]

        formatted = []
        for h in properties:
            formatted.append({
                "name": h.get("name", "Unknown"),
                "star_rating": h.get("hotel_class", "N/A"),
                "rating": h.get("overall_rating", "N/A"),
                "reviews": h.get("reviews", "N/A"),
                "location": h.get("neighborhood", h.get("location", "N/A")),
                "price_per_night": h.get("rate_per_night", {}).get("lowest", "N/A"),
                "total_price": h.get("total_rate", {}).get("lowest", "N/A"),
                "amenities": h.get("amenities", [])[:5],
                "description": h.get("description", "N/A")
            })

        return formatted if formatted else "No hotels found."

    except Exception as e:
        return f"Tool error: {str(e)}"