import pytest
import boto3
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import json
from rds_mcp.client import RDSClient, AWSClientManager, RDSClientConfig
from botocore.exceptions import NoCredentialsError

# Test data
MOCK_RDS_INSTANCES = {
    'DBInstances': [
        {
            'DBInstanceIdentifier': 'test-db-1',
            'Engine': 'mysql',
            'DBInstanceStatus': 'available',
            'Endpoint': {'Address': 'test-db-1.xxxxx.region.rds.amazonaws.com', 'Port': 3306}
        },
        {
            'DBInstanceIdentifier': 'prod-db-1',
            'Engine': 'postgres',
            'DBInstanceStatus': 'available',
            'Endpoint': {'Address': 'prod-db-1.xxxxx.region.rds.amazonaws.com', 'Port': 5432}
        }
    ]
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
        mock_rds.describe_db_instances.return_value = MOCK_RDS_INSTANCES
        mock_boto3_client.return_value = mock_rds
        
        manager = AWSClientManager(mock_aws_config)
        manager._rds = mock_rds
        manager._cloudwatch = Mock()
        yield manager

@pytest.fixture
def rds_client(mock_aws_client_manager):
    return RDSClient(
        model='gpt-3.5-turbo',
        openai_api_key='test-openai-key',
        aws_client_manager=mock_aws_client_manager
    )

@pytest.mark.asyncio
async def test_get_available_rds_instances(rds_client):
    """Test getting available RDS instances"""
    result = await rds_client.get_available_rds_instances()
    
    if isinstance(result, dict) and 'error' in result:
        assert result['status'] != 'error'
    else:
        assert 'rds_instances' in result
    assert len(result['rds_instances']) == 2
    assert 'test-db-1' in result['rds_instances']
    assert 'prod-db-1' in result['rds_instances']
    assert result['total_rds_instances'] == 2

@pytest.mark.asyncio
async def test_get_available_rds_instances_cache(rds_client):
    """Test RDS instances caching"""
    # First call
    result1 = await rds_client.get_available_rds_instances()
    # Second call should use cache
    result2 = await rds_client.get_available_rds_instances()
    
    assert result1 == result2
    # Verify boto3 client was called only once
    rds_client.rds_client.describe_db_instances.assert_called_once()

@pytest.mark.asyncio
async def test_find_matching_rds_instances(rds_client):
    """Test finding matching RDS instances using LLM"""
    with patch.object(rds_client, 'llm_call', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({"rds_instance": "test-db-1"})
        
        result = await rds_client.find_matching_rds_instances("test")
        assert result == "test-db-1"
        
        # Test cache
        result2 = await rds_client.find_matching_rds_instances("test")
        assert result2 == "test-db-1"
        assert mock_llm.call_count == 1  # Should use cache

@pytest.mark.asyncio
async def test_find_matching_rds_instances_no_match(rds_client):
    """Test finding matching RDS instances when no match is found"""
    with patch.object(rds_client, 'llm_call', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({"rds_instance": None})
        
        result = await rds_client.find_matching_rds_instances("nonexistent")
        assert result is None

def test_best_matching_rds_instance(rds_client):
    """Test basic string matching fallback"""
    candidates = ['test-db-1', 'prod-db-1', 'dev-db-1']
    
    # Test exact match
    assert rds_client.best_matching_rds_instance('test-db-1', candidates) == 'test-db-1'
    
    # Test partial match
    assert rds_client.best_matching_rds_instance('test', candidates) == 'test-db-1'
    
    # Test no match
    assert rds_client.best_matching_rds_instance('nonexistent', candidates) is None

@pytest.mark.asyncio
async def test_llm_call(rds_client):
    """Test LLM call functionality"""
    with patch("litellm.completion", new_callable=AsyncMock) as mock_completion:
         mock_completion.return_value.choices[0].message.content = json.dumps({"rds_instance": "test-db-1"})
         result = await rds_client.llm_call("Find the RDS instance matching 'test-db-1'")
         assert result == json.dumps({"rds_instance": "test-db-1"})

@pytest.mark.asyncio
async def test_llm_call_error(rds_client):
    """Test LLM call error handling"""
    with patch('litellm.completion', side_effect=Exception("API Error")):
        result = await rds_client.llm_call("test prompt")
        assert result is None

def test_aws_client_manager_credentials(mock_aws_config):
    """Test AWS client manager credential handling"""
    manager = AWSClientManager(mock_aws_config)
    access_key, secret_key = manager.get_aws_credentials()
    assert access_key == 'test-access-key'
    assert secret_key == 'test-secret-key'

def test_aws_client_manager_no_credentials():
    """Test AWS client manager with no credentials"""
    config = RDSClientConfig(access_key='', secret_access_key='', region_name='us-west-2')
    manager = AWSClientManager(config)
    
    with patch('boto3.Session') as mock_session:
        mock_session.return_value.get_credentials.return_value = None
        with pytest.raises(NoCredentialsError):
            manager.get_aws_credentials() 