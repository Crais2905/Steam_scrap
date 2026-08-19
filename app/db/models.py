from datetime import datetime
from typing import Optional, List

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, Mapped, mapped_column


Base = declarative_base()


class Runs(Base):
    __tablename__ = 'runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    method_type: Mapped[str] = mapped_column(String, nullable=False)
    request_data: Mapped[str] = mapped_column(String, nullable=False)
    response_data: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))