from datetime import datetime, timedelta, timezone
import re
from mcp.server.fastmcp import FastMCP
import logging
from rds_mcp.client import RDSClient, AWSClientManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('rds_mcp')


class RDSCMPServer:
    def __init__(self, model: str, openai_api_key: str, aws_client_manager: AWSClientManager):
        self.mcp = FastMCP("rds")
        self.client = RDSClient(model=model, openai_api_key=openai_api_key, aws_client_manager=aws_client_manager)
        self._register_tools()

    def _register_tools(self):
        self.mcp.tool()(self.get_db_info)
        self.mcp.tool()(self.get_database_metrics)
        self.mcp.tool()(self.get_database_queries)

    def run_mcp_blocking(self):
        """
        Runs the FastMCP server. This method is blocking and should be called
        after any necessary asynchronous initialization (like self.client.initialize_ecs)
        has been completed in a separate AnyIO event loop.
        """
        # self.client.initialize_ecs() is assumed to have been awaited
        # before this synchronous method is called.
        
        # The FastMCP server's run method will internally call anyio.run()
        # and manage its own event loop for stdio transport.
        self.mcp.run(transport='stdio')

    #Get RDS DB info
    async def get_db_info(self, database_name: str):
        """Get detailed information about an RDS database instance"""
        
        try:
            # Find the best matching RDS instance name
            matching_instance = await self.client.find_matching_rds_instances(database_name)
            if not matching_instance:
                return {"status": "error", "message": "No matching RDS instance found"}
            
            # Use the correct instance name
            database_name = matching_instance
            rds_info = self.client.rds_client.describe_db_instances(DBInstanceIdentifier=database_name)['DBInstances'][0]
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return {
            "status": rds_info['DBInstanceStatus'],
            "DBInstanceIdentifier": rds_info['DBInstanceIdentifier'],
            "DBInstanceEndpoint": rds_info['Endpoint']['Address'],
            "DBInstancePort": rds_info['Endpoint']['Port'],
            "DbiResourceId": rds_info['DbiResourceId'],
            "AllocatedStorage": rds_info['AllocatedStorage']
        }

    #Get RDS DB metrics
    async def get_database_metrics(self, database_name: str):
        """
        Get key RDS metrics including CPU, memory, connections, and storage
        Returns metrics for the last 60 minutes
        """
        try:
            # Find the best matching RDS instance name
            matching_instance = await self.client.find_matching_rds_instances(database_name)
            if not matching_instance:
                return {"status": "error", "message": "No matching RDS instance found"}
            
            # Use the correct instance name
            database_name = matching_instance
            
            metrics = [
                {'name': 'CPUUtilization', 'stat': 'Average'},
                {'name': 'FreeableMemory', 'stat': 'Average'},
                {'name': 'DatabaseConnections', 'stat': 'Average'},
                {'name': 'FreeStorageSpace', 'stat': 'Average'},
                {'name': 'ReadThroughput', 'stat': 'Average'},
                {'name': 'WriteThroughput', 'stat': 'Average'},
                {'name': 'ReadLatency', 'stat': 'Average'},
                {'name': 'WriteLatency', 'stat': 'Average'},
                {'name': 'DBLoad', 'stat': 'Average'}
            ]
            
            results = {}
            for metric in metrics:
                response = self.client.cloudwatch_client.get_metric_data(
                    MetricDataQueries=[
                        {
                            'Id': metric['name'].lower(),
                            'MetricStat': {
                                'Metric': {
                                    'Namespace': 'AWS/RDS',
                                    'MetricName': metric['name'],
                                    'Dimensions': [
                                        {'Name': 'DBInstanceIdentifier', 'Value': database_name}
                                    ]
                                },
                                'Period': 300,
                                'Stat': metric['stat']
                            }
                        }
                    ],
                    StartTime=datetime.now(timezone.utc) - timedelta(minutes=60),
                    EndTime=datetime.now(timezone.utc)
                )
                
                # Get the most recent value
                values = response['MetricDataResults'][0]['Values']
                results[metric['name']] = values[-1] if values else None
            
            return {
                "status": "success",
                "database": database_name,
                "metrics": {
                    "cpu_utilization": results['CPUUtilization'],
                    "free_memory_bytes": results['FreeableMemory'],
                    "connections": results['DatabaseConnections'],
                    "free_storage_bytes": results['FreeStorageSpace'],
                    "read_throughput": results['ReadThroughput'],
                    "write_throughput": results['WriteThroughput'],
                    "read_latency": results['ReadLatency'],
                    "write_latency": results['WriteLatency'],
                    "db_load": results['DBLoad']
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    #Get RDS DB slow queries from Cloudwatch
    async def get_database_queries(self, database_name: str, period_minutes: int = 60):
        """Get slow query logs from RDS database (supports MySQL and PostgreSQL)"""
        try:
            # Find the best matching RDS instance name
            matching_instance = await self.client.find_matching_rds_instances(database_name)
            if not matching_instance:
                return {"status": "error", "message": "No matching RDS instance found"}
            
            # Use the correct instance name
            database_name = matching_instance
            # Calculate time threshold
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=period_minutes)
            
            db_instance = self.client.rds_client.describe_db_instances(DBInstanceIdentifier=database_name)['DBInstances'][0]
            engine = db_instance['Engine'].lower()
            log_entries = []

            if 'mysql' in engine:
                log_file_name = 'slowquery/mysql-slowquery.log'
                log_data = []
                marker = '0'
                while True:
                    response = self.client.rds_client.download_db_log_file_portion(
                        DBInstanceIdentifier=database_name,
                        LogFileName='slowquery/mysql-slowquery.log',
                        NumberOfLines=1000,
                        Marker=marker
                    )
                    log_data.append(response.get('LogFileData', ''))
                    marker = response.get('Marker', '0')
                    if not response.get('AdditionalDataPending', False):
                        break
                
                current_entry = {}
                capture_sql = False
                sql_lines = []

                for line in ''.join(log_data).split('\n'):
                    line = line.strip()
                    #print(f'lines: {line}')

                    if line.startswith('# Time:'):
                        if current_entry.get('query_time') and sql_lines:
                                current_entry['sql'] = ' '.join(sql_lines).strip()

                                if "IN (" in current_entry['sql'].upper():
                                    # Handle IN clause truncation
                                    parts = current_entry['sql'].split("IN (")
                                    before_in = parts[0] + "IN ("
                                    in_clause = parts[1].split(")", 1)
                                    values = in_clause[0].split(",")
                                    
                                    if len(values) > 5:
                                        # Keep first 3 and last 2 values
                                        truncated = f"{','.join(values[:3])}, ... {','.join(values[-2:])}"
                                        current_entry['sql'] = f"{before_in}{truncated}){in_clause[1] if len(in_clause) > 1 else ''}"
                                
                                # Truncate long queries
                                if len(current_entry['sql']) > 1500:
                                    current_entry['sql'] = f"{current_entry['sql'][:1500]}... [truncated]"
                                
                                log_entries.append(current_entry)

                        current_entry = {
                            'timestamp': None,
                            'query_time': None,
                            'lock_time': None,
                            'rows_sent': None,
                            'rows_examined': None,
                            'sql': None
                        }

                        sql_lines = []
                        capture_sql = False

                        try: 
                            ts_str = line.replace('# Time: ', '').strip()
                            current_entry['timestamp'] = datetime.strptime(
                                ts_str,
                                '%Y-%m-%dT%H:%M:%S.%fZ'
                            ).replace(tzinfo=timezone.utc)
                            current_entry['timestamp'] = current_entry['timestamp'].isoformat()
                        except ValueError:
                                pass
                    elif line.startswith('# Query_time:'):
                        metrics = re.findall(
                            r'(\w+): (\d+\.?\d*|\d+)', 
                            line.replace('# ', '')
                        )
                        for metric, value in metrics:
                            if metric == 'Query_time':
                                current_entry['query_time'] = float(value)
                            elif metric == 'Lock_time':
                                current_entry['lock_time'] = float(value)
                            elif metric == 'Rows_sent':
                                current_entry['rows_sent'] = int(value)
                            elif metric == 'Rows_examined':
                                current_entry['rows_examined'] = int(value)
                    
                    elif not line.startswith('#') and line:
                        if line.lower().startswith('select'):
                            capture_sql = True
                            sql_lines.append(line)
                        elif capture_sql:
                            sql_lines.append(line)
                    
                    elif line.startswith('SET timestamp='):
                        # Skip internal MySQL timestamp lines
                        continue
                    
                    elif line.startswith('use '):
                        # Skip database selection lines
                        continue
                    elif line and not line.startswith('#'):
                        if not capture_sql and not line.lower().startswith('select'):
                            continue
                        capture_sql = True
                        sql_lines.append(line)
                    
                    elif capture_sql and line == '':
                        # End of query
                        capture_sql = False

            elif 'postgres' in engine:
                log_files = []
                describe_marker = None
                time_threshold_ms = int(time_threshold.timestamp() * 1000)
                postgres_log_regex = re.compile(
                    r'LOG:  duration: (\d+\.?\d*) ms  statement: (.*)',
                    re.DOTALL
                )
                timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC:')

                while True:
                    describe_kwargs = {
                        'DBInstanceIdentifier': database_name,
                        'FilenameContains': 'error/postgresql.log.'
                    }
                    if describe_marker:
                        describe_kwargs['Marker'] = describe_marker
                    describe_response = self.client.rds_client.describe_db_log_files(**describe_kwargs)
                    for log_file in describe_response.get('DescribeDBLogFiles', []):
                        if log_file.get('LastWritten', 0) >= time_threshold_ms:
                            log_files.append(log_file['LogFileName'])
                    describe_marker = describe_response.get('Marker')
                    if not describe_marker:
                        break
                print(f'found logs files: {log_files}')
                # Process each relevant log file
                for log_file_name in log_files:
                    log_data = []
                    marker = '0'
                    while True:
                        response = self.client.rds_client.download_db_log_file_portion(
                            DBInstanceIdentifier=database_name,
                            LogFileName=log_file_name,
                            NumberOfLines=1000,
                            Marker=marker
                        )
                        log_data.append(response.get('LogFileData', ''))
                        marker = response.get('Marker', '0')
                        if not response.get('AdditionalDataPending', False):
                            break
                    full_log = ''.join(log_data)
                    #print(full_log)
                    # Parse multi-line entries
                    buffer = []
                    for line in full_log.split('\n'):
                        line = line.strip()
                        #print(line)
                        if timestamp_pattern.match(line):
                            if buffer:
                                entry = '\n'.join(buffer)
                                #print(f'Raw entry: {entry}')
                                match = postgres_log_regex.search(entry)
                                #print(f'matching : {match}')
                                if match:
                                    duration, sql = match.groups()
                                    #print(f"Match groups: {match.groups() if match else 'No match'}")
                                    #print(f'sql_text: {sql}')
                                    if "IN (" in sql.upper():
                                        parts = sql.split("IN (")
                                        before_in = parts[0] + "IN ("
                                        in_clause = parts[1].split(")", 1)
                                        values = in_clause[0].split(",")
                                        if len(values) > 5:
                                            truncated_values = f"{','.join(values[:3])}, ... {','.join(values[-2:])}"
                                            sql = f"{before_in}{truncated_values}){in_clause[1]}"
                                    if len(sql) > 1500:
                                        sql = f"{sql[:1500]}... [truncated]"
                                    log_entries.append({
                                        "query_time": duration,
                                        "lock_time": None,
                                        "rows_sent": None,
                                        "rows_examined": None,
                                        "sql": sql
                                    })
                            buffer = [line]
                        else:
                            if buffer:
                                buffer.append(line)
                    # Process remaining buffer
                    if buffer:
                        entry = '\n'.join(buffer)
                        match = postgres_log_regex.search(entry)
                        if match:
                            duration, sql = match.groups()
                            if "IN (" in sql.upper():
                                parts = sql.split("IN (")
                                before_in = parts[0] + "IN ("
                                in_clause = parts[1].split(")", 1)
                                values = in_clause[0].split(",")
                                if len(values) > 5:
                                    truncated_values = f"{','.join(values[:3])}, ... {','.join(values[-2:])}"
                                    sql = f"{before_in}{truncated_values}){in_clause[1]}"
                            if len(sql) > 1500:
                                sql = f"{sql[:1500]}... [truncated]"
                            log_entries.append({
                                "query_time": duration,
                                "lock_time": None,
                                "rows_sent": None,
                                "rows_examined": None,
                                "sql": sql
                            })
            
            else:
                return {"status": "error", "message": f"Unsupported database engine: {engine}"}
            
            # Sort by query time (descending) and limit to top 50
            log_entries.sort(key=lambda x: x['query_time'], reverse=True)
            log_entries = log_entries[:50]
            
            return {
                "status": "success",
                "database": database_name,
                "period_minutes": period_minutes,
                "total_slow_queries": len(log_entries),
                "top_5_queries": log_entries[:5]
            }
            
        except Exception as e:
            logger.error(f"Error getting database queries: {str(e)}")
            return {"status": "error", "message": str(e)}