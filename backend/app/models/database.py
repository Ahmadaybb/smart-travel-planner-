from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_query = Column(Text, nullable=False)
    answer     = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ToolCallLog(Base):
    __tablename__ = "tool_call_logs"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id      = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False)
    tool_name   = Column(String, nullable=False)
    tool_input  = Column(Text, nullable=True)
    tool_output = Column(Text, nullable=True)
    called_at   = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination = Column(String, nullable=False)
    content   = Column(Text, nullable=False)
    embedding = Column(Vector(384))  # sentence-transformers dimension
    source    = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)