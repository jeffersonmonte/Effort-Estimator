from datetime import date
from uuid import uuid4

from estimation.models import EstimationMode, Factor, Sector, SprintMetric
from estimation.repository import Repository
from estimation.seed import seed_data


class TestRepositoryExtended:
    def test_update_sector(self):
        repository = Repository("sqlite:///:memory:")

        sector = Sector(
            name="Original Name",
            estimation_mode=EstimationMode.BASELINE,
            anchor_effort_pm=5.0,
        )
        saved_sector = repository.add_sector(sector)

        # Atualizar o setor
        saved_sector.name = "Updated Name"
        saved_sector.anchor_effort_pm = 7.0

        updated_sector = repository.update_sector(saved_sector)

        assert updated_sector.name == "Updated Name"
        assert updated_sector.anchor_effort_pm == 7.0

    def test_delete_sector(self):
        repository = Repository("sqlite:///:memory:")

        sector = Sector(name="Test Sector", estimation_mode=EstimationMode.BASELINE)
        saved_sector = repository.add_sector(sector)

        # Verificar que o setor existe
        retrieved_sector = repository.get_sector(saved_sector.id)
        assert retrieved_sector is not None

        # Deletar o setor
        repository.delete_sector(saved_sector.id)

        # Verificar que o setor foi deletado
        deleted_sector = repository.get_sector(saved_sector.id)
        assert deleted_sector is None

    def test_delete_nonexistent_sector(self):
        repository = Repository("sqlite:///:memory:")

        # Tentar deletar um setor que não existe (não deve gerar erro)
        repository.delete_sector(uuid4())

    def test_update_factor(self):
        repository = Repository("sqlite:///:memory:")

        sector = Sector(name="Test Sector", estimation_mode=EstimationMode.BASELINE)
        saved_sector = repository.add_sector(sector)

        factor = Factor(
            sector_id=saved_sector.id,
            name="Original Factor",
            weight_pct=30.0,
            baseline_score=5.0,
            target_score=7.0,
        )
        saved_factor = repository.add_factor(factor)

        # Atualizar o fator
        saved_factor.name = "Updated Factor"
        saved_factor.weight_pct = 50.0

        updated_factor = repository.update_factor(saved_factor)

        assert updated_factor.name == "Updated Factor"
        assert updated_factor.weight_pct == 50.0

    def test_delete_factor(self):
        repository = Repository("sqlite:///:memory:")

        sector = Sector(name="Test Sector", estimation_mode=EstimationMode.BASELINE)
        saved_sector = repository.add_sector(sector)

        factor = Factor(
            sector_id=saved_sector.id,
            name="Test Factor",
            weight_pct=30.0,
            baseline_score=5.0,
            target_score=7.0,
        )
        saved_factor = repository.add_factor(factor)

        # Verificar que o fator existe
        factors = repository.get_factors_by_sector(saved_sector.id)
        assert len(factors) == 1

        # Deletar o fator
        repository.delete_factor(saved_factor.id)

        # Verificar que o fator foi deletado
        factors = repository.get_factors_by_sector(saved_sector.id)
        assert len(factors) == 0

    def test_delete_nonexistent_factor(self):
        repository = Repository("sqlite:///:memory:")

        # Tentar deletar um fator que não existe (não deve gerar erro)
        repository.delete_factor(uuid4())

    def test_update_sprint_metric(self):
        repository = Repository("sqlite:///:memory:")

        sector = Sector(name="Test Sector", estimation_mode=EstimationMode.BASELINE)
        saved_sector = repository.add_sector(sector)

        metric = SprintMetric(
            sector_id=saved_sector.id,
            end_date=date(2025, 1, 15),
            story_points=10.0,
            person_days=20.0,
        )
        saved_metric = repository.add_sprint_metric(metric)

        # Atualizar a métrica
        saved_metric.story_points = 15.0
        saved_metric.person_days = 25.0

        updated_metric = repository.update_sprint_metric(saved_metric)

        assert updated_metric.story_points == 15.0
        assert updated_metric.person_days == 25.0

    def test_delete_sprint_metric(self):
        repository = Repository("sqlite:///:memory:")

        sector = Sector(name="Test Sector", estimation_mode=EstimationMode.BASELINE)
        saved_sector = repository.add_sector(sector)

        metric = SprintMetric(
            sector_id=saved_sector.id,
            end_date=date(2025, 1, 15),
            story_points=10.0,
            person_days=20.0,
        )
        saved_metric = repository.add_sprint_metric(metric)

        # Verificar que a métrica existe
        metrics = repository.get_sprint_metrics_by_sector(saved_sector.id)
        assert len(metrics) == 1

        # Deletar a métrica
        repository.delete_sprint_metric(saved_metric.id)

        # Verificar que a métrica foi deletada
        metrics = repository.get_sprint_metrics_by_sector(saved_sector.id)
        assert len(metrics) == 0

    def test_delete_nonexistent_sprint_metric(self):
        repository = Repository("sqlite:///:memory:")

        # Tentar deletar uma métrica que não existe (não deve gerar erro)
        repository.delete_sprint_metric(uuid4())

    def test_anchor_story_operations(self):
        repository = Repository("sqlite:///:memory:")

        sector = Sector(name="Test Sector", estimation_mode=EstimationMode.GREENFIELD)
        saved_sector = repository.add_sector(sector)

        from estimation.models import AnchorStory

        story = AnchorStory(
            sector_id=saved_sector.id,
            title="Test Story",
            story_points=3,
            description="Test description",
            is_anchor=True,
        )
        saved_story = repository.add_anchor_story(story)

        # Verificar que a história foi salva
        stories = repository.get_anchor_stories_by_sector(saved_sector.id)
        assert len(stories) == 1
        assert stories[0].title == "Test Story"

        # Atualizar a história
        saved_story.title = "Updated Story"
        updated_story = repository.update_anchor_story(saved_story)
        assert updated_story.title == "Updated Story"

        # Deletar a história
        repository.delete_anchor_story(saved_story.id)
        stories = repository.get_anchor_stories_by_sector(saved_sector.id)
        assert len(stories) == 0

    def test_estimation_snapshot_operations(self):
        repository = Repository("sqlite:///:memory:")

        sector = Sector(name="Test Sector", estimation_mode=EstimationMode.BASELINE)
        saved_sector = repository.add_sector(sector)

        from estimation.models import EstimationSnapshot

        snapshot = EstimationSnapshot(
            sector_id=saved_sector.id,
            sp_total=50.0,
            effort_pm_est=4.5,
            p50_weeks=12.0,
            p80_weeks=16.0,
        )
        saved_snapshot = repository.add_estimation_snapshot(snapshot)

        # Verificar que o snapshot foi salvo
        snapshots = repository.get_estimation_snapshots_by_sector(saved_sector.id)
        assert len(snapshots) == 1
        assert snapshots[0].sp_total == 50.0

        # Atualizar o snapshot
        saved_snapshot.sp_total = 60.0
        updated_snapshot = repository.update_estimation_snapshot(saved_snapshot)
        assert updated_snapshot.sp_total == 60.0

        # Deletar o snapshot
        repository.delete_estimation_snapshot(saved_snapshot.id)
        snapshots = repository.get_estimation_snapshots_by_sector(saved_sector.id)
        assert len(snapshots) == 0


