import asyncio
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from . import models
from .core import settings
from .logging_config import log_info, log_error

class BackupManager:
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    async def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a backup of the database"""
        if not backup_name:
            backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            # In a real implementation, you would use pg_dump or similar for PostgreSQL
            # For this example, we'll simulate the process
            log_info(f"Starting backup: {backup_name}")
            
            # Create metadata file
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.utcnow().isoformat(),
                "tables": []
            }
            
            # Simulate backing up tables
            tables_to_backup = [
                "users", "slots", "slot_status", "slot_events", 
                "bookings", "payments", "notifications", "api_keys", "audit_logs"
            ]
            
            for table in tables_to_backup:
                metadata["tables"].append(table)
            
            # Save metadata
            metadata_path = backup_path / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            log_info(f"Backup completed: {backup_name}")
            return str(backup_path)
            
        except Exception as e:
            log_error(e, f"Backup failed: {backup_name}")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise e

    async def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        for backup_path in self.backup_dir.iterdir():
            if backup_path.is_dir():
                metadata_path = backup_path / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        backups.append(metadata)
                    except Exception as e:
                        log_error(e, f"Failed to read metadata for backup: {backup_path.name}")
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups

    async def restore_backup(self, backup_name: str) -> bool:
        """Restore a backup (simulated)"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")
        
        try:
            log_info(f"Starting restore: {backup_name}")
            # In a real implementation, you would restore the database from the backup
            # For this example, we'll just return True to simulate success
            log_info(f"Restore completed: {backup_name}")
            return True
        except Exception as e:
            log_error(e, f"Restore failed: {backup_name}")
            raise e

    async def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")
        
        try:
            shutil.rmtree(backup_path)
            log_info(f"Backup deleted: {backup_name}")
            return True
        except Exception as e:
            log_error(e, f"Failed to delete backup: {backup_name}")
            raise e

    async def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Delete backups older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for backup_path in self.backup_dir.iterdir():
            if backup_path.is_dir():
                metadata_path = backup_path / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        created_at = datetime.fromisoformat(metadata["created_at"])
                        
                        if created_at < cutoff_date:
                            await self.delete_backup(backup_path.name)
                            deleted_count += 1
                    except Exception as e:
                        log_error(e, f"Failed to process backup for cleanup: {backup_path.name}")
        
        log_info(f"Cleaned up {deleted_count} old backups")
        return deleted_count

class DataRetentionManager:
    def __init__(self):
        self.retention_policies = {
            "slot_events": 90,  # Keep for 90 days
            "audit_logs": 365,  # Keep for 1 year
            "notifications": 30,  # Keep for 30 days
        }

    async def apply_retention_policies(self, session: AsyncSession) -> Dict[str, int]:
        """Apply data retention policies to clean up old data"""
        results = {}
        
        for table, days in self.retention_policies.items():
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            try:
                # Delete old records
                delete_query = text(f"DELETE FROM {table} WHERE created_at < :cutoff_date")
                result = await session.execute(delete_query, {"cutoff_date": cutoff_date})
                await session.commit()
                
                deleted_count = result.rowcount
                results[table] = deleted_count
                log_info(f"Applied retention policy for {table}: deleted {deleted_count} records")
                
            except Exception as e:
                log_error(e, f"Failed to apply retention policy for {table}")
                results[table] = 0
        
        return results

    async def get_data_age_info(self, session: AsyncSession) -> Dict[str, Dict]:
        """Get information about data age in different tables"""
        age_info = {}
        
        for table in self.retention_policies.keys():
            try:
                # Get min and max dates
                min_max_query = text(f"""
                    SELECT MIN(created_at) as min_date, MAX(created_at) as max_date, COUNT(*) as total_count
                    FROM {table}
                """)
                
                result = await session.execute(min_max_query)
                row = result.fetchone()
                
                age_info[table] = {
                    "min_date": row.min_date.isoformat() if row.min_date else None,
                    "max_date": row.max_date.isoformat() if row.max_date else None,
                    "total_count": row.total_count
                }
                
            except Exception as e:
                log_error(e, f"Failed to get age info for {table}")
                age_info[table] = {"error": str(e)}
        
        return age_info

# Global instances
backup_manager = BackupManager()
retention_manager = DataRetentionManager()

# Background task to run retention policies
async def run_retention_policies():
    """Background task to periodically run data retention policies"""
    while True:
        try:
            async for session in get_session():
                results = await retention_manager.apply_retention_policies(session)
                log_info(f"Retention policies applied: {results}")
                break  # Only process with first session
        
        except Exception as e:
            log_error(e, "Failed to run retention policies")
        
        # Run every 24 hours
        await asyncio.sleep(24 * 3600)