.PHONY: run-demo install lint test clean

run-demo:
	docker compose up --build -d
	@echo "System started. Run 'make seed' for demo data if needed."

seed:
	python scripts/seed_demo_data.py

install:
	pip install -r requirements.txt
	pre-commit install

lint:
	ruff check .
	black --check .
	isort --check-only .
	mypy .

test:
	pytest tests/ -q

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
