"""
Supabase Database Manager
Manages database operations and vector storage for speedtest history
"""

import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import csv
from supabase import create_client, Client
import json


class SupabaseManager:
    """Manages Supabase database and vector operations"""
    
    def __init__(self, url: str, key: str):
        """
        Initialize Supabase client
        
        Args:
            url: Supabase project URL
            key: Supabase API key (anon or service role)
        """
        self.url = url
        self.key = key
        self.client: Client = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        Connect to Supabase
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.client = create_client(self.url, self.key)
            # Test connection
            self.client.table('speedtest_history').select("id").limit(1).execute()
            self.is_connected = True
            print("✅ Connected to Supabase")
            return True
        except Exception as e:
            print(f"❌ Supabase connection error: {e}")
            self.is_connected = False
            return False
    
    def setup_database(self) -> bool:
        """
        Create tables and enable pgvector extension
        This should be run once during initial setup
        
        Returns:
            bool: True if setup successful
        """
        try:
            # Note: pgvector extension and table creation should be done via Supabase SQL Editor
            # This method checks if table exists
            result = self.client.table('speedtest_history').select("id").limit(1).execute()
            print("✅ Database tables already exist")
            return True
        except Exception as e:
            print(f"⚠️ Database setup needed. Please run the SQL setup script.")
            print(f"Error: {e}")
            return False
    
    def get_setup_sql(self) -> str:
        """
        Returns SQL script for database setup
        User should run this in Supabase SQL Editor
        """
        return """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create speedtest_history table
CREATE TABLE IF NOT EXISTS speedtest_history (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    ping_ms DECIMAL(10,2) NOT NULL,
    jitter_ms DECIMAL(10,2) NOT NULL,
    download_mbps DECIMAL(10,2) NOT NULL,
    upload_mbps DECIMAL(10,2) NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    server_country VARCHAR(100),
    isp VARCHAR(255),
    client_ip VARCHAR(50),
    embedding VECTOR(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS speedtest_embedding_idx 
ON speedtest_history 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for time-based queries
CREATE INDEX IF NOT EXISTS idx_timestamp 
ON speedtest_history(timestamp DESC);

-- Create index for ISP queries
CREATE INDEX IF NOT EXISTS idx_isp 
ON speedtest_history(isp);
"""
    
    def save_test_result(self, test_data: Dict, embedding: Optional[List[float]] = None) -> bool:
        """
        Save speedtest result to Supabase
        
        Args:
            test_data: Dictionary containing test results
            embedding: Optional vector embedding (768 dimensions)
            
        Returns:
            bool: True if save successful
        """
        try:
            # Parse server info
            server_info = test_data.get('server', 'Unknown')
            server_name = server_info
            server_country = ''
            
            if '(' in server_info and ')' in server_info:
                parts = server_info.split('(')
                server_name = parts[0].strip()
                server_country = parts[1].replace(')', '').strip()
            
            # Prepare data
            data = {
                'timestamp': test_data.get('timestamp', datetime.now().isoformat()),
                'ping_ms': float(test_data.get('ping', 0)),
                'jitter_ms': float(test_data.get('jitter', 0)),
                'download_mbps': float(test_data.get('download', 0)),
                'upload_mbps': float(test_data.get('upload', 0)),
                'server_name': server_name,
                'server_country': server_country,
                'isp': test_data.get('isp', 'Unknown'),
                'client_ip': test_data.get('ip', 'Unknown')
            }
            
            # Add embedding if provided
            if embedding:
                data['embedding'] = embedding
            
            # Insert into Supabase
            result = self.client.table('speedtest_history').insert(data).execute()
            print(f"✅ Saved test result to Supabase (ID: {result.data[0]['id']})")
            return True
            
        except Exception as e:
            print(f"❌ Error saving to Supabase: {e}")
            return False
    
    def query_similar_tests(self, embedding: List[float], limit: int = 5) -> List[Dict]:
        """
        Find similar tests using vector similarity search
        
        Args:
            embedding: Query vector (768 dimensions)
            limit: Number of results to return
            
        Returns:
            List of similar test results
        """
        try:
            # Use RPC function for vector similarity search
            # Note: This requires a custom function in Supabase
            result = self.client.rpc(
                'match_speedtest_history',
                {
                    'query_embedding': embedding,
                    'match_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"⚠️ Vector search not available, using fallback: {e}")
            # Fallback: get recent tests
            return self.get_recent_tests(limit)
    
    def get_rpc_function_sql(self) -> str:
        """
        Returns SQL for creating the vector similarity search function
        User should run this in Supabase SQL Editor
        """
        return """
-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION match_speedtest_history(
    query_embedding VECTOR(768),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id BIGINT,
    timestamp TIMESTAMPTZ,
    ping_ms DECIMAL,
    jitter_ms DECIMAL,
    download_mbps DECIMAL,
    upload_mbps DECIMAL,
    server_name VARCHAR,
    server_country VARCHAR,
    isp VARCHAR,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        speedtest_history.id,
        speedtest_history.timestamp,
        speedtest_history.ping_ms,
        speedtest_history.jitter_ms,
        speedtest_history.download_mbps,
        speedtest_history.upload_mbps,
        speedtest_history.server_name,
        speedtest_history.server_country,
        speedtest_history.isp,
        1 - (speedtest_history.embedding <=> query_embedding) AS similarity
    FROM speedtest_history
    WHERE speedtest_history.embedding IS NOT NULL
    ORDER BY speedtest_history.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""
    
    def get_recent_tests(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent test results
        
        Args:
            limit: Number of results to return
            
        Returns:
            List of recent test results
        """
        try:
            result = self.client.table('speedtest_history')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ Error fetching recent tests: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Calculate aggregate statistics from history
        
        Returns:
            Dictionary with statistics
        """
        try:
            # Get all data for statistics
            result = self.client.table('speedtest_history')\
                .select('ping_ms, jitter_ms, download_mbps, upload_mbps')\
                .execute()
            
            if not result.data:
                return {
                    'count': 0,
                    'avg_ping': 0,
                    'avg_jitter': 0,
                    'avg_download': 0,
                    'avg_upload': 0
                }
            
            data = result.data
            count = len(data)
            
            stats = {
                'count': count,
                'avg_ping': sum(float(d['ping_ms']) for d in data) / count,
                'avg_jitter': sum(float(d['jitter_ms']) for d in data) / count,
                'avg_download': sum(float(d['download_mbps']) for d in data) / count,
                'avg_upload': sum(float(d['upload_mbps']) for d in data) / count,
                'max_download': max(float(d['download_mbps']) for d in data),
                'max_upload': max(float(d['upload_mbps']) for d in data),
                'min_ping': min(float(d['ping_ms']) for d in data)
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error calculating statistics: {e}")
            return {}
    
    def migrate_csv_to_supabase(self, csv_path: str, embedding_generator=None) -> Tuple[int, int]:
        """
        Import existing history.csv data to Supabase
        
        Args:
            csv_path: Path to history.csv file
            embedding_generator: Function to generate embeddings (optional)
            
        Returns:
            Tuple of (success_count, total_count)
        """
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return (0, 0)
        
        try:
            success_count = 0
            total_count = 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    total_count += 1
                    
                    try:
                        # Parse CSV row
                        test_data = {
                            'timestamp': row.get('Waktu', ''),
                            'ping': row.get('Ping (ms)', 0),
                            'jitter': row.get('Jitter (ms)', 0),
                            'download': row.get('Download (Mbps)', 0),
                            'upload': row.get('Upload (Mbps)', 0),
                            'server': row.get('Server', 'Unknown'),
                            'isp': row.get('ISP', 'Unknown')
                        }
                        
                        # Generate embedding if function provided
                        embedding = None
                        if embedding_generator:
                            try:
                                text = self.create_test_description(test_data)
                                embedding = embedding_generator(text)
                            except Exception as e:
                                print(f"⚠️ Embedding generation failed for row {total_count}: {e}")
                        
                        # Save to Supabase
                        if self.save_test_result(test_data, embedding):
                            success_count += 1
                            
                    except Exception as e:
                        print(f"⚠️ Error processing row {total_count}: {e}")
                        continue
            
            print(f"✅ Migration complete: {success_count}/{total_count} records imported")
            return (success_count, total_count)
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            return (0, 0)
    
    def create_test_description(self, test_data: Dict) -> str:
        """
        Create text description for embedding generation
        
        Args:
            test_data: Test result dictionary
            
        Returns:
            Formatted text description
        """
        return f"""Network Speed Test Results:
- Date: {test_data.get('timestamp', 'Unknown')}
- ISP: {test_data.get('isp', 'Unknown')}
- Server: {test_data.get('server', 'Unknown')}
- Latency: {test_data.get('ping', 0)}ms (Jitter: {test_data.get('jitter', 0)}ms)
- Download Speed: {test_data.get('download', 0)} Mbps
- Upload Speed: {test_data.get('upload', 0)} Mbps"""
    
    def sync_to_csv(self, csv_path: str) -> bool:
        """
        Export Supabase data back to CSV for backup
        
        Args:
            csv_path: Path to save CSV file
            
        Returns:
            bool: True if export successful
        """
        try:
            # Get all data
            result = self.client.table('speedtest_history')\
                .select('timestamp, ping_ms, jitter_ms, download_mbps, upload_mbps, server_name, server_country, isp')\
                .order('timestamp', desc=False)\
                .execute()
            
            if not result.data:
                print("⚠️ No data to export")
                return False
            
            # Write to CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Waktu', 'Ping (ms)', 'Jitter (ms)', 
                    'Download (Mbps)', 'Upload (Mbps)', 
                    'Server', 'ISP'
                ])
                
                # Data rows
                for row in result.data:
                    server = row['server_name']
                    if row.get('server_country'):
                        server += f" ({row['server_country']})"
                    
                    writer.writerow([
                        row['timestamp'],
                        row['ping_ms'],
                        row['jitter_ms'],
                        row['download_mbps'],
                        row['upload_mbps'],
                        server,
                        row['isp']
                    ])
            
            print(f"✅ Exported {len(result.data)} records to {csv_path}")
            return True
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False
    
    def get_total_count(self) -> int:
        """Get total number of tests in database"""
        try:
            result = self.client.table('speedtest_history')\
                .select('id', count='exact')\
                .execute()
            return result.count if result.count else 0
        except:
            return 0
    
    # ==================== CHAT HISTORY METHODS ====================
    
    def save_chat_message(self, user_ip: str, user_message: str, bot_response: str, 
                         session_id: str = None, test_context: Dict = None, 
                         embedding: List[float] = None) -> bool:
        """
        Save chat message to Supabase
        
        Args:
            user_ip: User's IP address
            user_message: User's question
            bot_response: Bot's answer
            session_id: Optional session identifier
            test_context: Optional test result context
            embedding: Optional vector embedding (1024 dimensions)
            
        Returns:
            bool: True if save successful
        """
        try:
            data = {
                'user_ip': user_ip,
                'user_message': user_message,
                'bot_response': bot_response,
                'timestamp': datetime.now().isoformat()
            }
            
            if session_id:
                data['session_id'] = session_id
            
            if test_context:
                data['test_context'] = json.dumps(test_context)
            
            if embedding:
                data['embedding'] = embedding
            
            result = self.client.table('chat_history').insert(data).execute()
            print(f"✅ Saved chat to Supabase (ID: {result.data[0]['id']})")
            return True
            
        except Exception as e:
            print(f"❌ Error saving chat: {e}")
            return False
    
    def get_user_chat_history(self, user_ip: str, limit: int = 10) -> List[Dict]:
        """
        Get recent chat history for a specific user
        
        Args:
            user_ip: User's IP address
            limit: Number of recent chats to return
            
        Returns:
            List of chat messages
        """
        try:
            result = self.client.table('chat_history')\
                .select('*')\
                .eq('user_ip', user_ip)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ Error fetching chat history: {e}")
            return []
    
    def search_similar_chats(self, query_embedding: List[float], 
                            match_threshold: float = 0.7, 
                            limit: int = 5) -> List[Dict]:
        """
        Search for similar chat conversations using vector similarity
        
        Args:
            query_embedding: Query vector (1024 dimensions)
            match_threshold: Minimum similarity score (0-1)
            limit: Number of results to return
            
        Returns:
            List of similar chat messages with similarity scores
        """
        try:
            result = self.client.rpc(
                'match_chat_history',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': match_threshold,
                    'match_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"⚠️ Chat vector search not available: {e}")
            return []
    
    def get_all_chat_history(self, limit: int = 50) -> List[Dict]:
        """
        Get all recent chat history (for analytics)
        
        Args:
            limit: Number of recent chats to return
            
        Returns:
            List of all chat messages
        """
        try:
            result = self.client.table('chat_history')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ Error fetching all chat history: {e}")
            return []
    
    def get_chat_statistics(self) -> Dict:
        """
        Get statistics about chat usage
        
        Returns:
            Dictionary with chat statistics
        """
        try:
            result = self.client.table('chat_history')\
                .select('id, user_ip, timestamp')\
                .execute()
            
            if not result.data:
                return {
                    'total_chats': 0,
                    'unique_users': 0
                }
            
            data = result.data
            unique_ips = set(d['user_ip'] for d in data)
            
            return {
                'total_chats': len(data),
                'unique_users': len(unique_ips)
            }
            
        except Exception as e:
            print(f"❌ Error getting chat statistics: {e}")
            return {}

