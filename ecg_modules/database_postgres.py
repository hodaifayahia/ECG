"""
PostgreSQL Database Module for ECG Analysis
Production-grade implementation with connection pooling and thread safety
"""

import psycopg2
from psycopg2 import pool, extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json
import os
from datetime import datetime
from contextlib import contextmanager
import threading

class ECGDatabasePostgres:
    """
    Production-grade PostgreSQL database for ECG analysis results
    
    Features:
    - Connection pooling for performance
    - Thread-safe operations
    - Automatic schema creation
    - Prepared statements for security
    - Transaction management
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for connection pool"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 host='localhost',
                 port=5432,
                 database='ecg_analysis',
                 user='postgres',
                 password='postgres',
                 min_connections=2,
                 max_connections=10):
        """
        Initialize PostgreSQL connection pool
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        
        # Create database if it doesn't exist
        self._create_database_if_not_exists()
        
        # Create connection pool
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            print(f"✓ PostgreSQL connection pool created (min={min_connections}, max={max_connections})")
        except Exception as e:
            print(f"✗ Failed to create connection pool: {e}")
            raise
        
        # Create tables
        self._create_tables()
        
        self._initialized = True
    
    def _create_database_if_not_exists(self):
        """Create database if it doesn't exist"""
        try:
            # Connect to postgres database to create our database
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database='postgres',
                user=self.user,
                password=self.password
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.database,)
            )
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f'CREATE DATABASE {self.database}')
                print(f"✓ Created database '{self.database}'")
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not check/create database: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Automatically returns connection to pool
        """
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit=True):
        """
        Context manager for database cursor with automatic commit/rollback
        
        Args:
            commit: Whether to commit on success
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ecg_analyses (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(500) NOT NULL,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            feature_set VARCHAR(50) DEFAULT 'standard',
            file_size INTEGER,
            processing_time_ms FLOAT,
            
            -- Individual metric columns for fast queries
            heart_rate_bpm FLOAT,
            sdnn_ms FLOAT,
            rmssd_ms FLOAT,
            pnn50_percent FLOAT,
            pnn20_percent FLOAT,
            sd1_ms FLOAT,
            sd2_ms FLOAT,
            lf_power FLOAT,
            hf_power FLOAT,
            lf_hf_ratio FLOAT,
            
            -- JSON field for full metrics and extensibility
            raw_metrics JSONB,
            
            -- Status tracking
            status VARCHAR(50) DEFAULT 'completed',
            error_message TEXT,
            
            -- Indexes for common queries
            CONSTRAINT unique_filename_timestamp UNIQUE(filename, upload_timestamp)
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_upload_timestamp ON ecg_analyses(upload_timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_filename ON ecg_analyses(filename);
        CREATE INDEX IF NOT EXISTS idx_feature_set ON ecg_analyses(feature_set);
        CREATE INDEX IF NOT EXISTS idx_heart_rate ON ecg_analyses(heart_rate_bpm);
        CREATE INDEX IF NOT EXISTS idx_raw_metrics_gin ON ecg_analyses USING GIN(raw_metrics);
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(create_table_sql)
            print("✓ PostgreSQL tables and indexes created")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            raise
    
    def save_result(self, filename, metrics, feature_set='standard', 
                   file_size=None, processing_time_ms=None, status='completed'):
        """
        Save ECG analysis result to database
        
        Args:
            filename: Name of the PDF file
            metrics: Dictionary of computed metrics
            feature_set: Feature set used (basic/standard/complete)
            file_size: Size of uploaded file in bytes
            processing_time_ms: Processing time in milliseconds
            status: Status of analysis
            
        Returns:
            int: ID of inserted record
        """
        insert_sql = """
        INSERT INTO ecg_analyses (
            filename, feature_set, file_size, processing_time_ms,
            heart_rate_bpm, sdnn_ms, rmssd_ms, pnn50_percent, pnn20_percent,
            sd1_ms, sd2_ms, lf_power, hf_power, lf_hf_ratio,
            raw_metrics, status
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s
        ) RETURNING id
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(insert_sql, (
                    filename,
                    feature_set,
                    file_size,
                    processing_time_ms,
                    metrics.get('heart_rate_bpm'),
                    metrics.get('sdnn_ms'),
                    metrics.get('rmssd_ms'),
                    metrics.get('pnn50_percent'),
                    metrics.get('pnn20_percent'),
                    metrics.get('sd1_ms'),
                    metrics.get('sd2_ms'),
                    metrics.get('lf_power'),
                    metrics.get('hf_power'),
                    metrics.get('lf_hf_ratio'),
                    json.dumps(metrics),
                    status
                ))
                result = cursor.fetchone()
                record_id = result['id']
                print(f"✓ Saved record ID {record_id} for {filename}")
                return record_id
        except Exception as e:
            print(f"✗ Error saving result: {e}")
            raise
    
    def get_all_records(self, limit=None, offset=0):
        """
        Retrieve all analysis records
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            list: List of dictionaries with analysis results
        """
        query = """
        SELECT 
            id, filename, upload_timestamp, feature_set,
            file_size, processing_time_ms,
            heart_rate_bpm, sdnn_ms, rmssd_ms, pnn50_percent, pnn20_percent,
            sd1_ms, sd2_ms, lf_power, hf_power, lf_hf_ratio,
            raw_metrics, status
        FROM ecg_analyses
        ORDER BY upload_timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute(query)
                records = cursor.fetchall()
                
                # Convert to list of dicts and parse timestamps
                result = []
                for record in records:
                    record_dict = dict(record)
                    # Convert timestamp to ISO format string
                    if record_dict['upload_timestamp']:
                        record_dict['timestamp'] = record_dict['upload_timestamp'].isoformat()
                    # Parse raw_metrics JSON
                    if isinstance(record_dict['raw_metrics'], str):
                        record_dict['metrics'] = json.loads(record_dict['raw_metrics'])
                    else:
                        record_dict['metrics'] = record_dict['raw_metrics']
                    result.append(record_dict)
                
                return result
        except Exception as e:
            print(f"✗ Error retrieving records: {e}")
            raise
    
    def get_by_id(self, record_id):
        """Get a specific record by ID"""
        query = "SELECT * FROM ecg_analyses WHERE id = %s"
        
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute(query, (record_id,))
                record = cursor.fetchone()
                if record:
                    record_dict = dict(record)
                    if record_dict['upload_timestamp']:
                        record_dict['timestamp'] = record_dict['upload_timestamp'].isoformat()
                    return record_dict
                return None
        except Exception as e:
            print(f"✗ Error retrieving record: {e}")
            raise
    
    def get_statistics(self):
        """
        Get database statistics
        
        Returns:
            dict: Statistics including counts and averages
        """
        query = """
        SELECT 
            COUNT(*) as total_analyses,
            COUNT(DISTINCT filename) as unique_files,
            AVG(heart_rate_bpm) as avg_heart_rate,
            AVG(sdnn_ms) as avg_sdnn,
            AVG(rmssd_ms) as avg_rmssd,
            AVG(processing_time_ms) as avg_processing_time,
            MIN(upload_timestamp) as first_upload,
            MAX(upload_timestamp) as last_upload
        FROM ecg_analyses
        """
        
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                stats = dict(result)
                
                # Convert timestamps to ISO format
                if stats['first_upload']:
                    stats['first_upload'] = stats['first_upload'].isoformat()
                if stats['last_upload']:
                    stats['last_upload'] = stats['last_upload'].isoformat()
                
                return stats
        except Exception as e:
            print(f"✗ Error getting statistics: {e}")
            raise
    
    def delete_record(self, record_id):
        """Delete a specific record"""
        query = "DELETE FROM ecg_analyses WHERE id = %s RETURNING id"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (record_id,))
                result = cursor.fetchone()
                if result:
                    print(f"✓ Deleted record ID {record_id}")
                    return True
                return False
        except Exception as e:
            print(f"✗ Error deleting record: {e}")
            raise
    
    def clear_all(self):
        """Clear all records (use with caution!)"""
        query = "TRUNCATE TABLE ecg_analyses RESTART IDENTITY"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query)
                print("✓ All records cleared")
        except Exception as e:
            print(f"✗ Error clearing records: {e}")
            raise
    
    def export_for_ml(self):
        """
        Export data in format suitable for machine learning
        
        Returns:
            tuple: (feature_matrix, labels, feature_names)
        """
        query = """
        SELECT 
            heart_rate_bpm, sdnn_ms, rmssd_ms, pnn50_percent, pnn20_percent,
            sd1_ms, sd2_ms, lf_power, hf_power, lf_hf_ratio
        FROM ecg_analyses
        WHERE status = 'completed'
        """
        
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute(query)
                records = cursor.fetchall()
                
                import numpy as np
                
                feature_names = [
                    'heart_rate_bpm', 'sdnn_ms', 'rmssd_ms', 'pnn50_percent', 'pnn20_percent',
                    'sd1_ms', 'sd2_ms', 'lf_power', 'hf_power', 'lf_hf_ratio'
                ]
                
                # Convert to numpy array
                data = []
                for record in records:
                    row = [record[name] for name in feature_names]
                    data.append(row)
                
                feature_matrix = np.array(data)
                
                return feature_matrix, feature_names
        except Exception as e:
            print(f"✗ Error exporting for ML: {e}")
            raise
    
    def close(self):
        """Close all connections in the pool"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
            print("✓ PostgreSQL connection pool closed")


# Singleton instance - use environment variables if available
def get_db():
    """
    Get database instance with configuration from environment variables
    
    Environment variables:
    - DB_HOST: Database host (default: localhost)
    - DB_PORT: Database port (default: 5432)
    - DB_NAME: Database name (default: ecg_analysis)
    - DB_USER: Database user (default: postgres)
    - DB_PASSWORD: Database password (default: postgres)
    """
    return ECGDatabasePostgres(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'ecg_analysis'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        min_connections=2,
        max_connections=10
    )
