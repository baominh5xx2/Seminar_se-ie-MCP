"""
Demo script for Weather Tools
Run this to test weather tools functionality
"""
import asyncio
from src.mcp_server.core.config import settings
from src.mcp_server.tools.weather_tools import register_weather_tools
from fastmcp import FastMCP
from datetime import datetime, timezone


async def test_weather_tools():
    """Test weather tools"""
    
    print("=" * 60)
    print("🌤️  Weather Tools Demo")
    print("=" * 60)
    print()
    
    # Initialize FastMCP
    mcp = FastMCP(name="weather-demo")
    register_weather_tools(mcp)
    
    # Test cities
    cities = [
        ("Ho Chi Minh", "Thành phố Hồ Chí Minh"),
        ("Soc Trang", "Sóc Trăng"),
        ("Hanoi", "Hà Nội"),
    ]
    
    print("📍 Testing Current Weather")
    print("-" * 60)
    
    for city_en, city_vi in cities:
        print(f"\n🌍 {city_vi} ({city_en}):")
        try:
            import httpx
            
            api_key = settings.WEATHER_API_KEY
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city_en,
                "appid": api_key,
                "units": "metric"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                temperature = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                description = data["weather"][0]["description"]
                
                timezone_offset = data["timezone"]
                utc_time = datetime.now(timezone.utc)
                local_time = utc_time.timestamp() + timezone_offset
                local_datetime = datetime.fromtimestamp(local_time)
                time_str = local_datetime.strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"   ⏰ Time: {time_str} (local)")
                print(f"   🌡️  Temp: {temperature}°C (feels like {feels_like}°C)")
                print(f"   ☁️  Conditions: {description}")
                print(f"   💧 Humidity: {humidity}%")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print()
    print("=" * 60)
    print("📅 Testing Weather Forecast (3 days)")
    print("-" * 60)
    
    # Test forecast for one city
    test_city = "Ho Chi Minh"
    print(f"\n🌍 Forecast for {test_city}:")
    
    try:
        api_key = settings.WEATHER_API_KEY or "231783af55a5c399df3b94edaa86d763"
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": test_city,
            "appid": api_key,
            "units": "metric",
            "cnt": 24  # 3 days * 8 entries
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            forecast_list = data["list"]
            timezone_offset = data["city"]["timezone"]
            
            # Group by day
            daily_forecasts = {}
            for item in forecast_list:
                timestamp = item["dt"]
                local_datetime = datetime.fromtimestamp(timestamp + timezone_offset)
                date_key = local_datetime.strftime("%Y-%m-%d")
                
                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = {
                        "temps": [],
                        "humidity": [],
                        "weather": [],
                        "rain_prob": []
                    }
                
                daily_forecasts[date_key]["temps"].append(item["main"]["temp"])
                daily_forecasts[date_key]["humidity"].append(item["main"]["humidity"])
                daily_forecasts[date_key]["weather"].append(item["weather"][0]["description"])
                
                if "pop" in item:
                    daily_forecasts[date_key]["rain_prob"].append(item["pop"] * 100)
            
            # Display forecast
            for date, day_data in list(daily_forecasts.items())[:3]:
                avg_temp = sum(day_data["temps"]) / len(day_data["temps"])
                min_temp = min(day_data["temps"])
                max_temp = max(day_data["temps"])
                avg_humidity = sum(day_data["humidity"]) / len(day_data["humidity"])
                most_common_weather = max(set(day_data["weather"]), key=day_data["weather"].count)
                avg_rain = sum(day_data["rain_prob"]) / len(day_data["rain_prob"]) if day_data["rain_prob"] else 0
                
                print(f"\n   📅 {date}:")
                print(f"      🌡️  Temp: {min_temp:.1f}°C - {max_temp:.1f}°C (avg: {avg_temp:.1f}°C)")
                print(f"      ☁️  Weather: {most_common_weather}")
                print(f"      💧 Humidity: {avg_humidity:.0f}%")
                print(f"      🌧️  Rain chance: {avg_rain:.0f}%")
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    print("=" * 60)
    print("✅ Demo completed!")
    print("=" * 60)


def main():
    """Main entry point"""
    print("\n🌤️  Weather Tools Demo Script")
    print(f"API Key configured: {'Yes' if settings.WEATHER_API_KEY else 'Using default'}")
    print()
    
    # Run async tests
    asyncio.run(test_weather_tools())


if __name__ == "__main__":
    main()

