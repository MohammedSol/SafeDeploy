# ============================================================
# SafeDeploy — Makefile
# Cibles : up, down, logs, clean, help
# Prérequis : GNU Make 4.x, Docker Compose v2.x
# ============================================================

.DEFAULT_GOAL := help
.PHONY: up down logs clean help

# Affiche l'aide (toutes les cibles documentées avec ##)
help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

# Lance PostgreSQL et MLflow en arrière-plan
up: ## Lance les services (postgres + mlflow)
	docker compose up -d --remove-orphans

# Arrête les services sans supprimer les volumes
down: ## Arrête les services (conserve les données)
	docker compose down

# Affiche les logs en continu (Ctrl+C pour quitter)
logs: ## Affiche les logs de tous les services
	docker compose logs -f

# Arrête les services ET supprime les volumes (réinitialisation complète)
clean: ## Arrête les services et supprime les volumes (DESTRUCTIF)
	docker compose down -v

	.PHONY: train
train:
	docker compose run --rm trainer
