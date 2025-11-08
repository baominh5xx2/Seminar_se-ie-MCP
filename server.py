"""
AI Assistant MCP Server
Professional FastMCP implementation with modular architecture
"""
import os
import asyncio
from fastmcp import FastMCP
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.mcp_server.core.config import settings
from src.mcp_server.tools import register_all_tools
from src.mcp_server.resources import register_all_resources
from src.mcp_server.prompts import register_all_prompts
from src.mcp_server.utils import setup_logging

# Setup logging
logger = setup_logging(settings.LOG_LEVEL)

# Initialize FastAPI app for HTTP endpoints
app = FastAPI(
    title=settings.SERVER_NAME,
    version=settings.SERVER_VERSION,
    description="AI Assistant MCP Server - HTTP Wrapper"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.SERVER_NAME,
    version=settings.SERVER_VERSION
)

# Register all components
logger.info("Registering MCP tools...")
register_all_tools(mcp)

# Debug: Log registered tools immediately after registration
logger.info("=" * 60)
logger.info("DEBUG: Checking registered tools...")
logger.info("=" * 60)

try:
    # Check _tools attribute
    if hasattr(mcp, '_tools'):
        tools_dict = mcp._tools
        logger.info(f"✅ Found _tools attribute: {type(tools_dict)}")
        if isinstance(tools_dict, dict):
            logger.info(f"✅ _tools dict has {len(tools_dict)} keys: {list(tools_dict.keys())}")
        else:
            logger.warning(f"⚠️ _tools is not a dict: {type(tools_dict)}")
    else:
        logger.warning("⚠️ No _tools attribute found")
    
    # Check _list_tools (FastMCP private method - returns coroutine)
    if hasattr(mcp, '_list_tools'):
        try:
            # _list_tools() returns a coroutine, need to run it in sync context
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            tools_list = loop.run_until_complete(mcp._list_tools())
            logger.info(f"✅ _list_tools() returned: {type(tools_list)}")
            if isinstance(tools_list, (list, tuple)):
                logger.info(f"✅ _list_tools() has {len(tools_list)} items")
                tool_names = []
                for i, tool in enumerate(tools_list):
                    tool_name = None
                    if isinstance(tool, dict):
                        tool_name = tool.get('name', f'dict_{i}')
                    elif hasattr(tool, 'name'):
                        tool_name = tool.name
                    elif hasattr(tool, '__name__'):
                        tool_name = tool.__name__
                    else:
                        tool_name = str(tool)[:50]
                    tool_names.append(tool_name)
                    logger.debug(f"  Tool {i}: {tool_name} (type: {type(tool)})")
                logger.info(f"✅ Tool names from _list_tools(): {tool_names}")
            else:
                logger.warning(f"⚠️ _list_tools() returned non-list: {type(tools_list)}")
        except Exception as e:
            logger.error(f"❌ Error calling _list_tools(): {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.warning("⚠️ No _list_tools method found")
    
    # Check _tool_registry
    if hasattr(mcp, '_tool_registry'):
        registry = mcp._tool_registry
        logger.info(f"✅ Found _tool_registry: {type(registry)}")
        if isinstance(registry, dict):
            logger.info(f"✅ _tool_registry has {len(registry)} keys: {list(registry.keys())}")
    else:
        logger.debug("ℹ️ No _tool_registry attribute found")
    
    # List all non-private attributes
    all_attrs = [attr for attr in dir(mcp) if not attr.startswith('__')]
    logger.info(f"ℹ️ FastMCP attributes (first 20): {all_attrs[:20]}")
    
except Exception as e:
    logger.error(f"❌ Error checking registered tools: {e}")
    import traceback
    logger.error(traceback.format_exc())

logger.info("=" * 60)

logger.info("Registering MCP resources...")
register_all_resources(mcp)

logger.info("Registering MCP prompts...")
register_all_prompts(mcp)

logger.info(f"✅ {settings.SERVER_NAME} v{settings.SERVER_VERSION} initialized successfully")

# HTTP Endpoints for Render
@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse({
        "name": settings.SERVER_NAME,
        "version": settings.SERVER_VERSION,
        "status": "running",
        "message": "MCP Server is running. Use MCP protocol to interact."
    })

@app.get("/health")
@app.get("/healthz")
async def health_check():
    """Health check endpoint for Render"""
    try:
        return JSONResponse({
            "status": "healthy",
            "server": settings.SERVER_NAME,
            "version": settings.SERVER_VERSION,
            "backend_api": settings.BACKEND_API_URL
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/info")
async def server_info():
    """Get server information"""
    return JSONResponse({
        "server_name": settings.SERVER_NAME,
        "version": settings.SERVER_VERSION,
        "backend_api": settings.BACKEND_API_URL,
        "log_level": settings.LOG_LEVEL
    })

@app.get("/tools")
async def list_tools():
    """
    List all available MCP tools
    
    Returns:
        List of available tools with their descriptions
    """
    try:
        available_tools = []
        
        # Try to get tools from FastMCP
        if hasattr(mcp, '_list_tools'):
            try:
                tools_list = await mcp._list_tools()
                if isinstance(tools_list, (list, tuple)):
                    for tool in tools_list:
                        tool_info = {}
                        if isinstance(tool, dict):
                            tool_info = tool
                        elif hasattr(tool, 'name'):
                            tool_info = {
                                "name": tool.name,
                                "description": getattr(tool, 'description', ''),
                                "parameters": getattr(tool, 'inputSchema', {})
                            }
                        if tool_info:
                            available_tools.append(tool_info)
            except Exception as e:
                logger.warning(f"Error listing tools: {e}")
        
        # Fallback: Check _tools dict
        if not available_tools and hasattr(mcp, '_tools'):
            tools_dict = mcp._tools
            if isinstance(tools_dict, dict):
                for tool_name in tools_dict.keys():
                    available_tools.append({
                        "name": tool_name,
                        "description": f"Tool: {tool_name}"
                    })
        
        return JSONResponse({
            "tools": available_tools,
            "count": len(available_tools)
        })
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request = None):
    """
    HTTP wrapper to call MCP tools
    
    Usage: POST /tools/create_booking with JSON body
    Example:
        POST /tools/create_booking
        {
            "user_phone": "0123456789",
            "package_id": "package_123",
            "number_of_people": 2,
            "travel_date": "2024-12-25",
            "special_requests": "Window seat preferred"
        }
    """
    try:
        from fastapi import Request
        
        # Get params from request body
        params = {}
        if request:
            try:
                body = await request.json()
                params = body
            except:
                params = {}
        
        logger.info(f"📞 HTTP Tool Call: {tool_name} with params: {params}")
        
        # Debug: Log FastMCP attributes
        logger.debug(f"🔍 FastMCP attributes: {[attr for attr in dir(mcp) if not attr.startswith('__')]}")
        
        # FastMCP stores tools in a registry - try to access it
        tool_func = None
        
        # Method 1: Try to access via FastMCP's internal registry (_tools dict)
        if hasattr(mcp, '_tools'):
            tools_dict = mcp._tools
            logger.debug(f"🔍 _tools type: {type(tools_dict)}, keys: {list(tools_dict.keys()) if isinstance(tools_dict, dict) else 'Not a dict'}")
            if isinstance(tools_dict, dict) and tool_name in tools_dict:
                tool_func = tools_dict[tool_name]
                logger.info(f"✅ Found tool '{tool_name}' via _tools dict")
        
        # Method 2: Use FastMCP's _mcp_call_tool (FastMCP internal method)
        if tool_func is None and hasattr(mcp, '_mcp_call_tool'):
            # FastMCP's internal _mcp_call_tool method - check if tool exists first
            try:
                # Check if tool exists via _list_tools (async)
                tools_list = await mcp._list_tools()
                tool_exists = False
                if isinstance(tools_list, (list, tuple)):
                    for tool in tools_list:
                        tool_name_to_check = None
                        if isinstance(tool, dict):
                            tool_name_to_check = tool.get('name')
                        elif hasattr(tool, 'name'):
                            tool_name_to_check = tool.name
                        
                        if tool_name_to_check == tool_name:
                            tool_exists = True
                            break
                
                if tool_exists:
                    logger.info(f"✅ Found tool '{tool_name}' in _list_tools(), using _mcp_call_tool()")
                    # Use FastMCP's internal _mcp_call_tool method
                    try:
                        # _mcp_call_tool takes tool name and arguments dict
                        result = await mcp._mcp_call_tool(tool_name, params)
                        logger.info(f"✅ Tool '{tool_name}' executed successfully via _mcp_call_tool()")
                        
                        # FastMCP _mcp_call_tool returns a tuple: (content_list, metadata_dict)
                        # content_list contains TextContent objects with .text attribute
                        # metadata_dict may contain the actual result (for tools that return dict)
                        if isinstance(result, tuple) and len(result) >= 1:
                            content_list = result[0]
                            metadata = result[1] if len(result) > 1 else {}
                            
                            logger.debug(f"🔍 FastMCP returned tuple: content_list type={type(content_list)}, metadata type={type(metadata)}")
                            
                            # Priority 1: Check metadata dict first (some tools return result in metadata)
                            if isinstance(metadata, dict) and len(metadata) > 0:
                                # Check if metadata has the actual result
                                if "found" in metadata or "packages" in metadata:
                                    logger.debug(f"✅ Found result in metadata dict: keys={list(metadata.keys())}")
                                    result = metadata
                                elif "content" in metadata and isinstance(metadata["content"], dict):
                                    # Result might be in metadata.content
                                    if "found" in metadata["content"] or "packages" in metadata["content"]:
                                        logger.debug(f"✅ Found result in metadata.content")
                                        result = metadata["content"]
                            
                            # Priority 2: Extract from TextContent.text (if not found in metadata)
                            if not isinstance(result, dict) or ("found" not in result and "packages" not in result):
                                if isinstance(content_list, (list, tuple)) and len(content_list) > 0:
                                    first_content = content_list[0]
                                    if hasattr(first_content, 'text'):
                                        text_content = first_content.text
                                        logger.debug(f"🔍 Extracting from TextContent.text: {text_content[:200] if isinstance(text_content, str) else type(text_content)}")
                                        
                                        # Try to parse as JSON
                                        try:
                                            import json
                                            parsed = json.loads(text_content)
                                            if isinstance(parsed, dict):
                                                result = parsed
                                                logger.debug(f"✅ Parsed TextContent.text as JSON: {type(result)}")
                                            else:
                                                result = {"content": text_content}
                                        except (json.JSONDecodeError, TypeError) as e:
                                            logger.debug(f"🔍 TextContent.text is not JSON: {e}")
                                            result = {"content": text_content}
                                    else:
                                        logger.warning(f"⚠️ First content has no 'text' attribute: {type(first_content)}")
                                        result = metadata if isinstance(metadata, dict) else {"content": str(content_list)}
                                else:
                                    logger.warning(f"⚠️ Content list is empty, using metadata")
                                    result = metadata if isinstance(metadata, dict) else {}
                        elif hasattr(result, 'text'):
                            # Direct TextContent object - try to parse text as JSON first
                            try:
                                import json
                                parsed = json.loads(result.text)
                                result = parsed
                                logger.debug(f"🔍 Parsed TextContent.text as JSON: {type(result)}")
                            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                                logger.debug(f"🔍 TextContent.text is not JSON, type: {type(result.text)}, value: {str(result.text)[:200]}")
                                result = {"content": result.text}
                        elif hasattr(result, 'content'):
                            # Has content attribute
                            if isinstance(result.content, dict):
                                result = result.content
                            elif isinstance(result.content, str):
                                try:
                                    import json
                                    result = json.loads(result.content)
                                except json.JSONDecodeError:
                                    result = {"content": result.content}
                            else:
                                result = {"content": result.content}
                        elif isinstance(result, dict):
                            # Already a dict, use as is
                            pass
                        else:
                            # Convert other types to string
                            logger.warning(f"⚠️ Result is not dict or tuple, type: {type(result)}, converting to string")
                            result = {"content": str(result)}
                        
                        logger.debug(f"🔍 Final result type: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                        
                        # Debug: Log result structure for search_tour_packages
                        if tool_name == "search_tour_packages" and isinstance(result, dict):
                            logger.debug(f"🔍 search_tour_packages result structure: {result}")
                            logger.debug(f"🔍 Has 'found': {'found' in result}, Has 'packages': {'packages' in result}")
                            if "packages" in result:
                                logger.debug(f"🔍 Packages count: {len(result.get('packages', []))}")
                        
                        return JSONResponse(result)
                    except Exception as e:
                        logger.error(f"❌ Error calling tool via _mcp_call_tool(): {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        return JSONResponse(
                            status_code=500,
                            content={"error": str(e), "tool": tool_name}
                        )
                else:
                    logger.debug(f"⚠️ Tool '{tool_name}' not found in _list_tools()")
            except Exception as e:
                logger.warning(f"⚠️ Error checking _list_tools() or calling tool: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        # Method 3: Try _tool_registry (alternative FastMCP storage)
        if tool_func is None and hasattr(mcp, '_tool_registry'):
            registry = mcp._tool_registry
            logger.debug(f"🔍 _tool_registry type: {type(registry)}, keys: {list(registry.keys()) if isinstance(registry, dict) else 'Not a dict'}")
            if isinstance(registry, dict) and tool_name in registry:
                tool_func = registry[tool_name]
                logger.info(f"✅ Found tool '{tool_name}' via _tool_registry")
        
        # Method 4: Try to get tool directly as attribute
        if tool_func is None:
            try:
                if hasattr(mcp, tool_name):
                    attr = getattr(mcp, tool_name)
                    if callable(attr):
                        tool_func = attr
                        logger.info(f"✅ Found tool '{tool_name}' as attribute")
            except Exception as e:
                logger.debug(f"⚠️ Could not get tool as attribute: {e}")
        
        if tool_func is None:
            # List ALL available tools for debugging
            available_tools = []
            try:
                # Try _tools
                if hasattr(mcp, '_tools'):
                    tools_dict = mcp._tools
                    if isinstance(tools_dict, dict):
                        available_tools.extend(list(tools_dict.keys()))
                
                # Try _list_tools() (async, needs await)
                if hasattr(mcp, '_list_tools'):
                    try:
                        tools_list = await mcp._list_tools()
                        if isinstance(tools_list, (list, tuple)):
                            for tool in tools_list:
                                tool_name = None
                                if isinstance(tool, dict):
                                    tool_name = tool.get('name')
                                elif hasattr(tool, 'name'):
                                    tool_name = tool.name
                                
                                if tool_name and tool_name not in available_tools:
                                    available_tools.append(tool_name)
                    except Exception as e:
                        logger.debug(f"⚠️ Error calling _list_tools(): {e}")
                
                # Try _tool_registry
                if hasattr(mcp, '_tool_registry'):
                    registry = mcp._tool_registry
                    if isinstance(registry, dict):
                        for key in registry.keys():
                            if key not in available_tools:
                                available_tools.append(key)
            except Exception as e:
                logger.error(f"❌ Error listing tools: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            logger.error(f"❌ Tool '{tool_name}' not found. Available tools: {available_tools}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": f"Tool {tool_name} not found",
                    "available_tools": available_tools,
                    "mcp_attributes": [attr for attr in dir(mcp) if not attr.startswith('__')][:20]
                }
            )
        
        # Call the tool (async function)
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**params)
        else:
            result = tool_func(**params)
        
        logger.info(f"✅ Tool {tool_name} executed successfully")
        
        # Return result (may already be a dict with success/error)
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"❌ Tool {tool_name} error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "tool": tool_name}
        )

@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for MCP protocol"""
    async def event_generator():
        # Send initial connection event
        yield "data: {'type': 'connection', 'status': 'connected'}\n\n"
        
        # Keep connection alive
        while True:
            # Send heartbeat every 30 seconds
            instance_id = os.getenv("RENDER_INSTANCE_ID", "local")
            yield f"data: {{'type': 'heartbeat', 'timestamp': '{instance_id}'}}\n\n"
            await asyncio.sleep(30)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def main():
    """Main entry point for the MCP server"""
    # Check if running on Render (has PORT env var) or force HTTP mode
    port = os.getenv("PORT")
    
    # Always use HTTP mode (both local and Render)
    if port:
        # Running on Render - use provided port
        logger.info(f"🚀 Starting {settings.SERVER_NAME} in HTTP mode (Render)...")
        logger.info(f"Backend API: {settings.BACKEND_API_URL}")
        logger.info(f"Port: {port}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(port),
            log_level=settings.LOG_LEVEL.lower()
        )
    else:
        # Running locally - use HTTP mode on port 8001
        logger.info(f"🚀 Starting {settings.SERVER_NAME} in HTTP mode (local)...")
        logger.info(f"Backend API: {settings.BACKEND_API_URL}")
        logger.info(f"Port: 8001")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level=settings.LOG_LEVEL.lower()
        )


if __name__ == "__main__":
    main()