# RDS MCP Server

A Model Context Protocol (MCP) server for monitoring and analyzing Amazon RDS(MySQL, PostgreSQL) instances information, metrics and slowquery logs.

## Installation

Install directly from GitHub using pipx:

```bash
# Install
pipx install git+https://github.com/neoai-agent/rds-mcp.git

# Or run without installation
pipx run git+https://github.com/neoai-agent/rds-mcp.git
```

## Quick Start

### Authentication Options

The server supports multiple AWS authentication methods:

#### Option 1: IAM Roles (Recommended for EC2/ECS)
When running on AWS infrastructure with IAM roles attached, you can omit AWS credentials:

```bash
rds-mcp --openai-api-key "YOUR_OPENAI_API_KEY" --region "YOUR_AWS_REGION"
```

#### Option 2: AWS Access Keys
For local development or when IAM roles are not available:

```bash
rds-mcp --access-key "YOUR_AWS_ACCESS_KEY" --secret-access-key "YOUR_AWS_SECRET_KEY" --region "YOUR_AWS_REGION" --openai-api-key "YOUR_OPENAI_API_KEY"
```

#### Option 3: Environment Variables
You can also set AWS credentials via environment variables:
```bash
rds-mcp --access-key "YOUR_AWS_ACCESS_KEY" --secret-access-key "YOUR_AWS_SECRET_KEY" --region "YOUR_AWS_REGION" --openai_api_key "YOUR_OPENAI_API_KEY"
```

**Note**: When using IAM roles, the server will automatically use the default AWS credential chain, which includes IAM roles, environment variables, and AWS credentials file.

## Available Tools

The server provides the following tools for RDS instance management and monitoring:

1. Get RDS instance details:
```python
await get_db_info(
    database_name="your-db-instance",
    region="your-aws-region"
)
```

2. Get database metrics:
```python
await get_database_metrics(
    database_name="your-db-instance",
    time_range_minutes=30
)
```

3. Get slow queries:
```python
await get_database_queries(
    database_name="your-db-instance",
    time_range_minutes=30
)
```

4. Get instance performance metrics:
```python
await get_instance_performance_metrics(
    database_name="your-db-instance",
    time_range_minutes=30
)
```

## Development

For development setup:
```bash
git clone https://github.com/neoai-agent/rds-mcp.git
cd rds-mcp
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## License

MIT License - See [LICENSE](LICENSE) file for details 
