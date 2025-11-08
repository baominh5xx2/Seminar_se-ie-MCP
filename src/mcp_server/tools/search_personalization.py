"""
MCP Tools - Search Personalization
Search episodes using Graphiti for personalization
"""
from fastmcp import FastMCP
from typing import Optional, Dict, Any
import logging

from src.mcp_server.core.graphiti import get_graphiti_service

logger = logging.getLogger(__name__)


def register_search_personalization_tools(mcp: FastMCP):
    """Register search personalization tools"""
    
    @mcp.tool()
    async def search_episodes(
        query_text: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for episodes in the knowledge graph using hybrid search.
        
        This tool searches through conversation history and user interactions
        stored in the graph database to find relevant episodes based on the query.
        
        Args:
            query_text (str): Search query text. Example: "Đà Lạt tour", "beach destinations"
            user_id (str, optional): User ID for personalized search. Example: "user_123"
            limit (int, optional): Maximum number of results to return. Default: 5. Example: 5
        
        Returns:
            Dict with:
            - found (int): Number of episodes found
            - episodes (list): List of episode dictionaries with:
                - episode_id (str): Unique episode identifier
                - name (str): Episode name
                - episode_body (str): Episode content/body
                - source_description (str): Source description
                - created_at (str): Creation timestamp
                - user_id (str): Associated user ID
                - search_method (str): Search method used
        
        Example response:
        {
            "found": 3,
            "episodes": [
                {
                    "episode_id": "ep_abc123",
                    "name": "episode_abc12345",
                    "episode_body": "User: Tôi muốn đi Đà Lạt...",
                    "source_description": "Chat conversation",
                    "created_at": "2024-01-01T00:00:00",
                    "user_id": "user_123",
                    "search_method": "episode_fetch"
                }
            ]
        }
        """
        try:
            service = get_graphiti_service()
            episodes = await service.search_episodes(
                query_text=query_text,
                user_id=user_id,
                limit=limit
            )
            
            if episodes:
                return {
                    "found": len(episodes),
                    "episodes": episodes
                }
            else:
                return {
                    "found": 0,
                    "episodes": [],
                    "message": f"No episodes found for query: '{query_text}'"
                }
                
        except Exception as e:
            logger.error(f"❌ Error in search_episodes tool: {str(e)}")
            return {
                "found": 0,
                "episodes": [],
                "error": str(e),
                "message": f"Error searching episodes: {str(e)}"
            }

