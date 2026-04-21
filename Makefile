
.PHONY: help install infra-up infra-down init-db load generate validate compute test notify export pipeline clean

# ============================================================
# Sport Data Solution — Makefile
# ============================================================

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- Setup ----------

install: ## Install Python dependencies
	uv sync

infra-up: ## Start Docker infrastructure (PostgreSQL + Airflow)
	colima start 2>/dev/null || true
	docker compose up -d
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@sleep 5
	@echo "✅ Infrastructure is up"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   Airflow:    http://localhost:8080 (admin/admin)"

infra-down: ## Stop Docker infrastructure
	docker compose down
	@echo "✅ Infrastructure stopped"

# ---------- Pipeline Steps ----------

init-db: ## Create database tables
	uv run python -m src.utils.init_db

load: ## Extract and load HR + Sports data
	uv run python -m src.extraction.load_rh
	uv run python -m src.extraction.load_sports

generate: ## Generate synthetic Strava-like activities
	uv run python -m src.generation.generate_activities

validate: ## Validate commute distances via Google Maps API
	uv run python -m src.transformation.validate_distances

compute: ## Compute benefits eligibility and financial impact
	uv run python -m src.transformation.compute_avantages

test: ## Run Soda Core data quality checks
	uv run soda scan -d sport_data -c tests/soda/configuration.yml tests/soda/checks.yml

notify: ## Send latest activities to Slack
	uv run python -m src.notifications.slack_notifier

export: ## Export data to CSV for Power BI
	uv run python -m src.utils.export_powerbi

# ---------- Full Pipeline ----------

pipeline: load generate validate compute test notify export ## Run the full pipeline end-to-end
	@echo ""
	@echo "✅ Full pipeline completed successfully"

# ---------- Utilities ----------

db-shell: ## Open PostgreSQL interactive shell
	docker exec -it sport_postgres psql -U sport_admin -d sport_data

db-tables: ## List all database tables
	docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "\dt"

db-count: ## Show row counts for all tables
	@docker exec -it sport_postgres psql -U sport_admin -d sport_data -c " \
		SELECT 'salaries' as tbl, count(*) FROM salaries UNION ALL \
		SELECT 'sports_pratiques', count(*) FROM sports_pratiques UNION ALL \
		SELECT 'activites', count(*) FROM activites UNION ALL \
		SELECT 'avantages_salaries', count(*) FROM avantages_salaries UNION ALL \
		SELECT 'validation_distances', count(*) FROM validation_distances \
		ORDER BY tbl;"

logs: ## Show Airflow logs
	docker logs -f sport_airflow

clean: ## Remove all containers, volumes, and processed data
	docker compose down -v
	rm -rf data/processed/*.csv dashboards/*.csv
	@echo "✅ Cleaned"

