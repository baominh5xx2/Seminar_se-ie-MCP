"""
MCP Prompts - Agent Prompts
"""
from fastmcp import FastMCP


def register_agent_prompts(mcp: FastMCP):
    """Register prompts for agent interaction"""
    
    @mcp.prompt()
    async def chat_with_context(
        message: str,
        context: str = ""
    ) -> str:
        """
        Generate a contextual chat prompt.
        
        Args:
            message: User's message
            context: Additional context
            
        Returns:
            Enhanced prompt with context
        """
        base_prompt = f"User message: {message}"
        
        if context:
            base_prompt += f"\n\nAdditional context:\n{context}"
        
        base_prompt += """

Please use the chat_with_agent tool to respond to this message.
Consider the context provided and ensure your response is:
- Relevant and accurate
- Clear and concise
- Helpful and actionable
- Contextually appropriate"""
        
        return base_prompt
    
    @mcp.prompt()
    async def debug_agent_response(
        message: str,
        expected_response: str,
        actual_response: str
    ) -> str:
        """
        Generate a prompt for debugging agent responses.
        
        Args:
            message: Original message
            expected_response: What was expected
            actual_response: What was received
            
        Returns:
            Debugging analysis prompt
        """
        return f"""Analyze this agent interaction for debugging:

**Original Message:**
{message}

**Expected Response:**
{expected_response}

**Actual Response:**
{actual_response}

Please:
1. Compare the expected vs actual responses
2. Identify any discrepancies or issues
3. Suggest potential causes
4. Recommend improvements to the agent configuration or prompts
5. Check if the agent_info shows any relevant workflow issues"""
