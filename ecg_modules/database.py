"""
Database module for ECG analysis results
Now uses PostgreSQL for production-grade thread-safe storage
"""

# Import PostgreSQL implementation
from ecg_modules.database_postgres import get_db, ECGDatabasePostgres

# Re-export for backward compatibility
__all__ = ['get_db', 'ECGDatabase']

# Alias for backward compatibility
ECGDatabase = ECGDatabasePostgres
