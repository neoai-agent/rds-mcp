from typing import Dict, List, Any
import boto3
import logging
import json
from datetime import datetime, timezone
from litellm import completion
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('rds_mcp')

@dataclass
class RDSClientConfig:
    access_key: str
    secret_access_key: str
    region_name: str

class AWSClientManager:
    """Manages AWS service client connections."""
    
    def __init__(self, config: RDSClientConfig):
        self.config = config
        self._rds = None
        self._elbv2 = None
        self._cloudwatch = None

    def get_aws_credentials(self):
        """Get AWS credentials with proper error handling"""
        if not self.config.access_key or not self.config.secret_access_key:
            logger.info("No explicit AWS credentials provided. Using default AWS credential chain (IAM roles, environment variables, etc.)")
            return None, None
        return self.config.access_key, self.config.secret_access_key
    
    def get_rds_client(self, region_name=None):
        """Get or create RDS client."""
        if not self._rds:
            try:
                access_key, secret_key = self.get_aws_credentials()
                client_kwargs = {
                    'region_name': region_name or self.config.region_name
                }
                
                if access_key and secret_key:
                    client_kwargs.update({
                        'aws_access_key_id': access_key,    
                        'aws_secret_access_key': secret_key
                    })
                else:
                    client_kwargs.update({
                        'config': boto3.session.Config(
                            user_agent_extra='rds-mcp/1.0',
                            connect_timeout=10,
                            read_timeout=30
                        )
                    })
                
                self._rds = boto3.client('rds', **client_kwargs)
            except Exception as e:
                logger.error(f"Failed to create RDS client: {str(e)}")
                raise
        return self._rds

    def get_cloudwatch_client(self, region_name=None):
        """Get or create CloudWatch client."""
        if not self._cloudwatch:
            try:
                access_key, secret_key = self.get_aws_credentials()
                client_kwargs = {
                    'region_name': region_name or self.config.region_name
                }
                
                if access_key and secret_key:
                    client_kwargs.update({
                        'aws_access_key_id': access_key,
                        'aws_secret_access_key': secret_key
                    })
                else:
                    client_kwargs.update({
                        'config': boto3.session.Config(
                            user_agent_extra='rds-mcp/1.0',
                            connect_timeout=10,
                            read_timeout=30
                        )
                    })
                
                self._cloudwatch = boto3.client('cloudwatch', **client_kwargs)
            except Exception as e:
                logger.error(f"Failed to create CloudWatch client: {str(e)}")
                raise
        return self._cloudwatch

class RDSClient:
    """Client for interacting with AWS RDS services and cloudwatch metrics for rds services"""

    def __init__(self, model: str, openai_api_key: str, aws_client_manager: AWSClientManager):
        """Initialize the RDS client and cloudwatch client.

        Args:
            region_name: AWS region name
            profile_name: Optional AWS profile name
        """
        self.model = model
        self.openai_api_key = openai_api_key
        self._name_matching_cache = {}
        self._rds_instances_cache = {
            "data": None,
            "timestamp": None,
            "cache_ttl": 300  # Cache TTL in seconds (5 minutes)
        }
        self.aws_client_manager = aws_client_manager
        self.initialize_rds()

    def initialize_rds(self):
        """Initialize the RDS client and cloudwatch client."""
        self.rds_client = self.aws_client_manager.get_rds_client()
        self.cloudwatch_client = self.aws_client_manager.get_cloudwatch_client()

    async def get_available_rds_instances(self):
        current_time = datetime.now(timezone.utc)

        # Check if we have valid cached data
        if (self._rds_instances_cache["data"] is not None and 
            self._rds_instances_cache["timestamp"] is not None and
            (current_time - self._rds_instances_cache["timestamp"]).total_seconds() < self._rds_instances_cache["cache_ttl"]):
            logger.info("Returning cached rds instances data")
            return self._rds_instances_cache["data"]
        
        try:
            response = self.rds_client.describe_db_instances()

            formatted_response = {
            "rds_instances": [instance['DBInstanceIdentifier'] for instance in response['DBInstances']],
            "total_rds_instances": len(response['DBInstances'])
            }

            self._rds_instances_cache["data"] = formatted_response
            self._rds_instances_cache["timestamp"] = current_time

            return formatted_response
        except Exception as e:
            logger.error(f"Error getting rds instances: {str(e)}")
            return {
                "error": f"Failed to get rds instances: {str(e)}",
                "status": "error"
            }
    
    async def find_matching_rds_instances(self, database_name: str = None):
        """
        Find the correct RDS instance name using LLM for intelligent matching.
        """
        # Create a cache key based on the input parameters
        cache_key = f"{database_name}"

        # Check if we have a cached result
        if cache_key in self._name_matching_cache:
            logger.info(f"Using cached rds instances result for {cache_key}")
            return self._name_matching_cache[cache_key]
        
        available_instances = await self.get_available_rds_instances()
        rds_instances = available_instances['rds_instances']

        prompt = f"""
        Given the database name: {database_name}, please find the most likely RDS instance name from the following list: {rds_instances}
        Format your response as a JSON object with:
        {{
            "rds_instance": "best matching rds instance name or null"
        }}
        """

        response = await self.llm_call(prompt)
        if not response:
            logger.error("No response from LLM")
            return None
        
        try:
            result = json.loads(response)
            rds_instance = result.get('rds_instance')
            if rds_instance:
                self._name_matching_cache[cache_key] = rds_instance
                return rds_instance
            else:
                return None
        except Exception as e:
            logger.error(f"Error parsing JSON response: {str(e)}")

    def best_matching_rds_instance(self, target: str = None, candidates: list = None):
        """Basic fallback matching function when LLM is not available"""
        if not target or not candidates:
            return None
        
        target = target.lower()

        for candidate in candidates:
            if candidate.lower() == target:
                return candidate
            
        partial_matches = [
            c for c in candidates
            if target in c.lower() or c.lower() in target
        ]
        
        if partial_matches:
            partial_matches.sort(key=len)
            return partial_matches[0]
        
        return None

    async def llm_call(self, prompt: str) -> str:
        """
        Call LLM using LiteLLM to find matching names.
        
        Args:
            prompt (str): The prompt to send to the LLM
            
        Returns:
            str: JSON string containing the LLM's response with rds_instance
        """
        try:
            response = completion(
                model=self.model,
                api_key=self.openai_api_key,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that finds the best matching RDS instance name. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            response_content = response.choices[0].message.content
            
            try:
                json.loads(response_content)
                return response_content
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Error llm calling: {str(e)}")
            return None