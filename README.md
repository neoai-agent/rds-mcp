# RDS MCP (RDS Management Control Panel)

A powerful tool for monitoring and managing Amazon RDS instances through a Model-Controlled Panel (MCP) interface. This project provides an easy way to interact with RDS instances using natural language commands and AI-powered assistance.

## Features

- Get detailed RDS instance information
- Monitor database metrics in real-time
- Analyze slow queries for MySQL and PostgreSQL databases
- AI-powered natural language interface
- Secure AWS credential management
- Comprehensive metrics tracking including:
  - CPU utilization
  - Memory usage
  - Database connections
  - Storage space
  - Read/Write throughput
  - Query latency

## Prerequisites

- Python 3.8 or higher
- AWS account with appropriate permissions
- OpenAI API key
- AWS credentials configured

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rds-mcp.git
cd rds-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your environment variables:
```bash
export OPENAI_API_KEY='your-openai-api-key'
export AWS_ACCESS_KEY_ID='your-aws-access-key'
export AWS_SECRET_ACCESS_KEY='your-aws-secret-key'
export AWS_REGION='your-aws-region'
```

## Usage

1. Start the MCP server:
```bash
python server.py
```

2. Use the following commands to interact with your RDS instances:

- Get database information:
```
get_db_info database_name
```

- Get database metrics:
```
get_database_metrics database_name
```

- Get slow queries:
```
get_database_queries database_name [period_minutes]
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## Security

- Never commit AWS credentials or API keys
- Use environment variables for sensitive information
- Follow AWS security best practices
- Regularly update dependencies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- AWS RDS team for their excellent API
- OpenAI for providing the AI capabilities
- All contributors who help improve this project

## Support

If you encounter any issues or have questions, please:
1. Check the [existing issues](https://github.com/yourusername/rds-mcp/issues)
2. Create a new issue if your problem hasn't been reported
3. Join our community discussions

## Roadmap

- [ ] Add support for more database engines
- [ ] Implement query optimization suggestions
- [ ] Add automated backup management
- [ ] Create a web interface
- [ ] Add support for RDS clusters
- [ ] Implement automated scaling recommendations 