"""CLI for RDS MCP server."""
import os
import anyio
import argparse
import logging
from typing import Optional
from dotenv import load_dotenv
from rds_mcp.server import RDSCMPServer
from rds_mcp.client import RDSClientConfig, AWSClientManager

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger('rds_mcp')

async def perform_async_initialization(server_obj: RDSCMPServer) -> None:
    """Initialize AWS clients asynchronously."""
    try:
        # AWS clients are now initialized by AWSClientManager in the constructor
        # No need for explicit initialization
        pass
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")
        return 1

def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="ECS MCP Server")
    parser.add_argument("--host", default="localhost", type=str, help="Custom host for the server")
    parser.add_argument("--port", default=8000, type=int, help="Custom port for the server")
    parser.add_argument("--model", default="openai/gpt-4o-mini", type=str, help="OpenAI model to use")
    parser.add_argument("--openai-api-key", type=str, required=True, help="OpenAI API key")
    parser.add_argument("--access-key", type=str, help="AWS Access Key (optional when using IAM roles)")
    parser.add_argument("--secret-access-key", type=str, help="AWS Secret Access Key (optional when using IAM roles)")
    parser.add_argument("--region", default="us-east-1", type=str, required=True, help="AWS Region")

    args = parser.parse_args()

    if not args.openai_api_key or not args.region:
        logger.error("Missing required arguments. Please provide openai-api-key and region.")
        return 1

    # Check if both or neither AWS credentials are provided
    has_access_key = bool(args.access_key)
    has_secret_key = bool(args.secret_access_key)
    
    if has_access_key != has_secret_key:
        logger.error("Both access-key and secret-access-key must be provided together, or neither for IAM role usage.")
        return 1

    try:
        # Create AWS client manager
        aws_client_manager = AWSClientManager(
            RDSClientConfig(
                access_key=args.access_key,
                secret_access_key=args.secret_access_key,
                region_name=args.region
            )
        )

        # Create server instance
        server = RDSCMPServer(
            model=args.model,
            openai_api_key=args.openai_api_key,
            aws_client_manager=aws_client_manager
        )

        anyio.run(perform_async_initialization, server)
        server.run_mcp_blocking()
        return 0

    except Exception as e:
        logger.error(f"Error running server: {e}")
        return 1

if __name__ == "__main__":
    main()