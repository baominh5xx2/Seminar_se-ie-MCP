"""Prompts package - Register all MCP prompts"""
from fastmcp import FastMCP
from .system_prompts import register_system_prompts
from .agent_prompts import register_agent_prompts


def register_all_prompts(mcp: FastMCP):
    """
    Register all MCP prompts
    
    Args:
        mcp: FastMCP server instance
    """
    register_system_prompts(mcp)
    register_agent_prompts(mcp)


__all__ = [
    "register_all_prompts",
    "register_system_prompts",
    "register_agent_prompts"
]
