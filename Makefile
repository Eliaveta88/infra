.PHONY: clone up

clone:
	git submodule update --init --recursive

up:
	docker compose -f docker-compose.yml up
