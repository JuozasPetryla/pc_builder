.PHONY: up down logs demo test reset openapi

up:
	docker compose up --build --detach --wait

down:
	docker compose down

logs:
	docker compose logs --follow

demo:
	docker compose --profile demo run --rm demo

test:
	docker compose --profile test run --build --rm api-test

reset:
	docker compose down --volumes
	docker compose up --build --detach --wait

openapi:
	docker compose exec api python -m scripts.export_openapi

