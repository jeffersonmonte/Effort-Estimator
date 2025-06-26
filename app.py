from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from uuid import uuid4

from estimation.models import (AnchorStory, EstimationMode, Factor, Sector,
                               SprintMetric)
from estimation.repository import Repository
from estimation.seed import seed_data
from estimation.services import (ComplexityScorer, EstimationService,
                                 FibonacciRound, MonteCarloService,
                                 calculate_days_per_sp,
                                 convert_to_story_points)

# Configuração da página
st.set_page_config(
    page_title="Effort Estimator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Inicialização do repositório
@st.cache_resource
def init_repository():
    return Repository()


repo = init_repository()


# Inicialização dos serviços
@st.cache_resource
def init_services():
    return EstimationService(repo)


estimation_service = init_services()

# Sidebar para navegação
st.sidebar.title("📊 Effort Estimator")
st.sidebar.markdown("---")

# Menu de navegação
page = st.sidebar.selectbox(
    "Navegação",
    [
        "🏠 Dashboard",
        "⚙️ Configuração de Projeto",
        "📈 Fluxo Baseline",
        "🌱 Fluxo Greenfield",
        "📊 Dados de Sprint",
        "📋 Relatórios",
    ],
)

# Botão para seed de dados
if st.sidebar.button("🌱 Carregar Dados de Exemplo"):
    try:
        seed_data(repo)
        st.sidebar.success("Dados de exemplo carregados!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar dados: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Versão:** 0.1.0")


# Função auxiliar para obter setores
@st.cache_data
def get_sectors():
    return repo.get_all_sectors()


# Página Dashboard
if page == "🏠 Dashboard":
    st.title("📊 Dashboard - Effort Estimator")

    sectors = get_sectors()

    if not sectors:
        st.info(
            "Nenhum setor encontrado. Use o menu lateral para carregar dados de exemplo ou criar um novo projeto."
        )
    else:
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total de Setores", len(sectors))

        with col2:
            baseline_count = sum(
                1 for s in sectors if s.estimation_mode == EstimationMode.BASELINE
            )
            st.metric("Modo Baseline", baseline_count)

        with col3:
            greenfield_count = sum(
                1 for s in sectors if s.estimation_mode == EstimationMode.GREENFIELD
            )
            st.metric("Modo Greenfield", greenfield_count)

        with col4:
            total_snapshots = sum(
                len(repo.get_estimation_snapshots_by_sector(s.id)) for s in sectors
            )
            st.metric("Total de Estimativas", total_snapshots)

        st.markdown("---")

        # Lista de setores
        st.subheader("📋 Setores Cadastrados")

        for sector in sectors:
            with st.expander(f"🏢 {sector.name} ({sector.estimation_mode.value})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**ID:** {sector.id}")
                    st.write(f"**Modo:** {sector.estimation_mode.value}")
                    if sector.anchor_effort_pm:
                        st.write(f"**Esforço Âncora:** {sector.anchor_effort_pm} PM")

                with col2:
                    factors = repo.get_factors_by_sector(sector.id)
                    sprint_metrics = repo.get_sprint_metrics_by_sector(sector.id)
                    snapshots = repo.get_estimation_snapshots_by_sector(sector.id)

                    st.write(f"**Fatores:** {len(factors)}")
                    st.write(f"**Sprints:** {len(sprint_metrics)}")
                    st.write(f"**Estimativas:** {len(snapshots)}")

# Página Configuração de Projeto
elif page == "⚙️ Configuração de Projeto":
    st.title("⚙️ Configuração de Projeto")

    tab1, tab2 = st.tabs(["➕ Novo Setor", "📝 Editar Setor"])

    with tab1:
        st.subheader("Criar Novo Setor")

        with st.form("new_sector_form"):
            sector_name = st.text_input(
                "Nome do Setor", placeholder="Ex: Vendas, Financeiro, RH"
            )
            estimation_mode = st.selectbox(
                "Modo de Estimativa",
                [EstimationMode.BASELINE, EstimationMode.GREENFIELD],
                format_func=lambda x: (
                    "Baseline-Histórico"
                    if x == EstimationMode.BASELINE
                    else "Greenfield (sem histórico)"
                ),
            )

            anchor_effort_pm = None
            if estimation_mode == EstimationMode.BASELINE:
                anchor_effort_pm = st.number_input(
                    "Esforço Âncora (Pessoa-Mês)",
                    min_value=0.1,
                    value=1.0,
                    step=0.1,
                    help="Esforço real em pessoa-mês do setor de referência",
                )

            submitted = st.form_submit_button("Criar Setor")

            if submitted and sector_name:
                try:
                    new_sector = Sector(
                        name=sector_name,
                        estimation_mode=estimation_mode,
                        anchor_effort_pm=anchor_effort_pm,
                    )
                    repo.add_sector(new_sector)
                    st.success(f"Setor '{sector_name}' criado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao criar setor: {e}")

    with tab2:
        st.subheader("Editar Setor Existente")

        sectors = get_sectors()
        if sectors:
            sector_options = {
                f"{s.name} ({s.estimation_mode.value})": s for s in sectors
            }
            selected_sector_name = st.selectbox(
                "Selecione o Setor", list(sector_options.keys())
            )

            if selected_sector_name:
                selected_sector = sector_options[selected_sector_name]

                # Exibir informações do setor
                st.write(f"**ID:** {selected_sector.id}")
                st.write(f"**Modo:** {selected_sector.estimation_mode.value}")

                # Gerenciar fatores
                st.subheader("🔧 Fatores de Complexidade")

                factors = repo.get_factors_by_sector(selected_sector.id)

                if factors:
                    for factor in factors:
                        with st.expander(f"📊 {factor.name}"):
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.write(f"**Peso:** {factor.weight_pct}%")
                            with col2:
                                st.write(f"**Score Baseline:** {factor.baseline_score}")
                            with col3:
                                st.write(f"**Score Alvo:** {factor.target_score}")
                            with col4:
                                if st.button(
                                    f"🗑️ Remover", key=f"del_factor_{factor.id}"
                                ):
                                    repo.delete_factor(factor.id)
                                    st.rerun()

                # Adicionar novo fator
                with st.form(f"add_factor_{selected_sector.id}"):
                    st.subheader("➕ Adicionar Fator")

                    col1, col2 = st.columns(2)
                    with col1:
                        factor_name = st.text_input("Nome do Fator")
                        weight_pct = st.number_input(
                            "Peso (%)", min_value=0.0, max_value=100.0, value=20.0
                        )

                    with col2:
                        baseline_score = st.number_input(
                            "Score Baseline", min_value=1.0, max_value=10.0, value=5.0
                        )
                        target_score = st.number_input(
                            "Score Alvo", min_value=1.0, max_value=10.0, value=5.0
                        )

                    if st.form_submit_button("Adicionar Fator"):
                        if factor_name and len(factors) < 5:
                            try:
                                new_factor = Factor(
                                    sector_id=selected_sector.id,
                                    name=factor_name,
                                    weight_pct=weight_pct,
                                    baseline_score=baseline_score,
                                    target_score=target_score,
                                )
                                repo.add_factor(new_factor)
                                st.success(f"Fator '{factor_name}' adicionado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao adicionar fator: {e}")
                        elif len(factors) >= 5:
                            st.error("Máximo de 5 fatores por setor.")
                        else:
                            st.error("Nome do fator é obrigatório.")
        else:
            st.info("Nenhum setor encontrado. Crie um novo setor primeiro.")

# Página Fluxo Baseline
elif page == "📈 Fluxo Baseline":
    st.title("📈 Fluxo Baseline-Histórico")

    sectors = [s for s in get_sectors() if s.estimation_mode == EstimationMode.BASELINE]

    if not sectors:
        st.info(
            "Nenhum setor em modo Baseline encontrado. Crie um setor em modo Baseline primeiro."
        )
    else:
        sector_options = {s.name: s for s in sectors}
        selected_sector_name = st.selectbox(
            "Selecione o Setor", list(sector_options.keys())
        )

        if selected_sector_name:
            selected_sector = sector_options[selected_sector_name]
            factors = repo.get_factors_by_sector(selected_sector.id)

            if not factors:
                st.warning(
                    "Este setor não possui fatores de complexidade. Configure os fatores primeiro."
                )
            else:
                st.subheader("🧮 Cálculo de Estimativa")

                # Exibir fatores e calcular índice de complexidade
                complexity_scorer = ComplexityScorer()
                complexity_index = complexity_scorer.calculate_complexity_index(factors)

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Fatores de Complexidade:**")
                    for factor in factors:
                        st.write(
                            f"- {factor.name}: {factor.weight_pct}% (Baseline: {factor.baseline_score}, Alvo: {factor.target_score})"
                        )

                with col2:
                    st.metric("Índice de Complexidade", f"{complexity_index:.2f}")
                    st.metric(
                        "Esforço Âncora", f"{selected_sector.anchor_effort_pm} PM"
                    )

                # Calcular days_per_sp baseado nos sprints
                sprint_metrics = repo.get_sprint_metrics_by_sector(selected_sector.id)
                days_per_sp = calculate_days_per_sp(sprint_metrics)

                st.metric("Dias por Story Point", f"{days_per_sp:.2f}")

                # Converter para story points
                sp_raw = convert_to_story_points(
                    selected_sector.anchor_effort_pm, complexity_index, days_per_sp
                )

                fibonacci_round = FibonacciRound()
                sp_final = fibonacci_round.round_to_fibonacci(sp_raw)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Story Points (Raw)", f"{sp_raw:.2f}")
                with col2:
                    st.metric("Story Points (Fibonacci)", sp_final)

                # Gerar estimativa
                if st.button("🎯 Gerar Estimativa"):
                    try:
                        snapshot = estimation_service.create_estimation_snapshot(
                            selected_sector.id, sp_final
                        )

                        st.success("Estimativa gerada com sucesso!")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Esforço Estimado", f"{snapshot.effort_pm_est:.2f} PM"
                            )
                        with col2:
                            st.metric(
                                "Previsão P50", f"{snapshot.p50_weeks:.1f} semanas"
                            )
                        with col3:
                            st.metric(
                                "Previsão P80", f"{snapshot.p80_weeks:.1f} semanas"
                            )

                    except Exception as e:
                        st.error(f"Erro ao gerar estimativa: {e}")

