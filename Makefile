all: format lint_tests unit_tests

format:
	ruff check --fix src tests
	ruff format ./src tests

lint_tests:
	ruff check src tests

unit_tests:
	coverage run -m --source src pytest --durations=0
	coverage report -m
	coverage xml


docker-run:
	source .env && \
	uv pip compile pyproject.toml -o requirements.txt && \
	docker-compose up --build

docker-build:
	source .env && \
	uv pip compile pyproject.toml -o requirements.txt && \
	docker-compose build

docker-bash:
	docker-compose run strava bash

docker-dev:
	docker-compose run strava fastapi dev ./src/app.py --reload --host 0.0.0.0 --port 8000

deploy:
	bash ./cicd/deploy/deploy.sh