# Telemetry Dashboard — Parrot Technical Test

API de recherche de télémétrie drone + dashboard React/TypeScript.

---

## Démarrage rapide

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

API disponible sur `http://localhost:8000`  
Documentation Swagger : `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard disponible sur `http://localhost:5173`

---

## Endpoints

### `GET /events`

| Paramètre | Type   | Défaut | Description                     |
|-----------|--------|--------|---------------------------------|
| device    | string | —      | Filtre par device               |
| status    | string | —      | Filtre par status               |
| limit     | int    | 20     | Résultats par page (max 100)    |
| offset    | int    | 0      | Décalage de pagination          |
| sort      | string | desc   | Tri timestamp : `asc` / `desc`  |

Réponse :

```json
{
  "items": [...],
  "total": 10003,
  "limit": 20,
  "offset": 0,
  "anomaly_count": 2
}
```

### `GET /stats`

```json
{
  "total": 10003,
  "avg_battery": 49.87,
  "by_status": [
    { "status": "idle", "count": 2531 },
    { "status": "flying", "count": 2512 }
  ]
}
```

---

## Architecture

```
backend/
├── app/
│   ├── main.py              # CORS, lifespan, logging config
│   ├── database.py          # aiosqlite, seed 10k+ événements, index
│   ├── models/event.py      # Pydantic schemas + validators
│   ├── repositories/        # SQL async pur, aucune logique métier
│   ├── services/            # Logique métier, validation des params
│   └── routers/             # HTTP layer + logging structuré JSON

frontend/
├── src/
│   ├── api/client.ts        # fetch wrapper, AbortController, timeout
│   ├── hooks/               # useEvents (debounce), useStats (useMemo)
│   └── components/          # EventList, EventFilters, StatsPanel, BatteryChart
```

---

## Dataset — pièges volontaires

Le seed contient trois événements pathologiques intentionnels. Votre code doit les gérer proprement.

| Piège | Valeur |
|---|---|
| Status inconnu | `"unknown"` |
| Batterie négative | `-5` |
| Timestamp hors-ordre | `2025-12-31T23:59:00` |

---

## À documenter dans ce README

Complétez les sections suivantes avant de rendre le projet.

### Choix techniques

- **FastAPI & Async SQLite** : Le backend est construit avec FastAPI pour sa rapidité et sa gestion native de l'asynchrone. L'accès à la base de données SQLite utilise `aiosqlite` pour éviter tout blocage d'I/O lors de requêtes simultanées.
- **Indexation de Base de Données** : Pour garantir des performances optimales sur l'endpoint `/events`, j'ai ajouté des index multi-colonnes sur `(device, status, timestamp)` et `(status, timestamp)`. Cela permet au moteur de base de données de filtrer et trier en complexité logarithmique $O(\log N)$, maintenant le temps de réponse sous les 15ms pour 10 000+ enregistrements.
- **Gestion des Anomalies** : Au lieu de rejeter ou de masquer les lignes pathologiques (valeurs aberrantes ou statuts inconnus), je les lis comme des données brutes validées par Pydantic (`EventRaw`). Les erreurs de validation sont transformées en attributs `is_anomaly` et `anomaly_reason` dans le schéma de sortie, ce qui permet de les conserver pour analyse tout en les signalant graphiquement.
- **Frontend sombre translucide futuriste** : Réalisé en React, TypeScript et CSS natif, le dashboard affiche un style moderne et épuré. La police d'écriture **Outfit** est importée depuis Google Fonts. Recharts est utilisé pour les graphiques avec des transitions fluides et un style vitreux assorti. Cette stack m'a permis de créer une interface utilisateur moderne et intuitive, tout en bénéficiant de la robustesse et des performances de TypeScript et React. Aussi l'experience utilisateur est fluide et agréable, avec des animations douces et réactives.
- **Filtre d'anomalies dédié** : J'ai conçu et intégré un filtre d'anomalies à l'interface. Ce mécanisme permet à l'utilisateur d'isoler instantanément tous les événements défectueux en un clic, évitant ainsi de devoir parcourir manuellement l'intégralité de la pagination pour repérer les dysfonctionnements.
- **Tests unitaires et d'intégration (pytest)** : J'ai mis en place une suite de tests automatisés dans `backend/tests` couvrant la validation des modèles Pydantic (détection des anomalies sur la batterie, les statuts et les timestamps) ainsi que les méthodes du repository et du service pour sécuriser les fonctionnalités de filtrage.

