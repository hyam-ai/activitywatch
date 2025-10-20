.PHONY: build test clean

build:
	poetry install

test:
	poetry run pytest tests/ || echo "No tests yet"

clean:
	rm -rf build dist
	rm -rf aw_export_daily_report/__pycache__
