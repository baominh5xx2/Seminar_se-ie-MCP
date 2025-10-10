"""
MCP Resources - Agent Resources
"""
from fastmcp import FastMCP
from ..core.client import BackendClient
import json


def register_agent_resources(mcp: FastMCP):
    """Register agent-related resources"""
    
    @mcp.resource("agent://status")
    async def get_agent_status_resource() -> str:
        """
        Get agent status as a resource.
        
        Returns:
            Formatted agent status
        """
        async with BackendClient() as client:
            result = await client.get_agent_status()
            
            lines = [
                "# Agent Status\n",
                f"**Status:** {result.get('status')}",
                f"**Type:** {result.get('agent_type')}",
                f"**Model:** {result.get('model')}",
                "\n## Capabilities:",
            ]
            
            for cap in result.get("capabilities", []):
                lines.append(f"- {cap}")
            
            return "\n".join(lines)
    
    @mcp.resource("agent://info")
    async def get_agent_info_resource() -> str:
        """
        Get detailed agent information as a resource.
        
        Returns:
            Formatted agent information
        """
        async with BackendClient() as client:
            result = await client.get_agent_info()
            
            lines = [
                f"# {result.get('name')}\n",
                f"**Version:** {result.get('version')}",
                f"**Description:** {result.get('description')}",
                "\n## Features:",
            ]
            
            for feature in result.get("features", []):
                lines.append(f"- {feature}")
            
            lines.append("\n## Workflow Steps:")
            for step in result.get("workflow_steps", []):
                lines.append(f"\n### {step.get('step')}")
                lines.append(f"{step.get('description')}")
            
            return "\n".join(lines)
