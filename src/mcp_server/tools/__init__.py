"""Tools package - Register all MCP tools"""
from fastmcp import FastMCP
from .chat_tools import register_chat_tools
from .agent_tools import register_agent_tools


def register_all_tools(mcp: FastMCP):
    """
    Register all MCP tools
    
    Args:
        mcp: FastMCP server instance
    """
    register_chat_tools(mcp)
    register_agent_tools(mcp)


__all__ = [
    "register_all_tools",
    "register_chat_tools",
    "register_agent_tools"
]
