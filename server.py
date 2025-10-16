"""
AI Assistant MCP Server
Professional FastMCP implementation with modular architecture
"""
from fastmcp import FastMCP
from src.mcp_server.core.config import settings
from src.mcp_server.utils import setup_logging

# Import individual tool registrations
from src.mcp_server.tools.booking_tools import register_booking_tools
from src.mcp_server.tools.flight_tools import register_flight_tools
from src.mcp_server.tools.weather_tools import register_weather_tools
from src.mcp_server.resources import register_all_resources
from src.mcp_server.prompts import register_all_prompts

# Setup logging
logger = setup_logging(settings.LOG_LEVEL)

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.SERVER_NAME,
    version=settings.SERVER_VERSION,
    dependencies=["httpx", "pydantic", "pydantic-settings"]
)

# ============================================================================
# REGISTER TOOLS - Comment out tools you don't want to use
# ============================================================================
logger.info("Registering MCP tools...")

# Booking Tools (Tour search, booking management)
register_booking_tools(mcp)

# Flight Tools (Flight search) - Uncomment to enable
register_flight_tools(mcp)

# Weather Tools (Weather forecast) - Uncomment to enable
register_weather_tools(mcp)


# ============================================================================
# REGISTER RESOURCES & PROMPTS
# ============================================================================
logger.info("Registering MCP resources...")
register_all_resources(mcp)

logger.info("Registering MCP prompts...")
register_all_prompts(mcp)

logger.info(f"✅ {settings.SERVER_NAME} v{settings.SERVER_VERSION} initialized successfully")


def main():
    """Main entry point for the MCP server"""
    logger.info(f"🚀 Starting {settings.SERVER_NAME}...")
    logger.info(f"Backend API: {settings.BACKEND_API_URL}")
    logger.info(f"Max Iterations: {settings.MAX_ITERATIONS}")
    logger.info(f"Timeout: {settings.TIMEOUT}s")
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
