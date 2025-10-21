from fastapi import APIRouter, Depends, HTTPException
from ..security import get_current_admin_user
from .. import backup
from ..db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

# Access the managers from the imported backup module
backup_manager = backup.backup_manager
retention_manager = backup.retention_manager

router = APIRouter(prefix="/backup")

@router.post("/create")
async def create_backup(current_user = Depends(get_current_admin_user)):
    """Create a new backup"""
    try:
        backup_path = await backup_manager.create_backup()
        return {"message": "Backup created successfully", "backup_path": backup_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")

@router.get("/")
async def list_backups(current_user = Depends(get_current_admin_user)):
    """List all available backups"""
    try:
        backups = await backup_manager.list_backups()
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")

@router.post("/restore/{backup_name}")
async def restore_backup(backup_name: str, current_user = Depends(get_current_admin_user)):
    """Restore from a backup"""
    try:
        success = await backup_manager.restore_backup(backup_name)
        if success:
            return {"message": f"Backup {backup_name} restored successfully"}
        else:
            raise HTTPException(status_code=500, detail="Restore failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore backup: {str(e)}")

@router.delete("/{backup_name}")
async def delete_backup(backup_name: str, current_user = Depends(get_current_admin_user)):
    """Delete a backup"""
    try:
        success = await backup_manager.delete_backup(backup_name)
        if success:
            return {"message": f"Backup {backup_name} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Delete failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")

@router.post("/cleanup")
async def cleanup_backups(days_to_keep: int = 30, current_user = Depends(get_current_admin_user)):
    """Clean up old backups"""
    try:
        deleted_count = await backup_manager.cleanup_old_backups(days_to_keep)
        return {"message": f"Cleaned up {deleted_count} old backups"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup backups: {str(e)}")

@router.post("/retention/apply")
async def apply_retention_policies(current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Apply data retention policies manually"""
    try:
        results = await retention_manager.apply_retention_policies(session)
        return {"message": "Retention policies applied successfully", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply retention policies: {str(e)}")

@router.get("/retention/info")
async def get_retention_info(current_user = Depends(get_current_admin_user), session: AsyncSession = Depends(get_session)):
    """Get information about data age in different tables"""
    try:
        info = await retention_manager.get_data_age_info(session)
        return {"retention_info": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retention info: {str(e)}")