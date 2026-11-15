# SafeDeploy — SalesPredict

> Plateforme intelligente de prédiction du chiffre d'affaires, conteneurisée et déployable sur n'importe quelle machine avec une seule commande.

📄 Référence complète du projet : [SAFEDEPLOY_PLAN.md](./SAFEDEPLOY_PLAN.md)

---

## Prérequis

| Outil | Version minimale |
|---|---|
| Docker Desktop (ou Docker Engine) | 24.x |
| Docker Compose | v2.x |
| GNU Make | 4.x — ou utiliser `scripts/dev.ps1` sous Windows |
| Git | 2.x |

> **Windows sans `make` :** utilisez `.\scripts\dev.ps1 up` à la place de `make up`.

---

## Démarrage rapide

```bash
# 1. Copier les variables d'environnement (ne jamais versionner .env)
cp .env.example .env

# 2. Démarrer PostgreSQL et MLflow
make up

# 3. Vérifier que tout est healthy
docker compose ps

# 4. Ouvrir MLflow
# http://localhost:5000
```

> **Windows (sans make) :**
> ```powershell
> copy .env.example .env
> .\scripts\dev.ps1 up
> ```

---

## Commandes disponibles

| Commande | Rôle |
|---|---|
| `make up` | Lance tous les services en arrière-plan |
| `make down` | Arrête les services (conserve les volumes) |
| `make logs` | Affiche les logs en continu |
| `make clean` | Arrête les services et supprime les volumes |

---

## Ports exposés

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 *(S3)* |
| Backend FastAPI | http://localhost:8000 *(S2)* |
| MLflow | http://localhost:5000 |
| Prometheus | http://localhost:9090 *(S5)* |
| Grafana | http://localhost:3001 *(S5)* |

---

## État du projet

Sprint 0 en cours — seuls PostgreSQL et MLflow sont disponibles pour l'instant.
Voir [SAFEDEPLOY_PLAN.md](./SAFEDEPLOY_PLAN.md) pour le plan complet des 7 sprints.