# Página Fluxo Greenfield
elif page == "🌱 Fluxo Greenfield":
    st.title("🌱 Fluxo Greenfield")

    sectors = [
        s for s in get_sectors() if s.estimation_mode == EstimationMode.GREENFIELD
    ]

    if not sectors:
        st.info(
            "Nenhum setor em modo Greenfield encontrado. Crie um setor em modo Greenfield primeiro."
        )
    else:
        sector_options = {s.name: s for s in sectors}
        selected_sector_name = st.selectbox(
            "Selecione o Setor", list(sector_options.keys())
        )

        if selected_sector_name:
            selected_sector = sector_options[selected_sector_name]

            tab1, tab2 = st.tabs(
                ["🎯 Histórias Âncora", "📊 Estimativa por Comparação"]
            )

            with tab1:
                st.subheader("Gerenciar Histórias Âncora")

                anchor_stories = repo.get_anchor_stories_by_sector(selected_sector.id)

                # Exibir histórias âncora existentes
                if anchor_stories:
                    for story in anchor_stories:
                        with st.expander(f"📖 {story.title} ({story.story_points} SP)"):
                            st.write(f"**Descrição:** {story.description}")
                            if st.button(f"🗑️ Remover", key=f"del_story_{story.id}"):
                                repo.delete_anchor_story(story.id)
                                st.rerun()

                # Adicionar nova história âncora
                with st.form(f"add_anchor_story_{selected_sector.id}"):
                    st.subheader("➕ Adicionar História Âncora")

                    story_title = st.text_input("Título da História")
                    story_points = st.selectbox("Story Points", [1, 3, 8])
                    story_description = st.text_area("Descrição")

                    if st.form_submit_button("Adicionar História"):
                        if story_title:
                            try:
                                new_story = AnchorStory(
                                    sector_id=selected_sector.id,
                                    title=story_title,
                                    story_points=story_points,
                                    description=story_description,
                                    is_anchor=True,
                                )
                                repo.add_anchor_story(new_story)
                                st.success(f"História '{story_title}' adicionada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao adicionar história: {e}")
                        else:
                            st.error("Título da história é obrigatório.")

            with tab2:
                st.subheader("Estimativa por Comparação Relativa")

                anchor_stories = repo.get_anchor_stories_by_sector(selected_sector.id)

                if len(anchor_stories) < 3:
                    st.warning(
                        "É necessário ter pelo menos 3 histórias âncora (1, 3, 8 SP) para fazer estimativas."
                    )
                else:
                    st.write("**Histórias Âncora Disponíveis:**")
                    for story in sorted(anchor_stories, key=lambda x: x.story_points):
                        st.write(f"- **{story.story_points} SP:** {story.title}")

                    st.markdown("---")

                    # Calcular days_per_sp se houver sprints
                    sprint_metrics = repo.get_sprint_metrics_by_sector(
                        selected_sector.id
                    )

                    if len(sprint_metrics) >= 2:
                        days_per_sp = calculate_days_per_sp(sprint_metrics)
                        st.success(
                            f"Calibração automática: {days_per_sp:.2f} dias/SP (baseado em {len(sprint_metrics)} sprints)"
                        )

                        # Estimativa de backlog
                        total_sp = st.number_input(
                            "Total de Story Points do Backlog",
                            min_value=1.0,
                            value=50.0,
                            step=1.0,
                            help="Estime o total de story points do backlog usando comparação relativa com as histórias âncora",
                        )

                        if st.button("🎯 Gerar Estimativa Greenfield"):
                            try:
                                snapshot = (
                                    estimation_service.create_estimation_snapshot(
                                        selected_sector.id, total_sp
                                    )
                                )

                                st.success("Estimativa gerada com sucesso!")

                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric(
                                        "Esforço Estimado",
                                        f"{snapshot.effort_pm_est:.2f} PM",
                                    )
                                with col2:
                                    st.metric(
                                        "Previsão P50",
                                        f"{snapshot.p50_weeks:.1f} semanas",
                                    )
                                with col3:
                                    st.metric(
                                        "Previsão P80",
                                        f"{snapshot.p80_weeks:.1f} semanas",
                                    )

                            except Exception as e:
                                st.error(f"Erro ao gerar estimativa: {e}")
                    else:
                        st.info(
                            "Adicione pelo menos 2 sprints para calibração automática do days/SP."
                        )

