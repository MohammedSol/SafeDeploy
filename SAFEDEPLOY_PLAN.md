# SafeDeploy — Plan d'architecture et de sprints

> Plateforme intelligente de prédiction du chiffre d'affaires (SalesPredict), conteneurisée et déployable à l'identique sur n'importe quelle machine avec une seule commande.
> Durée : 7 jours. Ce fichier est la référence de l'équipe : on le met à jour dans Git à chaque fin de sprint.

## Suivi global (à mettre à jour)

| Sprint | Jour | Thème | Responsable | Statut |
|---|---|---|---|---|
| S0 | J1 matin | Fondations du dépôt | Mohammed | ⬜ À faire |
| S1 | J1 après-midi – J2 | Données, ML et MLflow | Ahmed | ⬜ À faire |
| S2 | J3 | Backend FastAPI | Farah | ⬜ À faire |
| S3 | J4 | Frontend Next.js | Mohammed | ⬜ À faire |
| S4 | J5 | Dockerisation complète | Ahmed | ⬜ À faire |
| S5 | J6 | Monitoring et CI | Farah | ⬜ À faire |
| S6 | J7 | Validation et livraison | Mohammed | ⬜ À faire |

Légende : ⬜ À faire · 🟨 En cours · ✅ Terminé (tous les tests du sprint passent, balise Git posée)

---

## 1. Vision

Une application web qui permet de consulter les ventes historiques, de prédire le chiffre d'affaires du mois suivant avec un modèle de machine learning, de comparer les modèles entraînés, et de surveiller la santé de l'ensemble des services.

Le cœur du projet n'est pas le modèle mais le **déploiement reproductible** :
- tout démarre avec `make up` depuis une machine propre ;
- chaque entraînement est tracé et versionné dans MLflow ;
- le backend charge le modèle de production depuis le registre MLflow ;
- l'état technique et ML est visible dans Grafana.

## 2. Stack technologique

| Couche | Technologie | Rôle |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript, Tailwind, Recharts | Dashboard, formulaire de prédiction, comparaison des modèles |
| Backend | FastAPI (Python 3.11) | API, prédictions, historique, métriques |
| Base de données | PostgreSQL 16 | Ventes mensuelles et historique des prédictions |
| ML | scikit-learn, XGBoost | Linear Regression, Random Forest, XGBoost |
| MLOps | MLflow (tracking + Model Registry) | Suivi des expériences, modèle `sales-model@production` |
| Conteneurs | Docker, Docker Compose | 6 services, volumes persistants, healthchecks |
| Monitoring | Prometheus + Grafana | Métriques techniques et métier |
| CI | GitHub Actions | Tests et build des images |
| Données | Superstore Sales (Kaggle), agrégé par mois | Série mensuelle de chiffre d'affaires |

## 3. Architecture

```
                         Navigateur
                             │
                  http://localhost:3000
                             │
                    ┌────────▼────────┐
                    │ frontend        │  Next.js
                    └────────┬────────┘
                             │ REST (JSON)
                    ┌────────▼────────┐        ┌────────────────┐
                    │ backend         │───────▶│ postgres       │
                    │ FastAPI         │  SQL   │ ventes,        │
                    │ /api/*, /metrics│        │ prédictions    │
                    └───┬─────────┬───┘        └────────────────┘
        charge le modèle│         │ scrape /metrics
        models:/sales-model@production         
                    ┌───▼───┐   ┌─▼──────────┐   ┌──────────┐
                    │mlflow │   │ prometheus │──▶│ grafana  │
                    └───▲───┘   └────────────┘   └──────────┘
                        │ logue runs + modèle
                  ┌─────┴─────┐
                  │ trainer   │  (conteneur ponctuel : make train)
                  └───────────┘
```

Ports : frontend 3000, backend 8000, mlflow 5000, prometheus 9090, grafana 3001, postgres 5432 (interne).

Points d'architecture importants :
- MLflow tourne avec `--serve-artifacts` : le backend et le trainer récupèrent les modèles en HTTP, sans volume partagé.
- Le navigateur appelle le backend via `NEXT_PUBLIC_API_URL=http://localhost:8000`. Les appels côté serveur Next.js utilisent `INTERNAL_API_URL=http://backend:8000`.
- Le backend active CORS pour `http://localhost:3000`.
- Le modèle est choisi par validation croisée temporelle ; le jeu de test final n'est utilisé qu'une fois, pour le rapport.

