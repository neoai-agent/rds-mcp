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

1. Set up your environment variables:

   **Method: Using .env file**
   ```bash
   # Create a .env file in your project directory
   cat > .env << EOL
   # AWS Credentials
   AWS_ACCESS_KEY_ID=your-aws-access-key-here
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key-here
   AWS_REGION=your-aws-region-here
   
   # OpenAI Credentials
   OPENAI_API_KEY=your-openai-api-key-here
   
   # Optional: Model Configuration
   MODEL=openai/gpt-4o-mini
   EOL
   ```

2. Create `agent.yaml`:
```yaml
- name: "RDS Agent"
  description: "Agent to manage and monitor Amazon RDS instances"
  mcp_servers: 
    - name: "RDS MCP Server"
      args: ["--access-key=${AWS_ACCESS_KEY_ID}", "--secret-access-key=${AWS_SECRET_ACCESS_KEY}", "--region=${AWS_REGION}", "--openai_api_key=${OPENAI_API_KEY}"]
      command: "rds-mcp"
  system_prompt: "You are a DevOps engineer specializing in Amazon RDS management and monitoring. You can use the tools provided to analyze RDS instance performance, monitor metrics, and manage database operations. Use the tools precisely to gather valuable information about RDS instances and their performance."
```

3. Run the server:
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