import os
from typing import Optional
from serpapi import GoogleSearch
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class FlightsInput(BaseModel):
    departure_airport: Optional[str] = Field(None, description='Departure airport IATA code')
    arrival_airport: Optional[str] = Field(None, description='Arrival airport IATA code')
    outbound_date: Optional[str] = Field(None, description='YYYY-MM-DD')
    return_date: Optional[str] = Field(None, description='YYYY-MM-DD')
    adults: Optional[int] = Field(1)
    children: Optional[int] = Field(0)
    infants_in_seat: Optional[int] = Field(0)
    infants_on_lap: Optional[int] = Field(0)


class FlightsInputSchema(BaseModel):
    params: FlightsInput


@tool(args_schema=FlightsInputSchema)
def flights_finder(params: FlightsInput):
    """Find flights using Google Flights (SerpAPI)"""
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        return "Error: SERPAPI_API_KEY not found"

    query = {
        "api_key": api_key,
        "engine": "google_flights",
        "hl": "en",
        "gl": "us",
        "departure_id": params.departure_airport,
        "arrival_id": params.arrival_airport,
        "outbound_date": params.outbound_date,
        "return_date": params.return_date,
        "currency": "USD",
        "adults": params.adults,
        "children": params.children,
        "infants_in_seat": params.infants_in_seat,
        "infants_on_lap": params.infants_on_lap,
        "stops": "1"
    }

    try:
        search = GoogleSearch(query)
        response = search.get_dict()
        best_flights = response.get("best_flights", [])[:3]
        other_flights = response.get("other_flights", [])[:2]
        all_flights = best_flights + other_flights

        formatted = []
        for f in all_flights:
            legs = f.get("flights", [])
            first_leg = legs[0] if legs else {}
            formatted.append({
                "airline": first_leg.get("airline", f.get("airline", "Unknown")),
                "flight_number": first_leg.get("flight_number", "N/A"),
                "departure_airport": first_leg.get("departure_airport", {}).get("name", "N/A"),
                "departure_time": first_leg.get("departure_airport", {}).get("time", "N/A"),
                "arrival_airport": first_leg.get("arrival_airport", {}).get("name", "N/A"),
                "arrival_time": first_leg.get("arrival_airport", {}).get("time", "N/A"),
                "duration": f.get("total_duration", "N/A"),
                "stops": len(legs) - 1 if legs else 0,
                "price": f.get("price", "N/A"),
                "type": "Best" if f in best_flights else "Other"
            })

        return formatted if formatted else "No flights found."

    except Exception as e:
        return f"Tool error: {str(e)}"