# SafeDeploy — Passation des sprints 1 et 2

**Statut au 18 novembre 2026**

| Sprint | Statut | Résultat |
|---|---|---|
| **S1 · Données, ML et MLflow** | ✅ Validé | Trois modèles comparés. **Random Forest v2** porte l’alias `production`. |
| **S2 · Backend FastAPI** | ✅ Validé | Sept routes vérifiées, import sur base neuve confirmé et **9 tests API réussis**. |
| **S3 · Interface web** | ⏭ À démarrer | Connecter le frontend sur `http://localhost:3000` à l’API sur le port **8000**. |

## S1 · Données et modèles

- **Données** — 48 mois de ventes Superstore agrégés dans `backend/data/sales.csv` (`month`, `revenue)), de janvier 2023 à décembre 2026.
- **Variables** — `lag_1`, `rolling_mean_3` et `month` dans `backend/ml/features.py`. Deux tests vérifient l’usage des ventes passées et l’absence de valeurs manquantes.
- **Évaluation** — 33 mois d’entraînement, trois plis chronologiques et 12 mois de test final. La prévision porte sur un mois et utilise les ventes réelles des mois précédents. Les six métriques sont identiques sur deux exécutions dans MLflow.

| Modèle | MAE validation | RMSE validation | R² validation | MAE test | RMSE test | R² test |
|---|---:|---:|---:|---:|---:|---:|
| Régression linéaire | 14 752,08 | 16 957,56 | −0,648 | **17 259,02** | **21 063,91** | **0,349** |
| Random Forest | **10 654,96** | **14 141,61** | −0,152 | 20 862,20 | 25 605,56 | 0,038 |
| XGBoost | 12 654,65 | 15 221,00 | **0,135** | 22 266,43 | 27 784,95 | −0,132 |

Random Forest a été choisi selon la **MAE moyenne de validation**, le critère fixé avant le test final. La régression linéaire a la plus faible MAE sur le test final. Les résultats sont consultables dans [MLflow · sales-forecast](http://localhost:5000/#/experiments/1).

## S2 · Backend FastAPI

- **PostgreSQL et SQLAlchemy** — `init.sql` crée les tables et charge automatiquement les 48 mois sur une base neuve. Les prévisions sont enregistrées et relues via SQLAlchemy.
- **MLflow** — FastAPI charge `models:/sales-model@production` au démarrage et signale explicitement l’échec si le modèle est introuvable. La comparaison renvoie un run par algorithme et indique la version active.
- **CORS et supervision** — Le frontend local sur le port 3000 est autorisé. `/metrics` expose les métriques HTTP, le compteur des prévisions, l’histogramme des montants et la jauge du modèle.
- **Vérifications** — 9 tests API réussis, notamment l’enregistrement et la relecture d’une prévision, les entrées invalides, le cas sans ventes et le démarrage sans modèle. Exemple validé dans Swagger avec `{}` pour janvier 2027 · **19 746,02 USD**, modèle v2.

## S3 · Où reprendre

| Besoin frontend | Route |
|---|---|
| Graphique et résumé des ventes | `GET /api/sales` · `GET /api/sales/summary` |
| Générer et afficher les prévisions | `POST /api/predictions` · `GET /api/predictions/history` |
| Comparer les modèles | `GET /api/models/compare` |
| Vérifier les services | `GET /health` · `GET /metrics` |

Le backend tourne actuellement dans un conteneur ponctuel du service `trainer`. Depuis la racine du dépôt, avec la configuration locale déjà en place, démarrer PostgreSQL et MLflow puis lancer l’API dans PowerShell.

```powershell
docker compose up -d postgres mlflow
docker compose run --rm -p 127.0.0.1:8000:8000 trainer sh -ec 'python -m pip install -q fastapi uvicorn sqlalchemy psycopg psycopg-binary mlflow==2.19.0 numpy==1.26.4 pandas==2.2.3 scikit-learn==1.5.2 cloudpickle==3.1.2 prometheus-fastapi-instrumentator && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000'
```

Une fois le démarrage terminé, vérifier [l’état de l’API](http://localhost:8000/health) et ouvrir [Swagger](http://localhost:8000/docs). Une installation avec un registre MLflow neuf doit d’abord lancer `docker compose run --rm trainer` pour créer le modèle portant l’alias `production`. Relancer cette commande sur un registre déjà initialisé crée une nouvelle version et déplace l’alias vers elle.