## 4. Structure du dépôt

```
safedeploy/
├── docker-compose.yml
├── Makefile                      # up, down, train, test, logs, clean
├── .env.example
├── README.md
├── SAFEDEPLOY_PLAN.md            # ce fichier
├── .github/workflows/ci.yml
├── backend/
│   ├── app/
│   │   ├── main.py               # création de l'app, CORS, /health, /metrics
│   │   ├── routes/               # sales.py, predictions.py, models.py
│   │   ├── services/             # sales_service.py, prediction_service.py
│   │   ├── database/             # connection.py
│   │   └── schemas/              # prediction.py
│   ├── ml/
│   │   ├── features.py           # lag_1, rolling_mean_3, month
│   │   ├── train.py              # compare 3 modèles, logue dans MLflow, pose l'alias
│   │   ├── evaluate.py
│   │   └── predict.py
│   ├── data/sales.csv            # série mensuelle agrégée
│   ├── tests/
│   ├── requirements.txt          # versions fixées
│   └── Dockerfile                # multi-stage, utilisateur non-root
├── frontend/
│   ├── src/app/                  # page.tsx (dashboard), predict/, models/
│   ├── src/components/           # cartes KPI, graphiques, formulaire, tableau
│   ├── src/lib/api.ts            # client de l'API
│   └── Dockerfile                # multi-stage, sortie standalone
├── infra/
│   ├── postgres/init.sql         # tables + chargement du CSV
│   ├── prometheus/prometheus.yml
│   └── grafana/
│       ├── provisioning/         # datasource + dashboards
│       └── dashboards/safedeploy.json
└── scripts/smoke_test.sh         # vérifie l'ensemble de la chaîne
```

## 5. Règles d'équipe

**Branche unique et passage de relais**
- Une seule branche Git : `main`. Il n'y a pas de branches par sprint, pas de Pull Requests.
- Chaque sprint est réalisé par une seule personne ; les sprints s'enchaînent strictement l'un après l'autre.
- Le responsable teste son sprint en local, puis pousse directement sur `main` à la fin du sprint. Le sprint suivant ne démarre qu'après ce push et la validation des tests.
- En début de sprint : `git pull --rebase origin main`. En fin de sprint : `git pull --rebase origin main` puis `git push origin main`. Pas de `push --force`.
- Format des commits : Conventional Commits avec le sprint en portée, par exemple `feat(s1): add training script`.

**Définition de « terminé » (Definition of Done) pour un sprint**
1. Toutes les tâches cochées.
2. Tous les tests de la section « Tests » du sprint passent — exécutés en local avec succès **avant** le push sur `main`. À partir de S5, la CI GitHub Actions doit aussi être verte sur `main` après le push ; en cas d'échec, le responsable du sprint le corrige immédiatement avant de déclarer le sprint terminé.
3. `make up` fonctionne toujours depuis un état propre.
4. Le README et ce fichier sont à jour.
5. La note de passation du sprint est rédigée.
6. La balise Git `sprint-N-done` est posée sur `main`.

**Comment marquer un sprint comme terminé**
1. Cocher les cases `[x]` du sprint dans ce fichier.
2. Passer son statut à `✅ Terminé` dans le tableau de suivi, avec le nom du responsable.
3. Rédiger la note de passation (sous-section « Note de passation » du sprint).
4. Pousser la mise à jour de ce fichier dans le même commit final que le sprint, ou dans un commit suivant, **avant** de poser la balise.
5. Poser la balise : `git tag sprint-N-done && git push --tags`.
6. Prévenir l'équipe : le sprint suivant peut démarrer.

On ne démarre pas un sprint tant que le précédent n'est pas ✅. Les autres membres peuvent se préparer (lecture du plan, du contrat d'API, téléchargement du jeu de données) sans rien pousser sur `main` avant leur tour.

**Contrat d'API (figé à la fin de S0)**

