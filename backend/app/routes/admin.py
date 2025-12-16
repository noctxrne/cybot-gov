from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
import os
import shutil
from typing import List
import uuid
from datetime import datetime

from app.database.session import get_db
from app.models.document import Document, AuditLog, User
from app.services.pdf_processor import PDFProcessor
from app.utils.audit_logger import AuditLogger
from app.utils.validators import validate_file, validate_document
from app.config import settings

from app.routes.auth import get_current_user, get_current_active_user


router = APIRouter(prefix="/admin", tags=["admin"])
audit_logger = AuditLogger()

# Document locking mechanism for concurrent edits
document_locks = {}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = "",
    document_type: str = "cyber_law",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process document with atomic transaction"""
    
    # Validate user role
    if current_user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Validate file
    validation_result = validate_file(file, settings.MAX_FILE_SIZE, settings.ALLOWED_EXTENSIONS)
    if not validation_result["valid"]:
        raise HTTPException(status_code=400, detail=validation_result["message"])
    
    # Create transaction for atomic operation
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Save file atomically
        temp_path = file_path + ".tmp"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        os.rename(temp_path, file_path)
        
        # Create document record
        db_document = Document(
            filename=file.filename,
            file_path=file_path,
            document_type=document_type,
            title=file.filename,
            source=source,
            uploaded_by=current_user.username,
            is_processed=False
        )
        
        db.add(db_document)
        db.flush()  # Get ID without committing
        
        # Log audit
        audit_logger.log(
            user_id=current_user.username,
            action="UPLOAD",
            document_id=db_document.id,
            details={"filename": file.filename, "source": source}
        )
        
        # Process in background
        if background_tasks:
            background_tasks.add_task(
                process_document_background,
                db_document.id,
                file_path,
                {
                    "source": source,
                    "document_type": document_type,
                    "uploaded_by": current_user.username,
                    "document_id": db_document.id
                }
            )
        
        # Commit transaction
        db.commit()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Document uploaded successfully. Processing started.",
                "document_id": db_document.id,
                "filename": file.filename
            }
        )
        
    except Exception as e:
        db.rollback()
        # Cleanup file if document creation failed
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_document_background(document_id: int, file_path: str, metadata: dict):
    """Background task for document processing"""
    from app.database.session import SessionLocal
    db = SessionLocal()
    
    try:
        # Process PDF
        processor = PDFProcessor(settings)
        result = processor.process_document(file_path, metadata)
        
        # Update document status
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            if result["success"]:
                document.is_processed = True
                document.total_pages = result.get("total_chunks", 0)
                document.summary = f"Processed {result['total_sections']} sections"
            else:
                document.processing_error = result.get("error", "Unknown error")
            
            db.commit()
            
            # Log completion
            audit_logger.log(
                user_id=metadata["uploaded_by"],
                action="PROCESS_COMPLETE" if result["success"] else "PROCESS_FAILED",
                document_id=document_id,
                details=result
            )
    except Exception as e:
        print(f"Background processing error: {e}")
    finally:
        db.close()

@router.put("/document/{document_id}")
async def update_document(
    document_id: int,
    updates: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update document with optimistic concurrency control"""
    
    # Check permissions
    if current_user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Implement optimistic locking
    try:
        # Get document with lock check
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check for concurrent modification
        if document.version != updates.get("expected_version", document.version):
            raise HTTPException(
                status_code=409,
                detail="Document has been modified by another user. Please refresh and try again."
            )
        
        # Create new version
        new_version = Document(
            filename=document.filename,
            file_path=document.file_path,
            document_type=document.document_type,
            title=updates.get("title", document.title),
            summary=updates.get("summary", document.summary),
            source=updates.get("source", document.source),
            previous_version_id=document.id,
            version=document.version + 1,
            uploaded_by=current_user.username,
            last_modified_by=current_user.username
        )
        
        db.add(new_version)
        db.flush()
        
        # Archive old version
        document.is_active = False
        
        # Log audit
        audit_logger.log(
            user_id=current_user.username,
            action="UPDATE",
            document_id=document_id,
            details={
                "old_version": document.version,
                "new_version": new_version.version,
                "changes": updates
            }
        )
        
        db.commit()
        
        return {
            "message": "Document updated successfully",
            "new_document_id": new_version.id,
            "version": new_version.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.get("/audit-logs")
async def get_audit_logs(
    start_date: datetime = None,
    end_date: datetime = None,
    user_id: str = None,
    action: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs with filters"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(AuditLog)
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "timestamp": log.timestamp,
                "details": log.details,
                "ip_address": log.ip_address
            }
            for log in logs
        ]
    }
