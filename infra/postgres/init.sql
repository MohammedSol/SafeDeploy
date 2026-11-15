-- ============================================================
-- SafeDeploy — Initialisation de la base PostgreSQL
-- Créé par : S0 (Mohammed)
-- Ce script est exécuté automatiquement au premier démarrage
-- du conteneur PostgreSQL via docker-entrypoint-initdb.d/
-- ============================================================

-- Table des ventes mensuelles (série historique)
-- Chargée depuis backend/data/sales.csv en S2.
CREATE TABLE IF NOT EXISTS sales_monthly (
    month   DATE        NOT NULL,
    revenue NUMERIC(14, 2) NOT NULL,
    CONSTRAINT pk_sales_monthly PRIMARY KEY (month)
);

-- Table de l'historique des prédictions
-- Alimentée par POST /api/predictions (S2).
CREATE TABLE IF NOT EXISTS predictions (
    id                SERIAL        NOT NULL,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    target_month      DATE          NOT NULL,
    input             JSONB,
    predicted_revenue NUMERIC(14, 2) NOT NULL,
    model_name        VARCHAR(128)  NOT NULL,
    model_version     VARCHAR(64),
    CONSTRAINT pk_predictions PRIMARY KEY (id)
);

-- Index utiles pour les requêtes de l'API
CREATE INDEX IF NOT EXISTS idx_sales_monthly_month
    ON sales_monthly (month);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at
    ON predictions (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_target_month
    ON predictions (target_month);
