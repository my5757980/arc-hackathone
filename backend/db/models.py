"""SQLAlchemy models for AgentFlow."""
import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, BigInteger, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    to_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_usdc: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(66), nullable=True)
    arc_block_number: Mapped[int] = mapped_column(BigInteger, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=True)
    task_input: Mapped[str] = mapped_column(Text, nullable=True)
    task_result: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AgentWallet(Base):
    __tablename__ = "agent_wallets"

    agent_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    circle_wallet_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(42), nullable=False)
    balance_usdc: Mapped[float] = mapped_column(Numeric(18, 8), default=10.0)
