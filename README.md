# Effort Estimator

O Effort Estimator é um aplicativo web desenvolvido para auxiliar no cálculo de prazos de desenvolvimento para módulos de ERP, suportando duas abordagens de estimativa: Baseline-Histórico e Greenfield.

## Funcionalidades

- **Modo Baseline-Histórico:** Utiliza um setor já entregue como âncora para estimativas.
- **Modo Greenfield (sem histórico):** Baseado em histórias-âncora internas e calibração automática.
- **Fatores de Complexidade:** Definição de até cinco fatores com pesos editáveis.
- **Lançamento de Dados de Sprint:** Importação ou adição manual de dados de sprint.
- **Previsões Monte-Carlo:** Geração de previsões P50/P80.
- **Dashboards:** Comparação de estimativa teórica vs. progresso real, Velocity Chart e Histograma Monte-Carlo.

## Tecnologias Utilizadas

- **Backend & Domínio:** Python 3.11, Pydantic, NumPy, Pandas
- **Persistência:** SQLite via SQLModel
- **Front-end:** Streamlit 1.35
- **Simulação:** Monte-Carlo (numpy.random.default_rng())
- **Dev UX:** Makefile
- **Container:** Docker + Docker Compose
- **Testes:** pytest + coverage

## Quick Start

### Local

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute a aplicação:
   ```bash
   streamlit run app.py
   ```

### Docker

1. Construa e execute os contêineres:
   ```bash
   docker compose up --build
   ```

## How it works

O sistema permite configurar projetos com diferentes modos de estimativa. No modo Baseline-Histórico, um setor de referência é usado para calcular o índice de complexidade. No modo Greenfield, histórias-âncora e dados de sprint são utilizados para calibrar a estimativa. As previsões são geradas através de simulações Monte-Carlo, e os resultados são visualizados em dashboards interativos.

## Next steps

- Implementar autenticação de usuários.
- Adicionar suporte a múltiplos bancos de dados.
- Melhorar a interface do usuário com mais opções de personalização.
- Expandir os tipos de gráficos e relatórios disponíveis.


