"""
Demo script for searching flights between airports
Demonstrates the FlightService functionality
"""

import asyncio
from src.mcp_server.tools.flight_tools import FlightService


async def search_vietnam_flights():
    """
    Demo function to search for flights on various routes
    """
    # Create flight service instance
    flight_service = FlightService()
    
    # Demo 1: Hanoi to Ho Chi Minh City
    print("\n" + "=" * 70)
    print("🔎 Demo 1: Tìm chuyến bay Hà Nội → Sài Gòn")
    print("=" * 70)
    result = await flight_service.search_flights(
        departure_iata="HAN",  # Hanoi
        arrival_iata="SGN",    # Ho Chi Minh City
        limit=5,               # Show 5 flights
        future_only=True       # Only show future flights
    )
    print(result)
    
    # Demo 2: Ho Chi Minh City to Da Nang
    print("\n\n" + "=" * 70)
    print("🔎 Demo 2: Tìm chuyến bay Sài Gòn → Đà Nẵng")
    print("=" * 70)
    result = await flight_service.search_flights(
        departure_iata="SGN",  # Ho Chi Minh City
        arrival_iata="DAD",    # Da Nang
        limit=5,               # Show 5 flights
        future_only=True       # Only show future flights
    )
    print(result)
    
    # Demo 3: Ho Chi Minh City to Singapore
    print("\n\n" + "=" * 70)
    print("🔎 Demo 3: Tìm chuyến bay Sài Gòn → Singapore")
    print("=" * 70)
    result = await flight_service.search_flights(
        departure_iata="SGN",  # Ho Chi Minh City
        arrival_iata="SIN",    # Singapore
        limit=5,               # Show 5 flights
        future_only=True       # Only show future flights
    )
    print(result)


if __name__ == "__main__":
    print("\n" + "🛫" * 35)
    print("   FLIGHT SEARCH DEMO - AviationStack API")
    print("🛫" * 35)
    asyncio.run(search_vietnam_flights())
    print("\n" + "=" * 70)
    print("✅ Demo completed!")
    print("=" * 70 + "\n")
