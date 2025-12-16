from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from app.database.session import get_db
from app.services.rag_service import HybridRAGService
from app.utils.audit_logger import AuditLogger
from app.config import settings
from app.routes.auth import get_current_user
from app.models.document import User, AuditLog

router = APIRouter(prefix="/chat", tags=["chat"])
rag_service = HybridRAGService(settings)
audit_logger = AuditLogger()

@router.post("/query")
async def query_chatbot(
    query_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handle chatbot queries with audit logging
    """
    try:
        query = query_data.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Get response from RAG service
        response = rag_service.query(query)
        
        # Log the query and response (without sensitive info)
        audit_logger.log(
            user_id=current_user.username if current_user else "anonymous",
            action="CHAT_QUERY",
            document_id=None,
            details={
                "query": query[:500],  # Limit length
                "intent": response.get("intent", "unknown"),
                "confidence": response.get("confidence", 0),
                "response_length": len(response.get("answer", ""))
            }
        )
        
        return response
        
    except Exception as e:
        audit_logger.log(
            user_id=current_user.username if current_user else "anonymous",
            action="CHAT_ERROR",
            details={"error": str(e), "query": query_data.get("query", "")[:100]}
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get chat history for the current user (admins can see all)
    """
    try:
        query = db.query(AuditLog).filter(AuditLog.action == "CHAT_QUERY")
        
        # Regular users only see their own history
        if current_user.role not in ["admin", "editor"]:
            query = query.filter(AuditLog.user_id == current_user.username)
        
        history = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return {
            "history": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp,
                    "query": log.details.get("query", ""),
                    "intent": log.details.get("intent", ""),
                    "confidence": log.details.get("confidence", 0)
                }
                for log in history
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
