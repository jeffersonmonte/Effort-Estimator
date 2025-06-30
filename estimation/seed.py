from datetime import date, datetime
from uuid import uuid4

from .models import (
    AnchorStory,
    EstimationMode,
    EstimationSnapshot,
    Factor,
    Sector,
    SprintMetric,
)
from .repository import Repository


def seed_data(repository: Repository):
    """
    Cria dados de exemplo para demonstração do sistema.
    """

    # Setor "Compras" em modo baseline
    compras_sector = Sector(
        id=uuid4(),
        name="Compras",
        estimation_mode=EstimationMode.BASELINE,
        anchor_effort_pm=6.0,
    )
    compras_sector = repository.add_sector(compras_sector)

    # Fatores para o setor Compras
    compras_factors = [
        Factor(
            sector_id=compras_sector.id,
            name="Integrações",
            weight_pct=30.0,
            baseline_score=5.0,
            target_score=7.0,
        ),
        Factor(
            sector_id=compras_sector.id,
            name="Regras de Negócio",
            weight_pct=25.0,
            baseline_score=6.0,
            target_score=8.0,
        ),
        Factor(
            sector_id=compras_sector.id,
            name="Interface do Usuário",
            weight_pct=20.0,
            baseline_score=4.0,
            target_score=6.0,
        ),
        Factor(
            sector_id=compras_sector.id,
            name="Relatórios",
            weight_pct=15.0,
            baseline_score=3.0,
            target_score=5.0,
        ),
        Factor(
            sector_id=compras_sector.id,
            name="Performance",
            weight_pct=10.0,
            baseline_score=5.0,
            target_score=7.0,
        ),
    ]

    for factor in compras_factors:
        repository.add_factor(factor)

    # Setor "Estoque" em modo greenfield
    estoque_sector = Sector(
        id=uuid4(),
        name="Estoque",
        estimation_mode=EstimationMode.GREENFIELD,
        anchor_effort_pm=None,
    )
    estoque_sector = repository.add_sector(estoque_sector)

    # Histórias âncora para o setor Estoque
    anchor_stories = [
        AnchorStory(
            sector_id=estoque_sector.id,
            title="Cadastro simples de produto",
            story_points=1,
            description="Como usuário, quero cadastrar um produto com informações básicas (nome, código, categoria).",
            is_anchor=True,
        ),
        AnchorStory(
            sector_id=estoque_sector.id,
            title="Movimentação de estoque com validações",
            story_points=3,
            description="Como usuário, quero registrar entrada/saída de produtos com validações de saldo e regras de negócio.",
            is_anchor=True,
        ),
        AnchorStory(
            sector_id=estoque_sector.id,
            title="Relatório de inventário com filtros avançados",
            story_points=8,
            description="Como usuário, quero gerar relatórios de inventário com múltiplos filtros, exportação e agendamento.",
            is_anchor=True,
        ),
    ]

    for story in anchor_stories:
        repository.add_anchor_story(story)

    # Métricas de sprint fictícias para ambos os setores
    sprint_metrics_compras = [
        SprintMetric(
            sector_id=compras_sector.id,
            end_date=date(2025, 1, 15),
            story_points=13.0,
            person_days=20.0,
        ),
        SprintMetric(
            sector_id=compras_sector.id,
            end_date=date(2025, 1, 29),
            story_points=8.0,
            person_days=18.0,
        ),
        SprintMetric(
            sector_id=compras_sector.id,
            end_date=date(2025, 2, 12),
            story_points=21.0,
            person_days=22.0,
        ),
        SprintMetric(
            sector_id=compras_sector.id,
            end_date=date(2025, 2, 26),
            story_points=5.0,
            person_days=16.0,
        ),
    ]

    sprint_metrics_estoque = [
        SprintMetric(
            sector_id=estoque_sector.id,
            end_date=date(2025, 1, 15),
            story_points=8.0,
            person_days=16.0,
        ),
        SprintMetric(
            sector_id=estoque_sector.id,
            end_date=date(2025, 1, 29),
            story_points=13.0,
            person_days=24.0,
        ),
        SprintMetric(
            sector_id=estoque_sector.id,
            end_date=date(2025, 2, 12),
            story_points=5.0,
            person_days=12.0,
        ),
        SprintMetric(
            sector_id=estoque_sector.id,
            end_date=date(2025, 2, 26),
            story_points=21.0,
            person_days=28.0,
        ),
    ]

    for metric in sprint_metrics_compras + sprint_metrics_estoque:
        repository.add_sprint_metric(metric)

    # Snapshots de estimativa fictícios
    compras_snapshot = EstimationSnapshot(
        sector_id=compras_sector.id,
        captured_at=datetime(2025, 1, 1),
        sp_total=89.0,
        effort_pm_est=7.2,
        p50_weeks=18.0,
        p80_weeks=24.0,
        algo_version="0.1.0",
    )

    estoque_snapshot = EstimationSnapshot(
        sector_id=estoque_sector.id,
        captured_at=datetime(2025, 1, 1),
        sp_total=55.0,
        effort_pm_est=4.8,
        p50_weeks=14.0,
        p80_weeks=20.0,
        algo_version="0.1.0",
    )

    repository.add_estimation_snapshot(compras_snapshot)
    repository.add_estimation_snapshot(estoque_snapshot)

    print("Dados de exemplo criados com sucesso!")
    print(f"- Setor Compras (Baseline): {compras_sector.id}")
    print(f"- Setor Estoque (Greenfield): {estoque_sector.id}")
    print(f"- Total de fatores: {len(compras_factors)}")
    print(f"- Total de histórias âncora: {len(anchor_stories)}")
    print(
        f"- Total de métricas de sprint: {len(sprint_metrics_compras + sprint_metrics_estoque)}"
    )


if __name__ == "__main__":
    repo = Repository()
    seed_data(repo)