# Página Dados de Sprint
elif page == "📊 Dados de Sprint":
    st.title("📊 Dados de Sprint")

    sectors = get_sectors()

    if not sectors:
        st.info("Nenhum setor encontrado. Crie um setor primeiro.")
    else:
        sector_options = {s.name: s for s in sectors}
        selected_sector_name = st.selectbox(
            "Selecione o Setor", list(sector_options.keys())
        )

        if selected_sector_name:
            selected_sector = sector_options[selected_sector_name]

            tab1, tab2 = st.tabs(["➕ Adicionar Sprint", "📋 Histórico de Sprints"])

            with tab1:
                st.subheader("Adicionar Dados de Sprint")

                with st.form(f"add_sprint_{selected_sector.id}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        end_date = st.date_input("Data de Término", value=date.today())

                    with col2:
                        story_points = st.number_input(
                            "Story Points Concluídos",
                            min_value=0.0,
                            value=0.0,
                            step=0.5,
                        )

                    with col3:
                        person_days = st.number_input(
                            "Pessoa-Dias Gastos", min_value=0.0, value=0.0, step=0.5
                        )

                    if st.form_submit_button("Adicionar Sprint"):
                        if story_points > 0 and person_days > 0:
                            try:
                                new_metric = SprintMetric(
                                    sector_id=selected_sector.id,
                                    end_date=end_date,
                                    story_points=story_points,
                                    person_days=person_days,
                                )
                                repo.add_sprint_metric(new_metric)
                                st.success("Dados de sprint adicionados!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao adicionar sprint: {e}")
                        else:
                            st.error(
                                "Story Points e Pessoa-Dias devem ser maiores que zero."
                            )

            with tab2:
                st.subheader("Histórico de Sprints")

                sprint_metrics = repo.get_sprint_metrics_by_sector(selected_sector.id)

                if sprint_metrics:
                    # Criar DataFrame para exibição
                    df_sprints = pd.DataFrame(
                        [
                            {
                                "Data de Término": metric.end_date,
                                "Story Points": metric.story_points,
                                "Pessoa-Dias": metric.person_days,
                                "Dias/SP": (
                                    metric.person_days / metric.story_points
                                    if metric.story_points > 0
                                    else 0
                                ),
                            }
                            for metric in sorted(
                                sprint_metrics, key=lambda x: x.end_date
                            )
                        ]
                    )

                    st.dataframe(df_sprints, use_container_width=True)

                    # Métricas resumo
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        total_sp = df_sprints["Story Points"].sum()
                        st.metric("Total SP", f"{total_sp:.1f}")

                    with col2:
                        total_days = df_sprints["Pessoa-Dias"].sum()
                        st.metric("Total Pessoa-Dias", f"{total_days:.1f}")

                    with col3:
                        avg_sp_per_sprint = df_sprints["Story Points"].mean()
                        st.metric("Média SP/Sprint", f"{avg_sp_per_sprint:.1f}")

                    with col4:
                        avg_days_per_sp = calculate_days_per_sp(sprint_metrics)
                        st.metric("Média Dias/SP", f"{avg_days_per_sp:.2f}")

                    # Gráfico de velocity
                    fig = px.line(
                        df_sprints,
                        x="Data de Término",
                        y="Story Points",
                        title="Velocity por Sprint",
                        markers=True,
                    )
                    fig.add_hline(
                        y=avg_sp_per_sprint, line_dash="dash", annotation_text="Média"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.info("Nenhum dado de sprint encontrado para este setor.")

# Página Relatórios
elif page == "📋 Relatórios":
    st.title("📋 Relatórios e Dashboards")

    sectors = get_sectors()

    if not sectors:
        st.info("Nenhum setor encontrado. Crie um setor primeiro.")
    else:
        sector_options = {s.name: s for s in sectors}
        selected_sector_name = st.selectbox(
            "Selecione o Setor", list(sector_options.keys())
        )

        if selected_sector_name:
            selected_sector = sector_options[selected_sector_name]

            tab1, tab2, tab3 = st.tabs(
                ["📊 Comparison View", "🚀 Velocity Chart", "🎲 Monte-Carlo"]
            )

            with tab1:
                st.subheader("Comparison View - Estimativa vs Realidade")

                snapshots = repo.get_estimation_snapshots_by_sector(selected_sector.id)
                sprint_metrics = repo.get_sprint_metrics_by_sector(selected_sector.id)

                if snapshots and sprint_metrics:
                    # Criar dados para comparação
                    df_comparison = []

                    # Dados de estimativa (linha teórica)
                    latest_snapshot = max(snapshots, key=lambda x: x.captured_at)
                    weeks_range = range(0, int(latest_snapshot.p80_weeks) + 5)

                    for week in weeks_range:
                        progress_pct = min(week / latest_snapshot.p50_weeks, 1.0) * 100
                        df_comparison.append(
                            {
                                "Semana": week,
                                "Tipo": "Estimativa P50",
                                "Progresso (%)": progress_pct,
                            }
                        )

                    # Dados reais (baseado nos sprints)
                    cumulative_sp = 0
                    for i, metric in enumerate(
                        sorted(sprint_metrics, key=lambda x: x.end_date)
                    ):
                        cumulative_sp += metric.story_points
                        progress_pct = (cumulative_sp / latest_snapshot.sp_total) * 100
                        df_comparison.append(
                            {
                                "Semana": (i + 1) * 2,  # Assumindo sprints de 2 semanas
                                "Tipo": "Progresso Real",
                                "Progresso (%)": min(progress_pct, 100),
                            }
                        )

                    df_comp = pd.DataFrame(df_comparison)

                    fig = px.line(
                        df_comp,
                        x="Semana",
                        y="Progresso (%)",
                        color="Tipo",
                        title="Estimativa vs Progresso Real",
                        markers=True,
                    )
                    fig.update_layout(yaxis_range=[0, 100])
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.info(
                        "Dados insuficientes para comparação. Adicione estimativas e sprints."
                    )

            with tab2:
                st.subheader("Velocity Chart")

                sprint_metrics = repo.get_sprint_metrics_by_sector(selected_sector.id)

                if sprint_metrics:
                    df_velocity = pd.DataFrame(
                        [
                            {
                                "Sprint": f"Sprint {i+1}",
                                "Data": metric.end_date,
                                "Story Points": metric.story_points,
                                "Pessoa-Dias": metric.person_days,
                            }
                            for i, metric in enumerate(
                                sorted(sprint_metrics, key=lambda x: x.end_date)
                            )
                        ]
                    )

                    # Gráfico de velocity
                    fig = go.Figure()

                    fig.add_trace(
                        go.Bar(
                            x=df_velocity["Sprint"],
                            y=df_velocity["Story Points"],
                            name="Story Points",
                            marker_color="lightblue",
                        )
                    )

                    # Linha de média
                    avg_velocity = df_velocity["Story Points"].mean()
                    fig.add_hline(
                        y=avg_velocity,
                        line_dash="dash",
                        annotation_text=f"Média: {avg_velocity:.1f}",
                    )

                    fig.update_layout(
                        title="Velocity por Sprint",
                        xaxis_title="Sprint",
                        yaxis_title="Story Points",
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Estatísticas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Velocity Média", f"{avg_velocity:.1f} SP")
                    with col2:
                        velocity_std = df_velocity["Story Points"].std()
                        st.metric("Desvio Padrão", f"{velocity_std:.1f} SP")
                    with col3:
                        max_velocity = df_velocity["Story Points"].max()
                        st.metric("Velocity Máxima", f"{max_velocity:.1f} SP")

                else:
                    st.info("Nenhum dado de sprint encontrado.")

            with tab3:
                st.subheader("Simulação Monte-Carlo")

                sprint_metrics = repo.get_sprint_metrics_by_sector(selected_sector.id)
                snapshots = repo.get_estimation_snapshots_by_sector(selected_sector.id)

                if sprint_metrics and snapshots:
                    latest_snapshot = max(snapshots, key=lambda x: x.captured_at)

                    # Executar simulação Monte-Carlo
                    monte_carlo = MonteCarloService()

                    # Simular distribuição de semanas
                    throughputs = [
                        metric.story_points
                        for metric in sprint_metrics
                        if metric.story_points > 0
                    ]

                    if throughputs:
                        # Simular 1000 execuções para o histograma
                        simulations = []
                        rng = np.random.default_rng()

                        for _ in range(1000):
                            remaining_sp = latest_snapshot.sp_total
                            sprints = 0

                            while remaining_sp > 0 and sprints < 100:
                                throughput = rng.choice(throughputs)
                                remaining_sp -= throughput
                                sprints += 1

                            simulations.append(sprints * 2)  # Converter para semanas

                        # Criar histograma
                        fig = px.histogram(
                            x=simulations,
                            nbins=20,
                            title="Distribuição de Semanas (Monte-Carlo)",
                            labels={"x": "Semanas", "y": "Frequência"},
                        )

                        # Adicionar linhas P50 e P80
                        fig.add_vline(
                            x=latest_snapshot.p50_weeks,
                            line_dash="dash",
                            annotation_text=f"P50: {latest_snapshot.p50_weeks:.1f}",
                        )
                        fig.add_vline(
                            x=latest_snapshot.p80_weeks,
                            line_dash="dash",
                            annotation_text=f"P80: {latest_snapshot.p80_weeks:.1f}",
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # Estatísticas da simulação
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("P50", f"{latest_snapshot.p50_weeks:.1f} semanas")
                        with col2:
                            st.metric("P80", f"{latest_snapshot.p80_weeks:.1f} semanas")
                        with col3:
                            sim_mean = np.mean(simulations)
                            st.metric("Média Simulação", f"{sim_mean:.1f} semanas")
                        with col4:
                            sim_std = np.std(simulations)
                            st.metric("Desvio Padrão", f"{sim_std:.1f} semanas")

                    else:
                        st.info("Dados de sprint insuficientes para simulação.")
                else:
                    st.info("Dados insuficientes para simulação Monte-Carlo.")

# Footer
st.markdown("---")
st.markdown(
    "**Effort Estimator v0.1.0** - Sistema de estimativa de esforço para desenvolvimento de software"
)