class TestSeedData:
    def test_seed_data_creation(self):
        repository = Repository("sqlite:///:memory:")

        # Executar seed
        seed_data(repository)

        # Verificar que os dados foram criados
        sectors = repository.get_all_sectors()
        assert len(sectors) == 2

        # Verificar setor Compras
        compras_sector = next((s for s in sectors if s.name == "Compras"), None)
        assert compras_sector is not None
        assert compras_sector.estimation_mode == EstimationMode.BASELINE
        assert compras_sector.anchor_effort_pm == 6.0

        # Verificar fatores do setor Compras
        compras_factors = repository.get_factors_by_sector(compras_sector.id)
        assert len(compras_factors) == 5

        # Verificar setor Estoque
        estoque_sector = next((s for s in sectors if s.name == "Estoque"), None)
        assert estoque_sector is not None
        assert estoque_sector.estimation_mode == EstimationMode.GREENFIELD
        assert estoque_sector.anchor_effort_pm is None

        # Verificar histórias âncora do setor Estoque
        estoque_stories = repository.get_anchor_stories_by_sector(estoque_sector.id)
        assert len(estoque_stories) == 3

        # Verificar métricas de sprint
        compras_metrics = repository.get_sprint_metrics_by_sector(compras_sector.id)
        estoque_metrics = repository.get_sprint_metrics_by_sector(estoque_sector.id)
        assert len(compras_metrics) == 4
        assert len(estoque_metrics) == 4

        # Verificar snapshots
        compras_snapshots = repository.get_estimation_snapshots_by_sector(
            compras_sector.id
        )
        estoque_snapshots = repository.get_estimation_snapshots_by_sector(
            estoque_sector.id
        )
        assert len(compras_snapshots) == 1
        assert len(estoque_snapshots) == 1
