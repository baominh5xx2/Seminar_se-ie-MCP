"""
AI Assistant MCP Server
Professional FastMCP implementation with modular architecture
"""
from fastmcp import FastMCP
from src.mcp_server.core.config import settings
from src.mcp_server.tools import register_all_tools
from src.mcp_server.resources import register_all_resources
from src.mcp_server.prompts import register_all_prompts
from src.mcp_server.utils import setup_logging

# Setup logging
logger = setup_logging(settings.LOG_LEVEL)

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.SERVER_NAME,
    version=settings.SERVER_VERSION,
    dependencies=["httpx", "pydantic", "pydantic-settings"]
)

# Register all components
logger.info("Registering MCP tools...")
register_all_tools(mcp)

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
