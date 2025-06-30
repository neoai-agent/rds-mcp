import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
import json
from rds_mcp.server import RDSMCPServer
from rds_mcp.client import RDSClient, AWSClientManager, RDSClientConfig

# Test data
MOCK_DB_INFO = {
    'DBInstances': [{
        'DBInstanceIdentifier': 'test-db-1',
        'DBInstanceStatus': 'available',
        'Endpoint': {
            'Address': 'test-db-1.xxxxx.region.rds.amazonaws.com',
            'Port': 3306
        },
        'DbiResourceId': 'db-12345',
        'AllocatedStorage': 100
    }]
}

MOCK_METRICS = {
    'MetricDataResults': [{
        'Id': 'cpuutilization',
        'Values': [75.5],
        'Timestamps': [datetime.now(timezone.utc)]
    }]
}

MOCK_SLOW_QUERIES = {
    'LogFileData': '''
# Time: 2024-01-01T10:00:00.000Z
# Query_time: 10.5  Lock_time: 0.1  Rows_sent: 100  Rows_examined: 1000
SELECT * FROM users WHERE status = 'active';
'''
}

@pytest.fixture
def mock_aws_config():
    return RDSClientConfig(
        access_key='test-access-key',
        secret_access_key='test-secret-key',
        region_name='us-west-2'
    )

@pytest.fixture
def mock_aws_client_manager(mock_aws_config):
    with patch('boto3.client') as mock_boto3_client:
        # Mock RDS client
        mock_rds = Mock()
        mock_rds.describe_db_instances.return_value = MOCK_DB_INFO
        mock_rds.download_db_log_file_portion.return_value = MOCK_SLOW_QUERIES
        
        # Mock CloudWatch client
        mock_cloudwatch = Mock()
        mock_cloudwatch.get_metric_data.return_value = MOCK_METRICS
        
        mock_boto3_client.side_effect = [mock_rds, mock_cloudwatch]
        
        manager = AWSClientManager(mock_aws_config)
        manager._rds = mock_rds
        manager._cloudwatch = mock_cloudwatch
        yield manager

@pytest.fixture
def mock_rds_client(mock_aws_client_manager):
    client = RDSClient(
        model='gpt-3.5-turbo',
        openai_api_key='test-openai-key',
        aws_client_manager=mock_aws_client_manager
    )
    client.find_matching_rds_instances = AsyncMock(return_value='test-db-1')
    return client

@pytest.fixture
def rds_mcp_server(mock_rds_client):
    with patch('rds_mcp.server.RDSClient', return_value=mock_rds_client):
        server = RDSMCPServer(
            model='gpt-3.5-turbo',
            openai_api_key='test-openai-key',
            aws_client_manager=mock_rds_client.aws_client_manager
        )
        yield server

@pytest.mark.asyncio
async def test_get_db_info(rds_mcp_server):
    """Test getting database information"""
    result = await rds_mcp_server.get_db_info('test-db-1')
    
    assert result['status'] == 'available'
    assert result['DBInstanceIdentifier'] == 'test-db-1'
    assert result['DBInstanceEndpoint'] == 'test-db-1.xxxxx.region.rds.amazonaws.com'
    assert result['DBInstancePort'] == 3306
    assert result['DbiResourceId'] == 'db-12345'
    assert result['AllocatedStorage'] == 100

@pytest.mark.asyncio
async def test_get_db_info_not_found(rds_mcp_server, mock_rds_client):
    """Test getting database information for non-existent database"""
    mock_rds_client.find_matching_rds_instances.return_value = None
    
    result = await rds_mcp_server.get_db_info('nonexistent-db')
    assert result['status'] == 'error'
    assert 'No matching RDS instance found' in result['message']

@pytest.mark.asyncio
async def test_get_database_metrics(rds_mcp_server):
    """Test getting database metrics"""
    result = await rds_mcp_server.get_database_metrics('test-db-1')
    
    assert result['status'] == 'success'
    assert result['database'] == 'test-db-1'
    assert 'metrics' in result
    assert 'timestamp' in result
    
    metrics = result['metrics']
    assert 'cpu_utilization' in metrics
    assert 'free_memory_bytes' in metrics
    assert 'connections' in metrics
    assert 'free_storage_bytes' in metrics

@pytest.mark.asyncio
async def test_get_database_metrics_not_found(rds_mcp_server, mock_rds_client):
    """Test getting metrics for non-existent database"""
    mock_rds_client.find_matching_rds_instances.return_value = None
    
    result = await rds_mcp_server.get_database_metrics('nonexistent-db')
    assert result['status'] == 'error'
    assert 'No matching RDS instance found' in result['message']

@pytest.mark.asyncio
async def test_get_database_queries_mysql(rds_mcp_server):
    """Test getting slow queries for MySQL database"""
    # Mock the database engine type
    rds_mcp_server.client.rds_client.describe_db_instances.return_value = {
        'DBInstances': [{
            'Engine': 'mysql',
            'DBInstanceIdentifier': 'test-db-1'
        }]
    }
    
    result = await rds_mcp_server.get_database_queries('test-db-1')
    
    assert result['status'] == 'success'
    assert result['database'] == 'test-db-1'
    assert 'total_slow_queries' in result
    assert 'top_5_queries' in result
    assert isinstance(result['top_5_queries'], list)

@pytest.mark.asyncio
async def test_get_database_queries_postgres(rds_mcp_server):
    """Test getting slow queries for PostgreSQL database"""
    # Mock the database engine type
    rds_mcp_server.client.rds_client.describe_db_instances.return_value = {
        'DBInstances': [{
            'Engine': 'postgres',
            'DBInstanceIdentifier': 'test-db-1'
        }]
    }
    
    # Mock the log files response
    rds_mcp_server.client.rds_client.describe_db_log_files.return_value = {
        'DescribeDBLogFiles': [{
            'LogFileName': 'error/postgresql.log.2024-01-01',
            'LastWritten': int(datetime.now(timezone.utc).timestamp() * 1000)
        }]
    }
    
    result = await rds_mcp_server.get_database_queries('test-db-1')
    
    assert result['status'] == 'success'
    assert result['database'] == 'test-db-1'
    assert 'total_slow_queries' in result
    assert 'top_5_queries' in result
    assert isinstance(result['top_5_queries'], list)

@pytest.mark.asyncio
async def test_get_database_queries_unsupported_engine(rds_mcp_server):
    """Test getting slow queries for unsupported database engine"""
    # Mock the database engine type
    rds_mcp_server.client.rds_client.describe_db_instances.return_value = {
        'DBInstances': [{
            'Engine': 'oracle',
            'DBInstanceIdentifier': 'test-db-1'
        }]
    }
    
    result = await rds_mcp_server.get_database_queries('test-db-1')
    assert result['status'] == 'error'
    assert 'Unsupported database engine' in result['message']

@pytest.mark.asyncio
async def test_get_database_queries_not_found(rds_mcp_server, mock_rds_client):
    """Test getting queries for non-existent database"""
    mock_rds_client.find_matching_rds_instances.return_value = None
    
    result = await rds_mcp_server.get_database_queries('nonexistent-db')
    assert result['status'] == 'error'
    assert 'No matching RDS instance found' in result['message']

def test_server_initialization(rds_mcp_server):
    """Test server initialization and tool registration"""
    assert hasattr(rds_mcp_server, 'mcp')
    assert hasattr(rds_mcp_server, 'client')
    assert callable(rds_mcp_server.get_db_info)
    assert callable(rds_mcp_server.get_database_metrics)
    assert callable(rds_mcp_server.get_database_queries) 