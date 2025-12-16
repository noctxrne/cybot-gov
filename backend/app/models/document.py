from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    total_pages = Column(Integer)
    
    # Metadata
    source = Column(String(255))  # e.g., "IT Act 2000"
    section_number = Column(String(100))
    amendment_date = Column(DateTime)
    effective_date = Column(DateTime)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    # Versioning
    version = Column(Integer, default=1)
    previous_version_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # Audit
    uploaded_by = Column(String(100))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_by = Column(String(100))
    last_modified_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    previous_version = relationship("Document", remote_side=[id])
    audit_logs = relationship("AuditLog", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSON)  # ✅ CHANGED: was 'metadata'
    
    # Vector embedding reference
    vector_id = Column(String(255))
    
    document = relationship("Document", back_populates="chunks")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    user_id = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, VIEW
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    document = relationship("Document", back_populates="audit_logs")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255))
    
    role = Column(String(50), default="user")  # admin, editor, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))