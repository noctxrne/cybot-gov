import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from app.database.session import SessionLocal
from app.models.document import AuditLog

class AuditLogger:
    def __init__(self):
        self.db = SessionLocal()
    
    def log(self, 
            user_id: str, 
            action: str, 
            document_id: Optional[int] = None, 
            details: Optional[Dict[str, Any]] = None,
            request: Optional[Request] = None):
        """
        Log an audit event
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                document_id=document_id,
                details=details if details else {},
                ip_address=self._get_client_ip(request) if request else None,
                user_agent=self._get_user_agent(request) if request else None,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            print(f"Audit logging failed: {e}")
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address"""
        if not request:
            return None
        
        # Try multiple headers for IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0]
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else None
    
    def _get_user_agent(self, request: Request) -> Optional[str]:
        """Extract user agent"""
        if not request:
            return None
        
        return request.headers.get("User-Agent")
    
    def get_logs(self, 
                 user_id: Optional[str] = None,
                 action: Optional[str] = None,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 limit: int = 100):
        """
        Retrieve audit logs with filters
        """
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    def close(self):
        """Close database connection"""
        self.db.close()