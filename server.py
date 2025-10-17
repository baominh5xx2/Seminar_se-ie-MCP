"""
AI Assistant MCP Server
Professional FastMCP implementation with modular architecture
"""
import os
import asyncio
from fastmcp import FastMCP
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.mcp_server.core.config import settings
from src.mcp_server.utils import setup_logging

# Import individual tool registrations
from src.mcp_server.tools.booking_tools import register_booking_tools
from src.mcp_server.tools.flight_tools import register_flight_tools
from src.mcp_server.tools.weather_tools import register_weather_tools
from src.mcp_server.resources import register_all_resources
from src.mcp_server.prompts import register_all_prompts

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
    version=settings.SERVER_VERSION,
    dependencies=["httpx", "pydantic", "pydantic-settings"]
)

# ============================================================================
# REGISTER TOOLS - Comment out tools you don't want to use
# ============================================================================
logger.info("Registering MCP tools...")

# Booking Tools (Tour search, booking management)
register_booking_tools(mcp)

# Flight Tools (Flight search) - Uncomment to enable
register_flight_tools(mcp)

# Weather Tools (Weather forecast) - Uncomment to enable
register_weather_tools(mcp)


# ============================================================================
# REGISTER RESOURCES & PROMPTS
# ============================================================================
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
