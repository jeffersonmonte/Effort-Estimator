.PHONY: dev seed lint test clean install

# Instalar dependências
install:
	pip install -r requirements.txt

# Executar aplicação em modo desenvolvimento
dev:
	streamlit run app.py

# Carregar dados de exemplo
seed:
	python -m estimation.seed

# Executar linting
lint:
	black --check .
	flake8 .
	isort --check-only .

# Formatar código
format:
	black .
	isort .

# Executar testes
test:
	pytest tests/ -v --cov=estimation --cov-report=html --cov-report=term

# Executar testes com cobertura mínima
test-coverage:
	pytest tests/ -v --cov=estimation --cov-fail-under=80

# Limpar arquivos temporários
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/
	rm -f estimator.db

# Executar aplicação via Docker
docker-dev:
	docker compose up --build

# Parar containers Docker
docker-stop:
	docker compose down

# Executar todos os checks de qualidade
check: lint test-coverage

# Preparar para produção
build: clean format check
	@echo "Build completed successfully!"

