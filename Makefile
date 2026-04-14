.PHONY: dev migrate build logs test

dev:
	docker compose up --build

migrate:
	docker compose exec api alembic upgrade head

build:
	docker compose build

logs:
	docker compose logs -f api worker

test:
	docker compose exec api pytest -v
