"""
MCP Tools - Chat Tools
"""
from fastmcp import FastMCP
from typing import Optional, Dict, Any
from ..core.client import BackendClient


def register_chat_tools(mcp: FastMCP):
    """Register chat-related tools"""
    
    @mcp.tool()
    async def chat_with_agent(
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat with the AI assistant agent.
        
        Args:
            message: The message to send to the agent
            conversation_id: Optional conversation ID to continue a conversation
            user_id: Optional user ID for tracking
            
        Returns:
            Agent's response with conversation details
        """
        async with BackendClient() as client:
            result = await client.chat(
                message=message,
                conversation_id=conversation_id,
                user_id=user_id
            )
            return {
                "success": True,
                "conversation_id": result.get("conversation_id"),
                "response": result.get("message"),
                "metadata": result.get("metadata"),
                "timestamp": result.get("timestamp")
            }
    
    @mcp.tool()
    async def get_conversation_history(
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve the history of a conversation.
        
        Args:
            conversation_id: The ID of the conversation to retrieve
            
        Returns:
            Conversation history with all messages
        """
        async with BackendClient() as client:
            result = await client.get_conversation(conversation_id)
            return {
                "success": True,
                "conversation_id": result.get("conversation_id"),
                "messages": result.get("messages"),
                "summary": result.get("summary")
            }
    
    @mcp.tool()
    async def delete_conversation(
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Delete a conversation and all its history.
        
        Args:
            conversation_id: The ID of the conversation to delete
            
        Returns:
            Deletion confirmation
        """
        async with BackendClient() as client:
            await client.delete_conversation(conversation_id)
            return {
                "success": True,
                "message": f"Conversation {conversation_id} deleted successfully"
            }
