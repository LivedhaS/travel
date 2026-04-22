import os
import json
import folium
import tempfile
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import Optional


class MapInput(BaseModel):
    destination_city: str = Field(description="Destination city e.g. Amsterdam")
    origin_city: Optional[str] = Field(None, description="Origin city e.g. Madrid")
    hotels: Optional[str] = Field(None, description="JSON string of hotel names")


class MapInputSchema(BaseModel):
    params: MapInput


@tool(args_schema=MapInputSchema)
def map_generator(params: MapInput):
    """Generate an interactive map showing flight route and hotel locations"""
    try:
        geolocator = Nominatim(user_agent="travel-agent")

        dest_location = geolocator.geocode(params.destination_city)
        if not dest_location:
            return f"Could not find location for {params.destination_city}"

        travel_map = folium.Map(
            location=[dest_location.latitude, dest_location.longitude],
            zoom_start=12
        )

        folium.Marker(
            location=[dest_location.latitude, dest_location.longitude],
            popup=f"📍 {params.destination_city}",
            tooltip=params.destination_city,
            icon=folium.Icon(color="red", icon="star")
        ).add_to(travel_map)

        if params.origin_city:
            origin_location = geolocator.geocode(params.origin_city)
            if origin_location:
                folium.Marker(
                    location=[origin_location.latitude, origin_location.longitude],
                    popup=f"✈️ {params.origin_city}",
                    tooltip=f"Departure: {params.origin_city}",
                    icon=folium.Icon(color="blue", icon="plane")
                ).add_to(travel_map)

                folium.PolyLine(
                    locations=[
                        [origin_location.latitude, origin_location.longitude],
                        [dest_location.latitude, dest_location.longitude]
                    ],
                    color="blue",
                    weight=2,
                    opacity=0.7,
                    dash_array="10"
                ).add_to(travel_map)

        if params.hotels:
            try:
                hotel_list = json.loads(params.hotels)
                for hotel in hotel_list:
                    hotel_name = hotel.get("name", "Hotel")
                    hotel_location_str = f"{hotel_name}, {params.destination_city}"
                    hotel_location = geolocator.geocode(hotel_location_str)
                    if hotel_location:
                        folium.Marker(
                            location=[hotel_location.latitude, hotel_location.longitude],
                            popup=f"🏨 {hotel_name}",
                            tooltip=hotel_name,
                            icon=folium.Icon(color="green", icon="home")
                        ).add_to(travel_map)
            except Exception:
                pass

        map_path = os.path.join(tempfile.gettempdir(), "travel_map.html")
        travel_map.save(map_path)
        with open(map_path, "r", encoding="utf-8", errors="replace") as f:
            map_content = f.read()
        with open(map_path, "w", encoding="utf-8") as f:
             f.write(map_content)

        return {
            "status": "success",
            "message": f"Map generated for {params.destination_city}",
            "map_path": map_path,
            "destination": {
                "city": params.destination_city,
                "lat": dest_location.latitude,
                "lon": dest_location.longitude
            }
        }

    except Exception as e:
        return f"Map error: {str(e)}"