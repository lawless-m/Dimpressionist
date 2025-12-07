#!/usr/bin/env python3
"""
Entry point for Dimpressionist web server.
"""

import argparse
import uvicorn

from src.utils.config import get_config


def main():
    parser = argparse.ArgumentParser(
        description="Dimpressionist Web Server"
    )
    parser.add_argument(
        '--host', '-H',
        default=None,
        help='Host to bind to (default: from config or 127.0.0.1)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=None,
        help='Port to bind to (default: from config or 8000)'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development'
    )

    args = parser.parse_args()
    config = get_config()

    host = args.host or config.host
    port = args.port or config.port

    print(f"Starting Dimpressionist server at http://{host}:{port}")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        "src.web.api:app",
        host=host,
        port=port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