| Endpoint | Méthode | Rôle |
|---|---|---|
| `/health` | GET | Santé du backend (base et modèle chargés) |
| `/api/sales` | GET | Ventes mensuelles |
| `/api/sales/summary` | GET | CA total, dernier mois, évolution |
| `/api/predictions` | POST | Prédit le CA du mois suivant ; corps optionnel (`lag_1`, `rolling_mean_3`, `month`), sinon calculé depuis la base |
| `/api/predictions/history` | GET | Historique des prédictions |
| `/api/models/compare` | GET | Résultats des runs MLflow (MAE, RMSE, R²) et modèle en production |
| `/metrics` | GET | Métriques Prometheus |

Tables : `sales_monthly(month DATE PK, revenue NUMERIC)` et `predictions(id, created_at, target_month, input JSONB, predicted_revenue, model_name, model_version)`.

---

## 6. Sprints

### S0 — Fondations du dépôt (J1 matin)

**Responsable :** Mohammed

**Objectif :** un dépôt propre où `make up` lance PostgreSQL et MLflow.

**Tâches**
- [ ] Créer le dépôt, la structure de dossiers, `.gitignore`, `README.md` minimal.
- [ ] Écrire `.env.example` (identifiants PostgreSQL, ports, URL MLflow).
- [ ] Écrire `docker-compose.yml` avec `postgres` et `mlflow` (volumes nommés, healthchecks).
- [ ] Écrire le `Makefile` (`up`, `down`, `logs`, `clean`).
- [ ] Figer le contrat d'API (tableau ci-dessus) dans `backend/app/schemas/`.
- [ ] Squelette `ci.yml` (exécution vide qui passe ; le workflow se déclenche sur `push` vers `main`).

**Comment**
- MLflow : image Python avec `mlflow` en version fixée, lancé avec `--backend-store-uri sqlite:////mlflow/mlflow.db --serve-artifacts --artifacts-destination /mlflow/artifacts --host 0.0.0.0`, volume nommé sur `/mlflow`.
- PostgreSQL : image `postgres:16`, volume nommé, `infra/postgres/init.sql` monté dans `/docker-entrypoint-initdb.d/`.
- Healthchecks : `pg_isready` pour PostgreSQL, requête HTTP sur `/health` pour MLflow.

**Tests**
- [ ] `docker compose config` ne retourne aucune erreur.
- [ ] `make up` : les deux conteneurs passent à l'état `healthy`.
- [ ] L'interface MLflow répond sur `http://localhost:5000`.
- [ ] `make down && make up` conserve les données (volumes).

**Livrable :** infrastructure de base fonctionnelle.

#### Note de passation

- **Ce qui a été fait :**
- **Écarts par rapport au plan :**
- **Commandes utiles :**
- **Points d'attention pour le sprint suivant :**

---

### S1 — Données, ML et MLflow (J1 après-midi – J2)

**Responsable :** Ahmed

**Objectif :** trois modèles comparés, tracés dans MLflow, le meilleur enregistré avec l'alias `production`.

**Tâches**
- [ ] Télécharger Superstore, agréger par mois, produire `backend/data/sales.csv` (colonnes `month`, `revenue`).
- [ ] `features.py` : `lag_1`, `rolling_mean_3` (calculée sur les 3 mois précédents), `month`.
- [ ] Séparation chronologique : les 9 à 12 derniers mois forment le jeu de test final.
- [ ] `train.py` : entraîner Linear Regression, Random Forest, XGBoost.
- [ ] Logguer dans MLflow : paramètres, MAE, RMSE, R² (validation croisée et test), modèle.
- [ ] Enregistrer le meilleur modèle sous `sales-model` avec l'alias `production`.
- [ ] Ajouter `make train` (conteneur ponctuel `trainer` qui logue vers `http://mlflow:5000`).

**Comment**
- Validation : `TimeSeriesSplit` (3 à 4 plis) sur les données d'entraînement ; les modèles sont comparés sur la **MAE moyenne de validation croisée**.
- Le jeu de test final sert uniquement à rapporter les métriques, pas à choisir le modèle.
- `random_state` fixé partout. Expérience MLflow nommée `sales-forecast`.
- Alias via `MlflowClient().set_registered_model_alias("sales-model", "production", version)`.

**Tests**
- [ ] `pytest` sur `features.py` : aucune fuite d'information (la valeur d'un mois n'entre jamais dans ses propres variables) et pas de valeur manquante après suppression des premiers mois.
- [ ] `make train` se termine sans erreur et crée 3 runs dans MLflow.
- [ ] Le registre contient `sales-model` avec l'alias `production`.
- [ ] Relancer `make train` donne des métriques identiques (reproductibilité).

