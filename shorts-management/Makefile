# Usage: make resume-from N=348
resume-from:
	python3 -c "import json; d=json.load(open('videos_today.json')); json.dump(d[348:], open('videos_today.json','w'), indent=2, ensure_ascii=False)"

# YouTube Shorts Processing Makefile (Docker Run version)

# Docker image name
IMAGE_NAME = youtube-shorts-processor
CONTAINER_NAME = youtube-shorts-ui

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run the web UI with Docker
ui: build
	docker run -d --name $(CONTAINER_NAME) \
		-p 5000:5000 \
		-v $(PWD):/app \
		-e OPENAI_API_KEY=$$(cat .env | grep OPENAI_API_KEY | cut -d'=' -f2) \
		$(IMAGE_NAME)

# Stop the web UI
stop-ui:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

# Restart the web UI
restart-ui: stop-ui ui

# View logs
logs:
	docker logs -f $(CONTAINER_NAME)

# Clean up
clean:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME) || true

# Quick start (build and run)
start: ui
	@echo "🎬 YouTube Shorts Processor UI is running!"
	@echo "🌐 Open your browser to: http://localhost:5000"
	@echo "📱 Use 'make stop-ui' to stop the container"

# Run without Docker (local development)
dev:
	python3 web_ui.py

# Resume from specific video index
resume-from:
	@echo "Usage: make resume-from N=348"
	@if [ -z "$(N)" ]; then \
		echo "Error: Please specify N parameter"; \
		echo "Example: make resume-from N=348"; \
		exit 1; \
	fi
	python3 -c "import json; d=json.load(open('videos_today.json')); json.dump(d[$(N):], open('videos_today.json','w'), indent=2, ensure_ascii=False)"

# Help
help:
	@echo "Available commands:"
	@echo "  make start      - Build and start the web UI with Docker"
	@echo "  make ui         - Start the web UI with Docker"
	@echo "  make stop-ui    - Stop the web UI"
	@echo "  make restart-ui - Restart the web UI"
	@echo "  make logs       - View container logs"
	@echo "  make clean      - Clean up containers and images"
	@echo "  make dev        - Run locally without Docker"
	@echo "  make resume-from N=348 - Resume from specific video index"