"""Tools package - Register all MCP tools"""
from fastmcp import FastMCP
from .chat_tools import register_chat_tools
from .agent_tools import register_agent_tools
from .weather_tools import register_weather_tools
from .flight_tools import register_flight_tools


def register_all_tools(mcp: FastMCP):
    """
    Register all MCP tools
    
    Args:
        mcp: FastMCP server instance
    """
    register_chat_tools(mcp)
    register_agent_tools(mcp)
    register_weather_tools(mcp)
    register_flight_tools(mcp)


__all__ = [
    "register_all_tools",
    "register_chat_tools",
    "register_agent_tools",
    "register_weather_tools",
    "register_flight_tools"
]