**Livrable :** modèle de production enregistré et comparaison visible dans MLflow.

#### Note de passation

- **Ce qui a été fait :**
- **Écarts par rapport au plan :**
- **Commandes utiles :**
- **Points d'attention pour le sprint suivant :**

---

### S2 — Backend FastAPI (J3)

**Responsable :** Farah

**Objectif :** l'API complète, testée, qui charge le modèle depuis MLflow.

**Tâches**
- [ ] `init.sql` : créer les deux tables et charger `sales.csv` dans `sales_monthly`.
- [ ] Connexion à PostgreSQL (SQLAlchemy).
- [ ] Chargement de `models:/sales-model@production` au démarrage.
- [ ] Endpoints du contrat d'API, avec schémas Pydantic.
- [ ] Enregistrement de chaque prédiction dans `predictions`.
- [ ] `/health` : vérifie la base et le modèle.
- [ ] `/metrics` avec `prometheus-fastapi-instrumentator` plus les métriques métier ci-dessous.
- [ ] CORS pour `http://localhost:3000`.

**Métriques métier**
- `safedeploy_predictions_total{model_version}` (compteur)
- `safedeploy_prediction_value` (histogramme)
- `safedeploy_model_info{algorithm,version}` (gauge à 1)

**Tests**
- [ ] `pytest` avec `TestClient` : succès et erreurs de chaque endpoint (corps invalide, base vide).
- [ ] `POST /api/predictions` retourne une valeur numérique et crée une ligne dans `predictions`.
- [ ] `/api/models/compare` retourne les 3 runs de S1.
- [ ] `/metrics` expose les trois métriques métier.
- [ ] Le backend refuse de démarrer proprement (message clair) si le modèle est introuvable.

**Livrable :** API fonctionnelle, documentée par `/docs`.

#### Note de passation

- **Ce qui a été fait :**
- **Écarts par rapport au plan :**
- **Commandes utiles :**
- **Points d'attention pour le sprint suivant :**

---

### S3 — Frontend Next.js (J4)

**Responsable :** Mohammed

**Objectif :** une interface utilisable qui consomme l'API.

**Tâches**
- [ ] Initialiser Next.js (App Router, TypeScript, Tailwind) et `src/lib/api.ts`.
- [ ] Page **Dashboard** : cartes KPI (CA total, dernier mois, prévision), courbe des ventes historiques et de la prévision.
- [ ] Page **Prédiction** : bouton « Prédire le mois suivant » et historique des prédictions.
- [ ] Page **Modèles** : tableau MAE / RMSE / R² des 3 modèles, modèle en production mis en évidence.
- [ ] États de chargement et d'erreur sur chaque page.
- [ ] Variables `NEXT_PUBLIC_API_URL` et `INTERNAL_API_URL`.

**Tests**
- [ ] `npm run lint` et `npm run build` sans erreur.
- [ ] Les trois pages affichent des données réelles du backend lancé en local.
- [ ] Backend arrêté : la page affiche un message d'erreur, pas un écran blanc.
- [ ] Parcours manuel : Dashboard → prédiction → l'historique contient la nouvelle ligne.

**Livrable :** application utilisable en local.

#### Note de passation

- **Ce qui a été fait :**
- **Écarts par rapport au plan :**
- **Commandes utiles :**
- **Points d'attention pour le sprint suivant :**

---

### S4 — Dockerisation complète (J5)

**Responsable :** Ahmed

**Objectif :** les 6 services démarrent ensemble depuis un état propre.

**Tâches**
- [ ] `backend/Dockerfile` multi-stage, utilisateur non-root, dépendances à versions fixées.
- [ ] `frontend/Dockerfile` multi-stage avec sortie `standalone`.
- [ ] Compléter `docker-compose.yml` : `backend`, `frontend` avec `depends_on` conditionné par les healthchecks.
- [ ] `scripts/smoke_test.sh` : vérifie `/health`, une prédiction et la page d'accueil.
- [ ] `make up` lance tout ; `make train` entraîne puis recharge le modèle.
- [ ] Documenter le démarrage dans le README.

**Tests**
- [ ] `docker compose down -v && make up` : tous les services deviennent `healthy`.
- [ ] `scripts/smoke_test.sh` retourne 0.
- [ ] `make train` puis redémarrage du backend : la nouvelle version du modèle est servie.
- [ ] Les images n'embarquent aucun secret (`.env` absent des couches).

