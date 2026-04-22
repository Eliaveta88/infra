.PHONY: clone up integration-tests

clone:
	git submodule update --init --recursive

up:
	docker compose -f docker-compose.yml up

integration-tests:
	bash scripts/run_integration_tests.sh
