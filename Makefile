install:
	uv sync
test:
	uv run pytest
lint:
	uv run flake8 page_loader tests
build:
	uv build
package-install:
	uv tool install --reinstall .