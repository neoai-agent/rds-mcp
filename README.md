# RDS MCP Server

A command-line tool for monitoring and managing Amazon RDS instances using MCP (Model Control Protocol).

## Installation

Install directly from GitHub using pipx:

```bash
# Install
pipx install git+https://github.com/yourusername/rds-mcp.git

# Or run without installation
pipx run git+https://github.com/yourusername/rds-mcp.git
```

## Quick Start

1. Run the server:
```bash
rds-mcp --access-key "YOUR_AWS_ACCESS_KEY" --secret-access-key "YOUR_AWS_SECRET_KEY" --region "YOUR_AWS_REGION" --openai_api_key "YOUR_OPENAI_API_KEY"
```

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

5. Get database connections:
```python
await get_database_connections(
    database_name="your-db-instance",
    time_range_minutes=30
)
```

6. Get storage metrics:
```python
await get_storage_metrics(
    database_name="your-db-instance",
    time_range_minutes=30
)
```

## Development

For development setup:
```bash
git clone https://github.com/yourusername/rds-mcp.git
cd rds-mcp
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## License

MIT License - See [LICENSE](LICENSE) file for details 