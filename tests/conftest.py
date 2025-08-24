import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from rds_mcp.client import RDSClient, AWSClientManager, RDSClientConfig

# Shared test data
MOCK_RDS_INSTANCES = {
    'DBInstances': [
        {
            'DBInstanceIdentifier': 'test-db-1',
            'Engine': 'mysql',
            'DBInstanceStatus': 'available',
            'DbiResourceId': 'db-ABCD1234TEST',
            'Endpoint': {'Address': 'test-db-1.xxxxx.region.rds.amazonaws.com', 'Port': 3306}
        },
        {
            'DBInstanceIdentifier': 'prod-db-1',
            'Engine': 'postgres',
            'DBInstanceStatus': 'available',
            'DbiResourceId': 'db-ABCD1234PROD',
            'Endpoint': {'Address': 'prod-db-1.xxxxx.region.rds.amazonaws.com', 'Port': 5432}
        }
    ]
}

@pytest.fixture(scope='session')
def mock_aws_config():
    """Shared AWS configuration fixture"""
    return RDSClientConfig(
        access_key='test-access-key',
        secret_access_key='test-secret-key',
        region_name='us-west-2'
    )

@pytest.fixture(scope='session')
def mock_aws_client_manager(mock_aws_config):
    """Shared AWS client manager fixture with mocked services"""
    with patch('boto3.client') as mock_boto3_client:
        # Mock RDS client
        mock_rds = Mock()
        mock_rds.describe_db_instances.return_value = MOCK_RDS_INSTANCES
        
        # Mock CloudWatch client
        mock_cloudwatch = Mock()
        mock_cloudwatch.get_metric_data.return_value = {
            'MetricDataResults': [{
                'Id': 'cpuutilization',
                'Values': [75.5],
                'Timestamps': [datetime.now(timezone.utc)]
            }]
        }
        
        mock_boto3_client.side_effect = [mock_rds, mock_cloudwatch]
        
        manager = AWSClientManager(mock_aws_config)
        manager._rds = mock_rds
        manager._cloudwatch = mock_cloudwatch
        yield manager

@pytest.fixture(scope='session')
def mock_rds_client(mock_aws_client_manager):
    """Shared RDS client fixture with mocked services"""
    client = RDSClient(
        model='openai/gpt-4o-mini',
        openai_api_key='test-openai-key',
        aws_client_manager=mock_aws_client_manager
    )
    return client

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Automatically mock environment variables for all tests"""
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'test-access-key')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test-secret-key')
    monkeypatch.setenv('AWS_REGION', 'us-west-2')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai-key') 