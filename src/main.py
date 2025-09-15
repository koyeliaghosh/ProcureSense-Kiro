"""
Main entry point for ProcureSense API server.
"""

import uvicorn
from src.api.app import create_app
from src.config.settings import get_settings


def main():
    """Run the ProcureSense API server."""
    settings = get_settings()
    app = create_app()
    
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level="info",
        reload=False  # Set to True for development
    )


if __name__ == "__main__":
    main()