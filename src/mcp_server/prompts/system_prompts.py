"""
MCP Prompts - System Prompts
"""
from fastmcp import FastMCP


def register_system_prompts(mcp: FastMCP):
    """Register system prompts for common tasks"""
    
    @mcp.prompt()
    async def summarize_conversation(conversation_id: str) -> str:
        """
        Generate a prompt to summarize a conversation.
        
        Args:
            conversation_id: The conversation to summarize
            
        Returns:
            Prompt for summarization
        """
        return f"""Please summarize the conversation with ID: {conversation_id}

Use the get_conversation_history tool to retrieve the conversation, then provide:
1. A brief overview of the main topics discussed
2. Key points and decisions made
3. Any action items or follow-ups needed
4. Overall sentiment and outcome

Format your summary in a clear, structured manner."""
    
    @mcp.prompt()
    async def analyze_conversation_pattern(conversation_id: str) -> str:
        """
        Generate a prompt to analyze conversation patterns.
        
        Args:
            conversation_id: The conversation to analyze
            
        Returns:
            Prompt for pattern analysis
        """
        return f"""Analyze the conversation pattern for conversation ID: {conversation_id}

Use the get_conversation_history tool to retrieve the conversation, then analyze:
1. Communication style and tone
2. Question types and complexity
3. Response effectiveness
4. User engagement level
5. Topic transitions and flow

Provide insights and recommendations for improving future interactions."""
    
    @mcp.prompt()
    async def create_follow_up_questions(last_message: str) -> str:
        """
        Generate follow-up questions based on the last message.
        
        Args:
            last_message: The last message in the conversation
            
        Returns:
            Prompt for generating follow-up questions
        """
        return f"""Based on this message: "{last_message}"

Generate 3-5 relevant follow-up questions that would help:
1. Clarify any ambiguous points
2. Deepen understanding of the topic
3. Explore related aspects
4. Guide the conversation productively

Format the questions clearly and make them open-ended where appropriate."""
