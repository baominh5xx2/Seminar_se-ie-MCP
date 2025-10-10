"""
MCP Resources - Conversation Resources
"""
from fastmcp import FastMCP
from typing import Dict, Any
from ..core.client import BackendClient


def register_conversation_resources(mcp: FastMCP):
    """Register conversation-related resources"""
    
    @mcp.resource("conversation://{conversation_id}")
    async def get_conversation_resource(conversation_id: str) -> str:
        """
        Get conversation as a resource.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Formatted conversation text
        """
        async with BackendClient() as client:
            result = await client.get_conversation(conversation_id)
            
            messages = result.get("messages", [])
            
            # Format conversation as text
            lines = [f"# Conversation: {conversation_id}\n"]
            
            for msg in messages:
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                lines.append(f"\n## [{role}] {timestamp}")
                lines.append(content)
                lines.append("\n" + "-" * 80)
            
            return "\n".join(lines)
