
from fastmcp import FastMCP
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timezone, timedelta

# Handle both direct execution and module import
try:
    from ..core.config import settings
except ImportError:
    # Direct execution - add parent directory to path
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from src.mcp_server.core.config import settings


class FlightService:
    """
    Flight Service class for retrieving flight information.
    
    This class provides methods to search for flights between airports
    using the AviationStack API. All times are converted to Vietnam
    timezone (UTC+7) for consistency.
    
    Attributes:
        api_key (str): AviationStack API key
        base_url (str): Base URL for AviationStack API
        vietnam_tz (timezone): Vietnam timezone (UTC+7)
        default_limit (int): Default number of flights to return
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FlightService with API key.
        
        Args:
            api_key (Optional[str]): AviationStack API key. 
                                    If not provided, uses settings.FLIGHT_API_KEY
        """
        self.api_key = api_key or settings.FLIGHT_API_KEY
        self.base_url = "http://api.aviationstack.com/v1"
        self.vietnam_tz = timezone(timedelta(hours=7))
        self.default_limit = 5
    
    def _format_datetime(self, dt_string: Optional[str]) -> str:
        """
        Convert ISO datetime string to Vietnam timezone with detailed date information.
        
        This is a helper method to parse and convert datetime strings
        from the API response to Vietnam timezone with day, month, year details.
        
        Args:
            dt_string (Optional[str]): ISO format datetime string
            
        Returns:
            str: Formatted datetime string in Vietnam timezone with detailed date info or "N/A" if input is None
        """
        if not dt_string:
            return "N/A"
        
        try:
            # Parse ISO format datetime
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            
            # Convert to Vietnam timezone
            vietnam_dt = dt.astimezone(self.vietnam_tz)
            
            # Format with detailed date information
            day_name = vietnam_dt.strftime("%A")
            month_name = vietnam_dt.strftime("%B")
            day = vietnam_dt.strftime("%d")
            year = vietnam_dt.strftime("%Y")
            time = vietnam_dt.strftime("%H:%M")
            
            return f"{vietnam_dt.strftime('%Y-%m-%d')} {time} ({day_name}, {month_name} {day}, {year})"
        except Exception:
            return dt_string
    
    def _format_flight_info(self, flight_data: Dict[str, Any]) -> str:
        """
        Format a single flight data object into readable string.
        
        This helper method extracts and formats all relevant flight information
        including departure, arrival, airline, and status details.
        
        Args:
            flight_data (Dict[str, Any]): Flight data dictionary from API
            
        Returns:
            str: Formatted flight information string
            
        """

        # Extract flight information
        flight_number = flight_data.get("flight", {}).get("iata", "N/A")
        airline_name = flight_data.get("airline", {}).get("name", "N/A")
        flight_date = flight_data.get("flight_date", "N/A")
        
        # Extract departure information
        departure = flight_data.get("departure", {})
        dep_airport = departure.get("airport", "N/A")
        dep_iata = departure.get("iata", "N/A")
        dep_terminal = departure.get("terminal", "N/A")
        dep_gate = departure.get("gate", "N/A")
        dep_scheduled = self._format_datetime(departure.get("scheduled"))
        
        # Extract arrival information
        arrival = flight_data.get("arrival", {})
        arr_airport = arrival.get("airport", "N/A")
        arr_iata = arrival.get("iata", "N/A")
        arr_terminal = arrival.get("terminal", "N/A")
        arr_gate = arrival.get("gate", "N/A")
        arr_scheduled = self._format_datetime(arrival.get("scheduled"))
        
        # Format output string with detailed date information
        result = f"✈️  Flight: {flight_number} ({airline_name})\n"
        # Parse and format flight date with detailed information
        try:
            if flight_date != "N/A":
                date_obj = datetime.strptime(flight_date, "%Y-%m-%d")
                day_name = date_obj.strftime("%A")
                month_name = date_obj.strftime("%B")
                day = date_obj.strftime("%d")
                year = date_obj.strftime("%Y")
                result += f"📅 Date: {flight_date} ({day_name}, {month_name} {day}, {year})\n"
            else:
                result += f"📅 Date: {flight_date}\n"
        except Exception:
            result += f"📅 Date: {flight_date}\n"
        
        result += "\n"
        
        # Departure section
        result += f"🛫 Departure:\n"
        result += f"   • Airport: {dep_airport} ({dep_iata})\n"
        result += f"   • Terminal: {dep_terminal}, Gate: {dep_gate}\n"
        result += f"   • Scheduled: {dep_scheduled}\n"
        
        result += "\n"
        
        # Arrival section
        result += f"🛬 Arrival:\n"
        result += f"   • Airport: {arr_airport} ({arr_iata})\n"
        result += f"   • Terminal: {arr_terminal}, Gate: {arr_gate}\n"
        result += f"   • Scheduled: {arr_scheduled}\n"
        
        # Add codeshare information if available
        codeshare = flight_data.get("flight", {}).get("codeshared")
        if codeshare:
            codeshare_airline = codeshare.get("airline_name", "N/A").title()
            codeshare_flight = codeshare.get("flight_iata", "N/A")
            result += f"\n🔗 Operated by: {codeshare_airline} {codeshare_flight}"
        
        return result
    
    async def search_flights(
        self,
        departure_iata: str,
        arrival_iata: str,
        limit: int = 5,
        future_only: bool = True
    ) -> str:
        """
        Search for flights between two airports.
        
        Args:
            departure_iata (str): Departure airport IATA code
            arrival_iata (str): Arrival airport IATA code
            limit (int): Maximum number of results (1-100)
            future_only (bool): Only show future flights
        """
        if not self.api_key:
            return "Error: FLIGHT_API_KEY not found in environment variables"

        departure_iata = departure_iata.upper()
        arrival_iata = arrival_iata.upper()
        limit = max(1, min(limit, 100))

        try:
            url = f"{self.base_url}/flights"
            params = {
                "access_key": self.api_key,
                "dep_iata": departure_iata,
                "arr_iata": arrival_iata,
                "limit": limit,
            }

            # Get current date in Vietnam timezone
            current_time = datetime.now(self.vietnam_tz)
            today = current_time.strftime("%Y-%m-%d")
            params["flight_date"] = today

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=15.0)
                response.raise_for_status()
                data = response.json()

            if "error" in data:
                return f"API Error: {data['error'].get('message', 'Unknown error')}"

            flights = data.get("data", [])
            
            if future_only:
                # Filter future flights
                future_flights = []
                for flight in flights:
                    departure_time = flight.get("departure", {}).get("scheduled")
                    if departure_time:
                        try:
                            departure_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
                            if departure_dt > current_time:
                                future_flights.append(flight)
                        except Exception:
                            continue
                flights = future_flights

            if not flights:
                message = f"No {'future ' if future_only else ''}flights found "
                message += f"from {departure_iata} to {arrival_iata} for {today}.\n"
                message += f"Please check:\n"
                message += f"  • IATA codes are correct\n"
                message += f"  • Route exists and has scheduled flights\n"
                if future_only:
                    message += f"  • Try searching for all flights (including past flights)\n"
                message += f"  • Try different dates"
                return message

            # Format output
            result = f"🔍 Found {len(flights)} {'future ' if future_only else ''}flight(s)\n"
            result += f"From: {departure_iata} → To: {arrival_iata}\n"
            result += f"📅 Date: {today}\n"
            result += f"⏰ All times shown in Vietnam timezone (UTC+7)\n"
            result += "⏰ Times shown in Vietnam timezone (UTC+7)\n\n"
            result += "=" * 60 + "\n\n"

            for i, flight in enumerate(flights, 1):
                result += f"Flight {i}/{len(flights)}\n{'─'*60}\n"
                result += self._format_flight_info(flight)
                result += "\n\n"

            return result + "=" * 60

        except Exception as e:
            return f"Unexpected error: {type(e).__name__} - {e}"



def register_flight_tools(mcp: FastMCP):
    """
    Register flight tools with FastMCP server.
    
    This function creates a FlightService instance and registers its methods
    as MCP tools, allowing them to be called through the MCP protocol.
    
    Args:
        mcp (FastMCP): FastMCP instance to register tools with
        
    """
    
    # Create FlightService instance
    flight_service = FlightService()
    
    @ mcp.tool()
    async def search_flights(
        departure_iata: str,
        arrival_iata: str,
        limit: int = 5,
    ) -> str:
        """
        Search for flights between two airports for current day only.
        """
        return await flight_service.search_flights(departure_iata, arrival_iata, limit)