from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, SQLModel, create_engine, select

from .models import AnchorStory, EstimationSnapshot, Factor, Sector, SprintMetric


class Repository:
    def __init__(self, database_url: str = "sqlite:///estimator.db"):
        self.engine = create_engine(database_url, echo=False)
        self.create_db_and_tables()

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    # Sector operations
    def add_sector(self, sector: Sector) -> Sector:
        with self.get_session() as session:
            session.add(sector)
            session.commit()
            session.refresh(sector)
            return sector

    def get_sector(self, sector_id: UUID) -> Optional[Sector]:
        with self.get_session() as session:
            return session.get(Sector, sector_id)

    def get_all_sectors(self) -> List[Sector]:
        with self.get_session() as session:
            statement = select(Sector)
            return session.exec(statement).all()

    def update_sector(self, sector: Sector) -> Sector:
        with self.get_session() as session:
            session.add(sector)
            session.commit()
            session.refresh(sector)
            return sector

    def delete_sector(self, sector_id: UUID):
        with self.get_session() as session:
            sector = session.get(Sector, sector_id)
            if sector:
                session.delete(sector)
                session.commit()

    # Factor operations
    def add_factor(self, factor: Factor) -> Factor:
        with self.get_session() as session:
            session.add(factor)
            session.commit()
            session.refresh(factor)
            return factor

    def get_factors_by_sector(self, sector_id: UUID) -> List[Factor]:
        with self.get_session() as session:
            statement = select(Factor).where(Factor.sector_id == sector_id)
            return session.exec(statement).all()

    def update_factor(self, factor: Factor) -> Factor:
        with self.get_session() as session:
            session.add(factor)
            session.commit()
            session.refresh(factor)
            return factor

    def delete_factor(self, factor_id: UUID):
        with self.get_session() as session:
            factor = session.get(Factor, factor_id)
            if factor:
                session.delete(factor)
                session.commit()

    # AnchorStory operations
    def add_anchor_story(self, story: AnchorStory) -> AnchorStory:
        with self.get_session() as session:
            session.add(story)
            session.commit()
            session.refresh(story)
            return story

    def get_anchor_stories_by_sector(self, sector_id: UUID) -> List[AnchorStory]:
        with self.get_session() as session:
            statement = select(AnchorStory).where(AnchorStory.sector_id == sector_id)
            return session.exec(statement).all()

    def update_anchor_story(self, story: AnchorStory) -> AnchorStory:
        with self.get_session() as session:
            session.add(story)
            session.commit()
            session.refresh(story)
            return story

    def delete_anchor_story(self, story_id: UUID):
        with self.get_session() as session:
            story = session.get(AnchorStory, story_id)
            if story:
                session.delete(story)
                session.commit()

    # SprintMetric operations
    def add_sprint_metric(self, metric: SprintMetric) -> SprintMetric:
        with self.get_session() as session:
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric

    def get_sprint_metrics_by_sector(self, sector_id: UUID) -> List[SprintMetric]:
        with self.get_session() as session:
            statement = select(SprintMetric).where(SprintMetric.sector_id == sector_id)
            return session.exec(statement).all()

    def update_sprint_metric(self, metric: SprintMetric) -> SprintMetric:
        with self.get_session() as session:
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric

    def delete_sprint_metric(self, metric_id: UUID):
        with self.get_session() as session:
            metric = session.get(SprintMetric, metric_id)
            if metric:
                session.delete(metric)
                session.commit()

    # EstimationSnapshot operations
    def add_estimation_snapshot(
        self, snapshot: EstimationSnapshot
    ) -> EstimationSnapshot:
        with self.get_session() as session:
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return snapshot

    def get_estimation_snapshots_by_sector(
        self, sector_id: UUID
    ) -> List[EstimationSnapshot]:
        with self.get_session() as session:
            statement = select(EstimationSnapshot).where(
                EstimationSnapshot.sector_id == sector_id
            )
            return session.exec(statement).all()

    def update_estimation_snapshot(
        self, snapshot: EstimationSnapshot
    ) -> EstimationSnapshot:
        with self.get_session() as session:
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return snapshot

    def delete_estimation_snapshot(self, snapshot_id: UUID):
        with self.get_session() as session:
            snapshot = session.get(EstimationSnapshot, snapshot_id)
            if snapshot:
                session.delete(snapshot)
                session.commit()