### Stratégie de scaling en production

Si le volume de données devait être multiplié par 100 (passant à 1M+ événements) :
1. **Migration vers PostgreSQL / TimescaleDB** : SQLite montre ses limites en accès concurrents en écriture. L'utilisation de TimescaleDB (extension time-series pour PostgreSQL) permettrait d'optimiser le stockage et le requêtage de séries temporelles massives.
2. **Indexation et persistance des anomalies** : Actuellement, le filtrage des anomalies s'effectue en mémoire en validant l'ensemble du dataset à la volée. À grande échelle, le flag `is_anomaly` et ses raisons doivent être calculés au moment de l'ingestion (écriture) et persistés sous forme de colonnes indexées en base de données.
3. **Partitionnement Temporel** : Partitionner les tables par tranches temporelles (par semaine ou par mois). Les requêtes du dashboard ciblant principalement les données récentes, cela réduit drastiquement le nombre de lignes scannées.
4. **Mise en cache** : Mettre en place un cache Redis devant l'endpoint `/stats`. Comme cet endpoint agrège l'ensemble de l'historique, une mise en cache avec un TTL (Time To Live) de quelques dizaines de secondes réduirait considérablement la charge de calcul.
5. **Conteneurisation et Orchestration (Docker & Kubernetes)** : Conteneuriser le backend FastAPI et le frontend React (compilé et servi par un serveur Nginx ultra-léger) avec Docker. Cette standardisation permettra d'exécuter l'application sur un orchestrateur de conteneurs (Kubernetes ou ECS) afin d'ajouter automatiquement des réplicas derrière un répartiteur de charge lors des pics de trafic.

### Question monitoring

Pour détecter et diagnostiquer un problème de performance sur l'endpoint `/events` :
1. **Métriques d'APM (Application Performance Monitoring)** : Intégrer un outil comme Datadog, Sentry ou OpenTelemetry pour tracer la latence de bout en bout (percentiles p50, p95, p99). Le header `X-Response-Time` déjà implémenté permet de suivre le temps passé côté serveur directement dans les logs.
2. **Logs Structurés et Alertes** : Les requêtes HTTP sont logguées au format JSON structuré avec les paramètres exacts. Une augmentation anormale du temps écoulé déclenchera des alertes automatisées.
3. **Profiling des requêtes SQL** : Activer le log des requêtes lents en base de données (ex: `pg_stat_statements` sur PostgreSQL) pour repérer si le planificateur de requêtes effectue des scans complets de tables (`Seq Scan`) plutôt que d'utiliser les index.

### Axes d'amélioration

Si je disposais d'un jour supplémentaire pour enrichir le projet :
1. **Temps réel avec WebSockets** : Remplacer le système de polling de 30 secondes par une connexion temps réel pour pousser instantanément les nouveaux événements drone vers le client.
2. **Filtres Temporels et Agrégations** : Permettre à l'utilisateur de sélectionner une plage de dates personnalisée pour limiter la recherche d'événements et adapter les graphiques.
3. **Couverture de Tests Client** : Écrire des tests unitaires pour les composants et hooks React avec Vitest et React Testing Library, ainsi que des tests de bout en bout (E2E) avec Playwright.
4. **Documentation complète** : Ajouter une documentation complète du projet avec Swagger et une documentation pour les développeurs.

## Objectif du test

Ce test vise à évaluer votre capacité à concevoir et implémenter une application full-stack en conditions proches de la production.

Nous portons une attention particulière à :
- la qualité du code
- la structuration
- la gestion des cas réels (edge cases)
- la réflexion autour de la performance et du passage à l’échelle

## Workflow attendu

1. Fork du repository
2. Créer une branche dédiée (ex: feature/telemetry)
3. Développer sur cette branche
4. Ouvrir une Pull Request vers main

Les push directs sur main sont bloqués

La qualité des commits et du workflow Git fait partie de l’évaluation


## Attendus importants

- L’API doit rester performante (<200ms sur 10k+ événements)
- Les données invalides doivent être traitées proprement (validation ou signalement)
- Une structuration claire du code est attendue (pas de code monolithique)
- Le projet n’a pas besoin d’être complet : la qualité prime sur l’exhaustivité

Il est tout à fait acceptable de ne pas tout terminer. Nous privilégions la qualité, la clarté des choix techniques et la capacité d’analyse.
