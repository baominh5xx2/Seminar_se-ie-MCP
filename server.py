"""
AI Assistant MCP Server
Professional FastMCP implementation with modular architecture
"""
import os
from fastmcp import FastMCP
from fastapi import FastAPI
from fastapi.responses import JSONResponse
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

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.SERVER_NAME,
    version=settings.SERVER_VERSION,
    dependencies=["httpx", "pydantic", "pydantic-settings"]
)

# Register all components
logger.info("Registering MCP tools...")
register_all_tools(mcp)

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


def main():
    """Main entry point for the MCP server"""
    # Check if running on Render (has PORT env var)
    port = os.getenv("PORT")
    
    if port:
        # Running on Render - use HTTP mode
        logger.info(f"🚀 Starting {settings.SERVER_NAME} in HTTP mode (Render)...")
        logger.info(f"Backend API: {settings.BACKEND_API_URL}")
        logger.info(f"Port: {port}")
        
        # Run with uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(port),
            log_level=settings.LOG_LEVEL.lower()
        )
    else:
        # Running locally - use stdio mode (standard MCP)
        logger.info(f"🚀 Starting {settings.SERVER_NAME} in stdio mode (local)...")
        logger.info(f"Backend API: {settings.BACKEND_API_URL}")
        
        # Run the MCP server in stdio mode
        mcp.run()


if __name__ == "__main__":
    main()
