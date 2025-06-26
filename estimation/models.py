from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class EstimationMode(str, Enum):
    BASELINE = "baseline"
    GREENFIELD = "greenfield"


class Sector(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    estimation_mode: EstimationMode
    anchor_effort_pm: Optional[float] = None

    # Relationships
    factors: List["Factor"] = Relationship(back_populates="sector")
    anchor_stories: List["AnchorStory"] = Relationship(back_populates="sector")
    sprint_metrics: List["SprintMetric"] = Relationship(back_populates="sector")
    estimation_snapshots: List["EstimationSnapshot"] = Relationship(
        back_populates="sector"
    )


class Factor(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    sector_id: UUID = Field(foreign_key="sector.id")
    name: str
    weight_pct: float = Field(ge=0, le=100)
    baseline_score: float = Field(ge=1, le=10)
    target_score: float = Field(ge=1, le=10)

    # Relationships
    sector: Sector = Relationship(back_populates="factors")


class AnchorStory(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    sector_id: UUID = Field(foreign_key="sector.id")
    title: str
    story_points: int = Field(ge=1)
    description: Optional[str] = None
    is_anchor: bool = True

    # Relationships
    sector: Sector = Relationship(back_populates="anchor_stories")


class SprintMetric(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    sector_id: UUID = Field(foreign_key="sector.id")
    end_date: date
    story_points: float = Field(ge=0)
    person_days: float = Field(ge=0)

    # Relationships
    sector: Sector = Relationship(back_populates="sprint_metrics")


class EstimationSnapshot(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    sector_id: UUID = Field(foreign_key="sector.id")
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    sp_total: float = Field(ge=0)
    effort_pm_est: float = Field(ge=0)
    p50_weeks: float = Field(ge=0)
    p80_weeks: float = Field(ge=0)
    algo_version: str = "0.1.0"

    # Relationships
    sector: Sector = Relationship(back_populates="estimation_snapshots")
