"""
AI Assistant MCP Server
Professional FastMCP implementation with modular architecture
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
ROOT_DIR = Path(__file__).parent
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from fastmcp import FastMCP
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from mcp_server.core.config import settings
from mcp_server.tools import register_all_tools
from mcp_server.resources import register_all_resources
from mcp_server.prompts import register_all_prompts
from mcp_server.utils import setup_logging

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
