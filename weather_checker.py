import os
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class WeatherInput(BaseModel):
    city: str = Field(description="City name e.g. Amsterdam")
    date: str = Field(description="Date in YYYY-MM-DD format")


class WeatherInputSchema(BaseModel):
    params: WeatherInput


@tool(args_schema=WeatherInputSchema)
def weather_checker(params: WeatherInput):
    """Check weather forecast for a city on a specific date"""
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OPENWEATHER_API_KEY not found"

    try:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={params.city}&limit=1&appid={api_key}"
        geo_response = requests.get(geo_url).json()

        if not geo_response:
            return f"City {params.city} not found"

        lat = geo_response[0]["lat"]
        lon = geo_response[0]["lon"]

        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        forecast_response = requests.get(forecast_url).json()

        forecasts = []
        for item in forecast_response.get("list", []):
            if params.date in item["dt_txt"]:
                forecasts.append({
                    "date": item["dt_txt"],
                    "temperature": f"{item['main']['temp']}°C",
                    "feels_like": f"{item['main']['feels_like']}°C",
                    "min_temp": f"{item['main']['temp_min']}°C",
                    "max_temp": f"{item['main']['temp_max']}°C",
                    "humidity": f"{item['main']['humidity']}%",
                    "description": item["weather"][0]["description"].title(),
                    "wind_speed": f"{item['wind']['speed']} m/s"
                })

        if not forecasts:
            return f"No forecast available for {params.city} on {params.date}. Note: forecast only available up to 5 days ahead."

        return {
            "city": params.city,
            "date": params.date,
            "forecasts": forecasts
        }

    except Exception as e:
        return f"Weather error: {str(e)}"