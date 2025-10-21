"""
AI Assistant MCP Server - STDIO Mode
For use with Cursor and Claude Desktop
"""
import sys
import asyncio
from fastmcp import FastMCP
from src.mcp_server.core.config import settings
from src.mcp_server.tools import register_all_tools
from src.mcp_server.resources import register_all_resources
from src.mcp_server.prompts import register_all_prompts
from src.mcp_server.utils import setup_logging

# Setup logging to stderr (not stdout, which is used for MCP protocol)
logger = setup_logging(settings.LOG_LEVEL)
logger.info("Initializing MCP server in STDIO mode...")

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.SERVER_NAME,
    version=settings.SERVER_VERSION
)

# Register all components
logger.info("Registering MCP tools...")
register_all_tools(mcp)

logger.info("Registering MCP resources...")
register_all_resources(mcp)

logger.info("Registering MCP prompts...")
register_all_prompts(mcp)

logger.info(f"✅ {settings.SERVER_NAME} v{settings.SERVER_VERSION} initialized successfully")
logger.info("Starting STDIO transport...")

if __name__ == "__main__":
    # Run in STDIO mode for Cursor/Claude Desktop
    mcp.run()

