"""
MCP Tools - Weather Tools
Get current weather and forecasts using OpenWeatherMap API
"""
from fastmcp import FastMCP
from typing import Dict, Any
import httpx
from datetime import datetime, timezone, timedelta
from ..core.config import settings


def register_weather_tools(mcp: FastMCP):
    """Register weather-related tools"""
    
    @mcp.tool()
    async def get_current_temperature_by_city(city_name: str) -> str:
        api_key = settings.WEATHER_API_KEY
        if not api_key:
            return "Error: WEATHER_API_KEY not found in environment variables"
        try:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {"q": city_name, "appid": api_key, "units": "metric"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()

            # --- weather fields ---
            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]

            # --- Force Vietnam timezone UTC+7 ---
            obs_ts = data.get("dt")  # epoch seconds (UTC)
            
            if obs_ts is None:
                # fallback to current UTC if API didn't provide dt
                obs_dt_utc = datetime.now(timezone.utc)
            else:
                obs_dt_utc = datetime.fromtimestamp(obs_ts, tz=timezone.utc)

            # Always use Vietnam timezone UTC+7
            vietnam_tz = timezone(timedelta(hours=7))
            local_dt = obs_dt_utc.astimezone(vietnam_tz)
            time_str = local_dt.strftime("%Y-%m-%d %H:%M:%S")

            return (
                f"Weather in {city_name} at {time_str} (Vietnam time UTC+7): "
                f"{temperature:.1f}°C (feels like {feels_like:.1f}°C), {description}, humidity: {humidity}%"
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Error: City '{city_name}' not found."
            if e.response.status_code == 401:
                return "Error: Invalid API key."
            return f"Error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Unexpected error: {e}"


    # --- FORECAST (sửa) ---
    @mcp.tool()
    async def get_weather_forecast_by_city(city_name: str, days: int = 5) -> str:
        api_key = settings.WEATHER_API_KEY
        if not api_key:
            return "Error: WEATHER_API_KEY not found in environment variables"
        days = max(1, min(days, 5))
        try:
            url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {"q": city_name, "appid": api_key, "units": "metric", "cnt": days * 8}
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()

            forecast_list = data.get("list", [])
            
            # Always use Vietnam timezone UTC+7
            vietnam_tz = timezone(timedelta(hours=7))
            daily = {}
            for item in forecast_list:
                utc_dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
                local_dt = utc_dt.astimezone(vietnam_tz)
                date_key = local_dt.strftime("%Y-%m-%d")

                if date_key not in daily:
                    daily[date_key] = {"temps": [], "humidity": [], "weather": [], "rain_prob": []}

                daily[date_key]["temps"].append(item["main"]["temp"])
                daily[date_key]["humidity"].append(item["main"]["humidity"])
                daily[date_key]["weather"].append(item["weather"][0]["description"])
                if "pop" in item:
                    daily[date_key]["rain_prob"].append(item["pop"] * 100)

            # Format
            result = f"Weather forecast for {city_name} (Vietnam time UTC+7):\n\n"
            for date, d in list(daily.items())[:days]:
                avg_temp = sum(d["temps"]) / len(d["temps"])
                min_t, max_t = min(d["temps"]), max(d["temps"])
                avg_h = sum(d["humidity"]) / len(d["humidity"])
                most_common = max(set(d["weather"]), key=d["weather"].count)
                avg_rain = sum(d["rain_prob"]) / len(d["rain_prob"]) if d["rain_prob"] else 0
                result += (
                    f"📅 {date}:\n"
                    f"   🌡️  Temp: {min_t:.1f}°C - {max_t:.1f}°C (avg: {avg_temp:.1f}°C)\n"
                    f"   ☁️  Weather: {most_common}\n"
                    f"   💧 Humidity: {avg_h:.0f}%\n"
                    f"   🌧️  Rain chance: {avg_rain:.0f}%\n\n"
                )
            return result.strip()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Error: City '{city_name}' not found."
            if e.response.status_code == 401:
                return "Error: Invalid API key."
            return f"Error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Unexpected error: {e}"

