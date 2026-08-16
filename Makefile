.PHONY: up down build logs test lint format migrate

# Docker commands
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up -d --build

logs:
	docker compose logs -f

# Testing and Code Quality
test:
	python -m pytest --cov=app tests/

lint:
	flake8 app/ tests/

format:
	isort app/ tests/
	black app/ tests/

# Database Migrations
migrate:
	alembic upgrade head

makemigrations:
	alembic revision --autogenerate -m "Auto migration"
