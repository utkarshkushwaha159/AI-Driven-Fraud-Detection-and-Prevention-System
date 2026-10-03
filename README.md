# AI-Driven Fraud Detection and Prevention System


A high-performance, machine-learning-powered financial fraud screening and intelligence platform with real-time risk classification, explainable AI (SHAP), behavioural transaction profiling, graph network intelligence, simulated customer checkout, and fraud analyst case management.

- **Live Website**: [https://ai-driven-fraud-detection-and-prevention-system.vercel.app](https://ai-driven-fraud-detection-and-prevention-system.vercel.app)
- **GitHub Repository**: [https://github.com/utkarshkushwaha159/AI-Driven-Fraud-Detection-and-Prevention-System](https://github.com/utkarshkushwaha159/AI-Driven-Fraud-Detection-and-Prevention-System)

---

## 1. System Overview & Architecture

The system provides an enterprise-grade defense mechanism against card-not-present fraud, account takeovers, suspicious velocity attacks, and syndicate networks. Unlike naive rule checkers, the core risk evaluation is powered by a machine-learning engine combining an **XGBoost Classifier** with an **Isolation Forest Anomaly Detector**, accompanied by model explanations using **SHAP (SHapley Additive exPlanations)**.

### Architectural Diagram

```
                                [ Customer Browser ]
                                        │ (HTTPS / REST)
                                        ▼
                         [ FastAPI Gateway (:8000) ]
                                 │              │
                   ┌─────────────┴──────┐       │
                   ▼                    ▼       ▼
          [ Feature Engine ]    [ Auth Service ] [ Network Service ]
                   │                                    │
          ┌────────┴────────┐                           ▼
          ▼                 ▼                  [ Adjacency Graph ]
    [ XGBoost Model ] [ Isolation Forest ]       (BFS, DFS, Dijkstra,
          │                 │                     Connected Clusters)
          └────────┬────────┘                           │
                   ▼                                    │
          [ SHAP Explainer ]                            │
                   │                                    │
                   └─────────────────┬──────────────────┘
                                     ▼
                            [ SQLite / SQLAlchemy ]
                                     │
                                     ▼
                        [ Fraud Analyst Dashboard ]
                           React 19 + Vite (:5173)
```

---

## 2. Key Features

1. **Simulated Customer Payment Checkout**:
   - Clean, realistic consumer payment portal with zero technical jargon.
   - Immediate feedback with 3 operational security states:
     - `SAFE`: Approved instantly.
     - `SUSPICIOUS`: Temporarily held with simulation of 2FA/OTP verification.
     - `HIGH_RISK`: Held for investigator review; alert and case opportunities generated.
   - Quick one-click simulation presets (Safe ₹450, Suspicious ₹45,000, High-Risk ₹2,50,000).

2. **Machine-Learning Fraud Screening Pipeline**:
   - **Primary Model**: XGBoost Classifier trained on behavioural patterns and transaction velocity.
   - **Anomaly Detector**: Scikit-Learn Isolation Forest identifying multidimensional outliers.
   - **No Target Leakage**: Historical aggregations only consider transactions preceding the current timestamp.
   - **Metrics Evaluated**: Precision, Recall, F1 Score, ROC-AUC, PR-AUC, and Confusion Matrix.

3. **Explainable AI (XAI)**:
   - Evaluates each prediction via SHAP values or feature importance distributions.
   - Explains exactly *why* a transaction was flagged (e.g. amount deviation, unusual hour, novel device/IP combination, rapid velocity).

4. **Graph & Network Security Intelligence**:
   - Internal Adjacency-List Graph modeling:
     - `Account → Device`
     - `Account → IP`
     - `Account → Transaction`
     - `Transaction → Merchant`
     - `Device → other Accounts`
     - `IP → other Accounts`
   - Algorithms applied: Connected Components (syndicate ring detection), BFS/DFS traversal, Dijkstra shortest-path connection, and Minimum Spanning Trees.
   - Interactive visual graph inspection on the Analyst Portal.

5. **Internal DSA Utilities (`backend/app/dsa/`)**:
   - Structured and tested implementations across all 5 units:
     - **Unit 1**: Binary Search Tree (BST), AVL Tree (auto-balancing), Max Heap, Heap Sort, Threaded Binary Tree.
     - **Unit 2**: Adjacency Graph, BFS, DFS, Connected Components, Prim, Kruskal, Dijkstra, Bellman-Ford, Floyd-Warshall, Transitive Closure.
     - **Unit 3 (DP)**: 0/1 Knapsack (investigation prioritization), Longest Common Subsequence (transaction pattern matching), Matrix Chain Multiplication, Resource Allocation.
     - **Unit 4 (Backtracking & Branch & Bound)**: Graph Coloring (conflict-free analyst scheduling), N-Queen, Hamiltonian Cycle, Sum of Subsets, TSP Branch & Bound.
     - **Unit 5**: Red-Black Tree, B-Tree, B+ Tree, Binomial Heap, Fibonacci Heap.

6. **Analyst Portal & Case Management**:
   - **Executive Dashboard**: KPI stat cards, risk distributions, 7-day transaction velocity trends, recent alerts.
   - **Transactions Explorer**: Full search, filtering by status, pagination, and sorting.
   - **Transaction Deep-Dive**: Entity relationship cards, ML probability breakdown, and SHAP factor attribution.
   - **Fraud Alerts**: Severity ranking (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) with triage status toggles.
   - **Investigation Cases**: Workflow tracking (`OPEN`, `UNDER_REVIEW`, `ESCALATED`, `RESOLVED`, `FALSE_POSITIVE`) with collaborative analyst notes and priority levels.
   - **Reports & Analytics**: Volume trends, approval rates, merchant risk breakdown, and infrastructure analytics.

---

## 3. Technology Stack

- **Frontend**: React 19, Vite 8, React Router 7, Recharts, @xyflow/react (Graph Visualizer), Axios, Vanilla CSS design system (Inter typography, navy security palette, zero AI-gimmick styling).
- **Backend**: Python 3.14, FastAPI, SQLAlchemy 2, Pydantic v2, SQLite.
- **Machine Learning**: XGBoost, Scikit-Learn, Pandas, NumPy, SHAP, Joblib.

---

## 4. Folder Structure

```
Fraud/
├── backend/
│   ├── app/
│   │   ├── api/                  # REST endpoints (auth, transactions, alerts, investigations, etc.)
│   │   ├── database.py           # SQLite engine & session management
│   │   ├── dsa/                  # Internal DSA algorithms (Units 1 - 5)
│   │   │   ├── trees.py          # BST, AVL, RB-Tree, B-Tree, B+ Tree, Threaded Tree
│   │   │   ├── graph.py          # Adjacency Graph, BFS, DFS, Dijkstra, MST, etc.
│   │   │   ├── heaps.py          # Binomial & Fibonacci Heaps, Max Heap
│   │   │   └── algorithms.py     # DP (Knapsack, LCS), Backtracking, Branch & Bound
│   │   ├── main.py               # FastAPI application entry & CORS
│   │   ├── ml/                   # Machine learning training & inference
│   │   │   ├── generate_dataset.py
│   │   │   ├── feature_engineering.py
│   │   │   ├── preprocessing.py
│   │   │   ├── train_model.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── explain.py
│   │   │   ├── predict.py
│   │   │   └── model_artifacts/  # Serialized models, scalers, and metadata
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic validation schemas
│   │   └── services/             # Core business logic
│   ├── scripts/
│   │   └── seed_database.py      # Demo dataset seeder
│   ├── tests/
│   │   └── test_system.py        # System unit and integration tests
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/           # Navbar, Sidebar, StatCard, Badges, etc.
│   │   ├── pages/                # CustomerPayment, Dashboard, Transactions, Alerts, etc.
│   │   ├── services/             # Axios API client
│   │   ├── App.jsx               # Role-based router & layout
│   │   ├── main.jsx              # React DOM mounting
│   │   └── index.css             # Professional banking CSS design system
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```

---

## 5. Quickstart & Setup Guide

### Prerequisites
- Python 3.10+ (Python 3.12 - 3.14 supported)
- Node.js 18+ and npm

### Step 1: Backend Setup & Dependencies

```bash
cd backend

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Generate Synthetic Dataset & Train ML Model

```bash
# Generate synthetic dataset (20,000 realistic transactions)
python -m app.ml.generate_dataset

# Train the XGBoost Classifier and Isolation Forest pipeline
python -m app.ml.train_model
```

### Step 3: Initialize Database & Seed Demo Data

```bash
python scripts/seed_database.py
```

### Step 4: Run Backend Tests

```bash
python -m unittest tests/test_system.py
```

### Step 5: Start the Backend Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

### Step 6: Frontend Setup & Run

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```
The web application will open at `http://localhost:5173`.

---

## 6. Demo Accounts & Credentials

| Role | Username | Password | Access Description |
| :--- | :--- | :--- | :--- |
| **Fraud Analyst** | `analyst` | `password123` | Dashboard, Live Alerts, Network Graph, Case Management, Reports |
| **Administrator** | `admin` | `password123` | Full administrative visibility, Model Health, System Config |
| **Customer** | `customer1` | `password123` | Clean Payment Simulation Checkout, Personal Transaction History |
| **Customer** | `customer2` | `password123` | Clean Payment Simulation Checkout, Personal Transaction History |

---

## 7. API Reference Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate user and receive token |
| `POST` | `/api/payments/check` | Real-time payment screening & risk scoring |
| `GET` | `/api/transactions` | Query filtered & paginated transactions |
| `GET` | `/api/transactions/{id}` | Inspect single transaction with ML attribution |
| `GET` | `/api/dashboard/stats` | Executive metrics, fraud trends & risk summary |
| `GET` | `/api/alerts` | List detected fraud alerts with severity |
| `PATCH`| `/api/alerts/{id}` | Update alert triage status |
| `POST` | `/api/investigations` | Open new fraud investigation case |
| `GET` | `/api/investigations` | List investigation cases |
| `PATCH`| `/api/investigations/{id}` | Update investigation status |
| `POST` | `/api/investigations/{id}/notes`| Add notes to case |
| `GET` | `/api/network/{tx_id}` | Generate entity relationship graph |
| `GET` | `/api/ml/model-info` | Read active model metadata and feature weights |
| `GET` | `/api/reports/summary` | Global statistical breakdown for reporting |
| `GET` | `/api/health` | Healthcheck and model readiness check |

---

## 8. Simulated Environment Notice

This platform is a prototype built for fraud detection demonstration, security operations research, and algorithmic analysis. It simulates payment gateway transactions and does not process real fiat currency or connect to live interbank settlement networks.