**Livrable :** application complète lancée par une seule commande.

#### Note de passation

- **Ce qui a été fait :**
- **Écarts par rapport au plan :**
- **Commandes utiles :**
- **Points d'attention pour le sprint suivant :**

---

### S5 — Monitoring et CI (J6)

**Responsable :** Farah

**Objectif :** observabilité technique et ML, pipeline d'intégration continue.

**Tâches**
- [ ] `prometheus.yml` : cibles `backend` et `prometheus`.
- [ ] Grafana provisionné par fichiers : datasource Prometheus et dashboard `safedeploy.json`.
- [ ] Panneaux : requêtes par seconde, latence p95, taux d'erreurs, prédictions par version du modèle, dernière valeur prédite, état des cibles (`up`).
- [ ] `ci.yml` : `pytest` du backend, lint et build du frontend, `docker compose build` ; le workflow s'exécute sur chaque push vers `main` et le responsable du sprint en vérifie le résultat.

**Tests**
- [ ] Prometheus : toutes les cibles sont `UP` sur `http://localhost:9090/targets`.
- [ ] Grafana démarre avec le dashboard déjà présent, sans configuration manuelle.
- [ ] Générer du trafic (quelques prédictions) : les panneaux évoluent.
- [ ] Arrêter le backend : la cible passe à `DOWN` et le panneau d'état le montre.
- [ ] Le workflow GitHub Actions est vert sur `main`.

**Livrable :** monitoring opérationnel et pipeline CI vert.

#### Note de passation

- **Ce qui a été fait :**
- **Écarts par rapport au plan :**
- **Commandes utiles :**
- **Points d'attention pour le sprint suivant :**

---

### S6 — Validation et livraison (J7)

**Responsable :** Mohammed

**Objectif :** prouver la reproductibilité et préparer la remise.

**Tâches**
- [ ] Test sur une machine propre (ou une VM) : clone, `cp .env.example .env`, `make up`, `make train`.
- [ ] Vérifier la persistance (arrêt puis redémarrage sans perte de données).
- [ ] README final : prérequis, démarrage, ports, commandes, dépannage.
- [ ] Rapport : architecture, choix, résultats honnêtes de la comparaison des modèles, limites, perspectives.
- [ ] Captures d'écran (dashboard, MLflow, Grafana) et script de démo de 5 minutes.
- [ ] Balise finale `v1.0`.

**Tests**
- [ ] Un membre de l'équipe qui n'a pas écrit le code déroule le README seul, sans aide, jusqu'au dashboard.
- [ ] `docker compose down -v && make up && make train` fonctionne de bout en bout.
- [ ] Le scénario de démo passe deux fois de suite sans erreur.

**Livrable :** SafeDeploy v1.0, documentation et démo prêtes.

#### Note de passation

- **Ce qui a été fait :**
- **Écarts par rapport au plan :**
- **Commandes utiles :**
- **Points d'attention pour le sprint suivant :**

---

## 7. Hors périmètre

Spring Boot, Kafka, Kubernetes, RAG et LLM, authentification, réentraînement automatique, détection de dérive avancée, déploiement continu en production. Ces points peuvent figurer dans la section « Perspectives » du rapport.

## 8. Risques connus

| Risque | Parade |
|---|---|
| Artefacts MLflow introuvables depuis le backend | `--serve-artifacts` (voir S0) |
| Appels API du navigateur qui échouent dans Docker | Deux URL distinctes, public et interne (voir section 3) |
| Peu de données (environ 45 mois exploitables) | Validation croisée temporelle ; résultats présentés sans surinterprétation |
| Image Docker du backend trop lourde ou build XGBoost trop lent | Utiliser `GradientBoostingRegressor` de scikit-learn à la place |
| Dérive du planning | Un sprint non terminé le jour prévu : on retire des tâches secondaires, jamais des tests |
| Conflits ou régression lors d'un push direct sur main | `git pull --rebase` avant le push, tests exécutés avant chaque push, un seul sprint actif à la fois |
| Un sprint bloqué retarde toute l'équipe (enchaînement strict) | Signaler le blocage dès qu'il dépasse deux heures, et retirer des tâches secondaires plutôt que des tests |
