"""
MCP Tools - Agent Tools
"""
from fastmcp import FastMCP
from typing import Dict, Any
from ..core.client import BackendClient


def register_agent_tools(mcp: FastMCP):
    """Register agent management tools"""
    
    @mcp.tool()
    async def get_agent_status() -> Dict[str, Any]:
        """
        Get the current status of the AI agent.
        
        Returns:
            Agent status including type, model, and capabilities
        """
        async with BackendClient() as client:
            result = await client.get_agent_status()
            return {
                "success": True,
                "status": result.get("status"),
                "agent_type": result.get("agent_type"),
                "model": result.get("model"),
                "capabilities": result.get("capabilities")
            }
    
    @mcp.tool()
    async def get_agent_info() -> Dict[str, Any]:
        """
        Get detailed information about the AI agent.
        
        Returns:
            Detailed agent information including features and workflow
        """
        async with BackendClient() as client:
            result = await client.get_agent_info()
            return {
                "success": True,
                "name": result.get("name"),
                "version": result.get("version"),
                "description": result.get("description"),
                "features": result.get("features"),
                "workflow_steps": result.get("workflow_steps")
            }
    
    @mcp.tool()
    async def check_backend_health() -> Dict[str, Any]:
        """
        Check if the backend API is healthy and responding.
        
        Returns:
            Backend health status
        """
        async with BackendClient() as client:
            result = await client.health_check()
            return {
                "success": True,
                "status": result.get("status"),
                "service": result.get("service", "Backend API"),
                "version": result.get("version")
            }
