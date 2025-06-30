from datetime import date
from uuid import uuid4

import pytest

from estimation.models import (
    EstimationMode,
    EstimationSnapshot,
    Factor,
    Sector,
    SprintMetric,
)
from estimation.repository import Repository
from estimation.services import (
    ComplexityScorer,
    EstimationService,
    FibonacciRound,
    MonteCarloService,
    calculate_days_per_sp,
    convert_to_story_points,
)


@pytest.fixture
def repository():
    """Fixture para criar um repositório em memória para testes."""
    return Repository("sqlite:///:memory:")


@pytest.fixture
def sample_sector(repository):
    """Fixture para criar um setor de exemplo."""
    sector = Sector(
        name="Test Sector",
        estimation_mode=EstimationMode.BASELINE,
        anchor_effort_pm=5.0,
    )
    return repository.add_sector(sector)


@pytest.fixture
def sample_factors(repository, sample_sector):
    """Fixture para criar fatores de exemplo."""
    factors = [
        Factor(
            sector_id=sample_sector.id,
            name="Integration",
            weight_pct=40.0,
            baseline_score=5.0,
            target_score=7.0,
        ),
        Factor(
            sector_id=sample_sector.id,
            name="Business Rules",
            weight_pct=60.0,
            baseline_score=6.0,
            target_score=8.0,
        ),
    ]

    return [repository.add_factor(factor) for factor in factors]


@pytest.fixture
def sample_sprint_metrics(repository, sample_sector):
    """Fixture para criar métricas de sprint de exemplo."""
    metrics = [
        SprintMetric(
            sector_id=sample_sector.id,
            end_date=date(2025, 1, 15),
            story_points=10.0,
            person_days=20.0,
        ),
        SprintMetric(
            sector_id=sample_sector.id,
            end_date=date(2025, 1, 29),
            story_points=8.0,
            person_days=16.0,
        ),
    ]

    return [repository.add_sprint_metric(metric) for metric in metrics]


class TestRepository:
    def test_create_and_get_sector(self, repository):
        sector = Sector(
            name="Test Sector",
            estimation_mode=EstimationMode.BASELINE,
            anchor_effort_pm=3.0,
        )

        saved_sector = repository.add_sector(sector)
        retrieved_sector = repository.get_sector(saved_sector.id)

        assert retrieved_sector is not None
        assert retrieved_sector.name == "Test Sector"
        assert retrieved_sector.estimation_mode == EstimationMode.BASELINE
        assert retrieved_sector.anchor_effort_pm == 3.0

    def test_get_all_sectors(self, repository):
        sector1 = Sector(name="Sector 1", estimation_mode=EstimationMode.BASELINE)
        sector2 = Sector(name="Sector 2", estimation_mode=EstimationMode.GREENFIELD)

        repository.add_sector(sector1)
        repository.add_sector(sector2)

        all_sectors = repository.get_all_sectors()
        assert len(all_sectors) == 2

    def test_add_and_get_factors(self, repository, sample_sector):
        factor = Factor(
            sector_id=sample_sector.id,
            name="Test Factor",
            weight_pct=50.0,
            baseline_score=5.0,
            target_score=7.0,
        )

        repository.add_factor(factor)
        factors = repository.get_factors_by_sector(sample_sector.id)

        assert len(factors) == 1
        assert factors[0].name == "Test Factor"
        assert factors[0].weight_pct == 50.0

    def test_add_and_get_sprint_metrics(self, repository, sample_sector):
        metric = SprintMetric(
            sector_id=sample_sector.id,
            end_date=date(2025, 1, 15),
            story_points=10.0,
            person_days=20.0,
        )

        repository.add_sprint_metric(metric)
        metrics = repository.get_sprint_metrics_by_sector(sample_sector.id)

        assert len(metrics) == 1
        assert metrics[0].story_points == 10.0
        assert metrics[0].person_days == 20.0


class TestComplexityScorer:
    def test_calculate_complexity_index(self, sample_factors):
        scorer = ComplexityScorer()
        index = scorer.calculate_complexity_index(sample_factors)

        # Cálculo esperado:
        # (40 * 7 + 60 * 8) / (40 * 5 + 60 * 6) = (280 + 480) / (200 + 360) = 760 / 560 = 1.357
        expected_index = (40 * 7 + 60 * 8) / (40 * 5 + 60 * 6)
        assert abs(index - expected_index) < 0.001

    def test_calculate_complexity_index_empty_factors(self):
        scorer = ComplexityScorer()
        index = scorer.calculate_complexity_index([])
        assert index == 1.0

    def test_calculate_complexity_index_zero_baseline(self, repository, sample_sector):
        factor = Factor(
            sector_id=sample_sector.id,
            name="Test Factor",
            weight_pct=100.0,
            baseline_score=0.0,
            target_score=5.0,
        )

        scorer = ComplexityScorer()
        index = scorer.calculate_complexity_index([factor])
        assert index == 1.0  # Deve retornar 1.0 quando baseline_score é 0


