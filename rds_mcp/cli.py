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
    parser = argparse.ArgumentParser(description="RDS MCP Server")
    parser.add_argument("--host", default="localhost", type=str, help="Custom host for the server")
    parser.add_argument("--port", default=8000, type=int, help="Custom port for the server")
    parser.add_argument("--model", default="openai/gpt-4o-mini", type=str, help="OpenAI model to use")
    parser.add_argument("--openai-api-key", type=str, help="OpenAI API key")
    parser.add_argument("--access-key", type=str, help="AWS Access Key")
    parser.add_argument("--secret-access-key", type=str, help="AWS Secret Access Key")
    parser.add_argument("--region", default="us-east-1", type=str, help="AWS Region")

    args = parser.parse_args()

    # Get OpenAI API key from args or environment
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or use --openai-api-key")
        return 1

    # Get model from args or environment
    model = args.model or os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

    # Get AWS credentials from args or environment
    aws_access_key = args.access_key or os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = args.secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = args.region or os.getenv("AWS_REGION", "us-east-1")

    if not aws_access_key or not aws_secret_key:
        logger.error("AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        logger.info("Looking for .env file in: " + os.path.abspath(".env"))
        return 1

    try:
        # Create AWS client manager
        aws_client_manager = AWSClientManager(
            RDSClientConfig(
                access_key=aws_access_key,
                secret_access_key=aws_secret_key,
                region_name=aws_region
            )
        )

        # Create server instance
        server = RDSCMPServer(
            model=model,
            openai_api_key=openai_api_key,
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