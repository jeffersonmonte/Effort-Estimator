from datetime import datetime
from typing import List, Tuple

import numpy as np

from .models import EstimationSnapshot, Factor, SprintMetric


class ComplexityScorer:
    @staticmethod
    def calculate_complexity_index(factors: List[Factor]) -> float:
        """
        Calcula o índice de complexidade baseado nos fatores.
        index = Σ(weight × target_score) / Σ(weight × baseline_score)
        """
        if not factors:
            return 1.0

        weighted_target_sum = sum(
            factor.weight_pct * factor.target_score for factor in factors
        )
        weighted_baseline_sum = sum(
            factor.weight_pct * factor.baseline_score for factor in factors
        )

        if weighted_baseline_sum == 0:
            return 1.0

        return weighted_target_sum / weighted_baseline_sum


class FibonacciRound:
    FIBONACCI_SEQUENCE = [1, 2, 3, 5, 8, 13, 21]

    @staticmethod
    def round_to_fibonacci(value: float) -> int:
        """
        Arredonda um valor para o número de Fibonacci mais próximo.
        Se exceder 21, sugere quebrar a história.
        """
        if value <= 0:
            return 1

        if value > 21:
            return 21  # Sugere quebrar a história

        # Encontra o número de Fibonacci mais próximo
        closest_fib = min(
            FibonacciRound.FIBONACCI_SEQUENCE, key=lambda x: abs(x - value)
        )
        return closest_fib


class MonteCarloService:
    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations
        self.rng = np.random.default_rng()

    def simulate_sprints(
        self, sp_total: float, sprint_metrics: List[SprintMetric]
    ) -> Tuple[float, float]:
        """
        Simula quantos sprints são necessários para cobrir sp_total usando distribuição de throughput.
        Retorna P50 e P80 em semanas.
        """
        if not sprint_metrics or sp_total <= 0:
            return 0.0, 0.0

        # Calcula o throughput (story points por sprint) de cada sprint
        throughputs = [
            metric.story_points for metric in sprint_metrics if metric.story_points > 0
        ]

        if not throughputs:
            return 0.0, 0.0

        # Simula o número de sprints necessários
        sprints_needed = []

        for _ in range(self.num_simulations):
            remaining_sp = sp_total
            sprints = 0

            while remaining_sp > 0:
                # Amostra um throughput aleatório baseado no histórico
                throughput = self.rng.choice(throughputs)
                remaining_sp -= throughput
                sprints += 1

                # Proteção contra loops infinitos
                if sprints > 1000:
                    break

            sprints_needed.append(sprints)

        # Converte sprints para semanas (assumindo 2 semanas por sprint)
        weeks_needed = np.array(sprints_needed) * 2

        # Calcula P50 e P80
        p50_weeks = np.percentile(weeks_needed, 50)
        p80_weeks = np.percentile(weeks_needed, 80)

        return float(p50_weeks), float(p80_weeks)


def calculate_days_per_sp(sprint_metrics: List[SprintMetric]) -> float:
    """
    Calcula a média de dias por story point baseado no histórico de sprints.
    days_per_sp = Σ(person_days) / Σ(story_points)
    """
    if not sprint_metrics:
        return 1.0

    total_person_days = sum(metric.person_days for metric in sprint_metrics)
    total_story_points = sum(metric.story_points for metric in sprint_metrics)

    if total_story_points == 0:
        return 1.0

    return total_person_days / total_story_points


def convert_to_story_points(
    anchor_effort_pm: float, complexity_index: float, days_per_sp: float
) -> float:
    """
    Converte esforço em pessoa-mês para story points.
    sp_raw = (anchor_effort_pm × index) / days_per_sp
    """
    if days_per_sp == 0:
        return 0.0

    # Converte pessoa-mês para pessoa-dias (assumindo 22 dias úteis por mês)
    person_days = anchor_effort_pm * 22

    # Aplica o índice de complexidade
    adjusted_person_days = person_days * complexity_index

    # Converte para story points
    sp_raw = adjusted_person_days / days_per_sp

    return sp_raw


class EstimationService:
    def __init__(self, repository):
        self.repository = repository
        self.complexity_scorer = ComplexityScorer()
        self.fibonacci_round = FibonacciRound()
        self.monte_carlo = MonteCarloService()

    def create_estimation_snapshot(
        self, sector_id, sp_total: float
    ) -> EstimationSnapshot:
        """
        Cria um snapshot de estimativa para um setor.
        """
        sector = self.repository.get_sector(sector_id)
        if not sector:
            raise ValueError(f"Sector {sector_id} not found")

        sprint_metrics = self.repository.get_sprint_metrics_by_sector(sector_id)

        # Calcula days_per_sp
        days_per_sp = calculate_days_per_sp(sprint_metrics)

        # Calcula esforço em pessoa-mês
        effort_pm_est = (sp_total * days_per_sp) / 22  # 22 dias úteis por mês

        # Simula previsões Monte-Carlo
        p50_weeks, p80_weeks = self.monte_carlo.simulate_sprints(
            sp_total, sprint_metrics
        )

        # Cria o snapshot
        snapshot = EstimationSnapshot(
            sector_id=sector_id,
            captured_at=datetime.utcnow(),
            sp_total=sp_total,
            effort_pm_est=effort_pm_est,
            p50_weeks=p50_weeks,
            p80_weeks=p80_weeks,
            algo_version="0.1.0",
        )

        return self.repository.add_estimation_snapshot(snapshot)
