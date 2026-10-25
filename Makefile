.PHONY: all run build stop status test clean help

all: run

build:
	@./build.sh

run:
	@./build.sh

daemon:
	@./build.sh --daemon

stop:
	@./build.sh --stop

status:
	@./build.sh --status

test:
	@./build.sh --test

clean:
	@./build.sh --clean

help:
	@echo "Udyog Sathi — Build & Execution Controls:"
	@echo "  make run      - Verify environment, prepare database, and start server on http://localhost:8000"
	@echo "  make daemon   - Start server in background mode"
	@echo "  make stop     - Stop running server instance and free port 8000"
	@echo "  make status   - Check health endpoint and active port status"
	@echo "  make test     - Run full unit test suite"
	@echo "  make clean    - Remove locks, caches, and temp files"
