# CloudPilot – Intelligent Cloud Resource Optimization (Simple Django Version)

CloudPilot is an educational cloud-resource optimization simulator built with Django, SQLite and Scikit-learn. It provides a local dashboard for simulated servers, accepts workload readings, predicts next-interval CPU and memory utilization, recommends a VM size, estimates monthly cost, and records alerts.

**No AWS/Azure account, API key, billing account, Docker or paid service is required.** This version does not change real infrastructure. All scaling actions are recommendations and simulator records only.

## Included features

1. Dashboard with server count, CPU/memory averages, open alerts and workload trend chart.
2. Add simulated servers with Small, Medium and Large instance profiles.
3. Add workload readings for CPU, memory, disk, network and requests per second.
4. ML forecasts for next-interval CPU and memory utilization.
5. Scaling-action classification (scale up / maintain / scale down).
6. Anomaly detection with Isolation Forest.
7. Rule-based VM right-sizing recommendation with illustrative cost comparison.
8. Auto-scaling simulation: recommendations are saved as history; no real VM is started or stopped.
9. Alert generation and resolve action.
10. SQLite database, admin interface, seed-data command and automated Django tests.
11. Included synthetic training CSV and pre-trained sample model files; models can be retrained locally.

## Technology

- Python 3.11 or later
- Django 5.2
- SQLite
- Pandas, NumPy, Scikit-learn and Joblib
- HTML, CSS and vanilla JavaScript (charts are drawn locally without a chart CDN)

## Project layout

```text
CloudPilot_Django/
├── manage.py
├── requirements.txt
├── README.md
├── MANUAL_SETUP_WINDOWS.md
├── cloudpilot/                 # Django project settings and URLs
├── monitoring/                 # Models, forms, views, ML pipeline, tests
│   ├── management/commands/    # seed_demo_data and train_cloud_models
│   └── migrations/
├── templates/                  # Django templates
├── static/                     # CSS and JavaScript
├── data/                       # Included synthetic training dataset
└── ml_models/                  # Pre-trained Scikit-learn model artifacts
```

## Quick start (Windows PowerShell)

See [MANUAL_SETUP_WINDOWS.md](MANUAL_SETUP_WINDOWS.md) for the full commands. In summary:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py train_cloud_models
python manage.py check
python manage.py test
python manage.py runserver
```

Open http://127.0.0.1:8000/.

## First-time workflow

1. Start the server and open the dashboard.
2. Demo servers and historical readings appear after running `seed_demo_data`.
3. Use **Add server** to register another simulated VM.
4. Use **Add a workload reading** to submit updated utilization values.
5. Click **Optimize** on a server to generate a workload forecast and VM-size recommendation.
6. Open **ML models** to view the model list and training evaluation.
7. Review alerts and mark them resolved when reviewed.

## ML pipeline

Run:

```powershell
python manage.py train_cloud_models
```

The command reads `data/cloud_workload_training.csv` and creates/updates four artifacts under `ml_models/`:

- `cpu_regressor.joblib`: Random Forest regression model for next-interval CPU utilization.
- `memory_regressor.joblib`: Random Forest regression model for next-interval memory utilization.
- `scaling_classifier.joblib`: Decision Tree classifier for the scaling action label.
- `anomaly_detector.joblib`: Isolation Forest anomaly detector.
- `training_metrics.json`: held-out test metrics.

The app converts the predicted utilization into approximate required vCPU and RAM at safe target utilization levels (70% CPU and 75% RAM). A* searches the VM-size graph for the smallest feasible profile; Greedy Best-First is run as a comparison. The classifier output is also shown in the recommendation note when it differs from the search-based result.

## Cost calculation

The simulator uses illustrative instance prices:

| Size | vCPU | RAM | Sample hourly price | Approx. monthly price (730 h) |
|---|---:|---:|---:|---:|
| Small | 2 | 4 GB | $0.12 | $87.60 |
| Medium | 4 | 8 GB | $0.24 | $175.20 |
| Large | 8 | 16 GB | $0.48 | $350.40 |

These are made-up classroom simulator rates, not live AWS/Azure prices. You can edit them in `monitoring/forms.py` and `monitoring/ml.py` if you want to demonstrate a different pricing model.

## Data notes and limitations

- The bundled 1,200-row training dataset and demo readings are synthetic. They are suitable for offline demonstrations, not for production decisions.
- The training metrics only describe performance on a held-out section of this synthetic dataset. They do not establish real-world cloud prediction accuracy.
- No real cloud metrics are collected in this simple version. AWS CloudWatch/Azure Monitor connectors can be added as a future extension with user-provided credentials and permissions.
- No infrastructure is automatically scaled. All actions are recommendations recorded in the local database.
- The anomaly detector may flag unusual combinations, not confirmed outages or attacks.

## Django admin (optional)

Create an administrator account:

```powershell
python manage.py createsuperuser
```

Then visit http://127.0.0.1:8000/admin/.

## Troubleshooting

**`py` is not recognized:** Install Python 3.11+ and enable “Add Python to PATH”, then reopen PowerShell.

**PowerShell blocks activation:** Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate the environment again.

**`No module named django`:** Activate `.venv`, then run `pip install -r requirements.txt`.

**Model artifacts cannot load after changing Scikit-learn versions:** Run `python manage.py train_cloud_models` to rebuild the artifacts using your installed version.

**Dashboard is empty:** Run `python manage.py seed_demo_data`.

**Port 8000 is busy:** Run `python manage.py runserver 8001` and open http://127.0.0.1:8001/.

## Academic scope

This project demonstrates a small end-to-end ML application: data ingestion, preprocessing, supervised regression/classification, unsupervised anomaly detection, a recommendation layer, persistence, dashboard visualization and testing. For a stronger research evaluation, replace the synthetic CSV with a properly licensed public cloud workload trace, document preprocessing, and compare predictions against a time-ordered holdout set.
