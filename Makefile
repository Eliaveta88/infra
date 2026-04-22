.PHONY: clone up integration-tests data-generator

clone:
	git submodule update --init --recursive

up:
	docker compose -f docker-compose.yml up

integration-tests:
	bash scripts/run_integration_tests.sh

# Генерация тестовых данных (см. data_generator/README.md). Передайте ARGS при необходимости.
# Пример: make data-generator ARGS="--count 5000 --truncate"
data-generator:
	bash scripts/run_data_generator.sh $(ARGS)