class TestFibonacciRound:
    def test_round_to_fibonacci(self):
        fibonacci = FibonacciRound()

        assert fibonacci.round_to_fibonacci(1.2) == 1
        assert fibonacci.round_to_fibonacci(2.8) == 3
        assert fibonacci.round_to_fibonacci(4.5) == 5
        assert fibonacci.round_to_fibonacci(7.0) == 8
        assert fibonacci.round_to_fibonacci(15.0) == 13
        assert fibonacci.round_to_fibonacci(25.0) == 21

    def test_round_to_fibonacci_edge_cases(self):
        fibonacci = FibonacciRound()

        assert fibonacci.round_to_fibonacci(0) == 1
        assert fibonacci.round_to_fibonacci(-5) == 1
        assert fibonacci.round_to_fibonacci(100) == 21


class TestMonteCarloService:
    def test_simulate_sprints(self, sample_sprint_metrics):
        monte_carlo = MonteCarloService(num_simulations=100)  # Reduzido para testes

        p50, p80 = monte_carlo.simulate_sprints(50.0, sample_sprint_metrics)

        assert p50 > 0
        assert p80 > 0
        assert p80 >= p50  # P80 deve ser maior ou igual a P50

    def test_simulate_sprints_empty_metrics(self):
        monte_carlo = MonteCarloService()

        p50, p80 = monte_carlo.simulate_sprints(50.0, [])

        assert p50 == 0.0
        assert p80 == 0.0

    def test_simulate_sprints_zero_sp(self, sample_sprint_metrics):
        monte_carlo = MonteCarloService()

        p50, p80 = monte_carlo.simulate_sprints(0.0, sample_sprint_metrics)

        assert p50 == 0.0
        assert p80 == 0.0


class TestUtilityFunctions:
    def test_calculate_days_per_sp(self, sample_sprint_metrics):
        days_per_sp = calculate_days_per_sp(sample_sprint_metrics)

        # (20 + 16) / (10 + 8) = 36 / 18 = 2.0
        expected_days_per_sp = (20 + 16) / (10 + 8)
        assert abs(days_per_sp - expected_days_per_sp) < 0.001

    def test_calculate_days_per_sp_empty_metrics(self):
        days_per_sp = calculate_days_per_sp([])
        assert days_per_sp == 1.0

    def test_convert_to_story_points(self):
        sp = convert_to_story_points(
            anchor_effort_pm=5.0, complexity_index=1.5, days_per_sp=2.0
        )

        # (5 * 22 * 1.5) / 2.0 = 165 / 2.0 = 82.5
        expected_sp = (5 * 22 * 1.5) / 2.0
        assert abs(sp - expected_sp) < 0.001

    def test_convert_to_story_points_zero_days_per_sp(self):
        sp = convert_to_story_points(
            anchor_effort_pm=5.0, complexity_index=1.5, days_per_sp=0.0
        )
        assert sp == 0.0


class TestEstimationService:
    def test_create_estimation_snapshot(
        self, repository, sample_sector, sample_sprint_metrics
    ):
        estimation_service = EstimationService(repository)

        snapshot = estimation_service.create_estimation_snapshot(
            sample_sector.id, sp_total=50.0
        )

        assert snapshot.sector_id == sample_sector.id
        assert snapshot.sp_total == 50.0
        assert snapshot.effort_pm_est > 0
        assert snapshot.p50_weeks > 0
        assert snapshot.p80_weeks > 0
        assert snapshot.algo_version == "0.1.0"

    def test_create_estimation_snapshot_invalid_sector(self, repository):
        estimation_service = EstimationService(repository)

        with pytest.raises(ValueError, match="Sector .* not found"):
            estimation_service.create_estimation_snapshot(
                uuid4(), sp_total=50.0  # ID inexistente
            )


class TestModels:
    def test_sector_creation(self):
        sector = Sector(
            name="Test Sector",
            estimation_mode=EstimationMode.BASELINE,
            anchor_effort_pm=5.0,
        )

        assert sector.name == "Test Sector"
        assert sector.estimation_mode == EstimationMode.BASELINE
        assert sector.anchor_effort_pm == 5.0

    def test_factor_validation(self):
        # Teste com valores válidos
        factor = Factor(
            sector_id=uuid4(),
            name="Test Factor",
            weight_pct=50.0,
            baseline_score=5.0,
            target_score=7.0,
        )

        assert factor.weight_pct == 50.0
        assert factor.baseline_score == 5.0
        assert factor.target_score == 7.0

    def test_sprint_metric_creation(self):
        metric = SprintMetric(
            sector_id=uuid4(),
            end_date=date(2025, 1, 15),
            story_points=10.0,
            person_days=20.0,
        )

        assert metric.end_date == date(2025, 1, 15)
        assert metric.story_points == 10.0
        assert metric.person_days == 20.0

    def test_estimation_snapshot_creation(self):
        snapshot = EstimationSnapshot(
            sector_id=uuid4(),
            sp_total=50.0,
            effort_pm_est=4.5,
            p50_weeks=12.0,
            p80_weeks=16.0,
        )

        assert snapshot.sp_total == 50.0
        assert snapshot.effort_pm_est == 4.5
        assert snapshot.p50_weeks == 12.0
        assert snapshot.p80_weeks == 16.0
        assert snapshot.algo_version == "0.1.0"
