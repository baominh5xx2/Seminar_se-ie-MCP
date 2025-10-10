"""Resources package - Register all MCP resources"""
from fastmcp import FastMCP
from .conversation_resources import register_conversation_resources
from .agent_resources import register_agent_resources


def register_all_resources(mcp: FastMCP):
    """
    Register all MCP resources
    
    Args:
        mcp: FastMCP server instance
    """
    register_conversation_resources(mcp)
    register_agent_resources(mcp)


__all__ = [
    "register_all_resources",
    "register_conversation_resources",
    "register_agent_resources"
]
