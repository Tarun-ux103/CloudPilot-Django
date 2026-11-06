"""Small ML pipeline for CloudPilot's local cloud-resource simulator."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report
from .search_algorithms import astar_vm_search, best_first_vm_search, path_between_vm_sizes

FEATURES = ['cpu_utilization', 'memory_utilization', 'disk_utilization', 'network_mbps', 'requests_per_second', 'hour']
VM_PLANS = {
    'small': {'vcpu': 2, 'ram_gb': 4, 'rate': 0.12},
    'medium': {'vcpu': 4, 'ram_gb': 8, 'rate': 0.24},
    'large': {'vcpu': 8, 'ram_gb': 16, 'rate': 0.48},
}
VM_ORDER = ['small', 'medium', 'large']
HOURS_PER_MONTH = 730


def train_all(dataset_path, model_dir):
    dataset_path = Path(dataset_path)
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(dataset_path)
    required = set(FEATURES + ['next_cpu_utilization', 'next_memory_utilization', 'scaling_action'])
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f'Dataset is missing columns: {", ".join(sorted(missing))}')

    X = data[FEATURES].astype(float)
    y_cpu = data['next_cpu_utilization'].astype(float)
    y_mem = data['next_memory_utilization'].astype(float)
    X_train, X_test, cpu_train, cpu_test, mem_train, mem_test = train_test_split(
        X, y_cpu, y_mem, test_size=0.2, random_state=42
    )

    cpu_model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    mem_model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    cpu_model.fit(X_train, cpu_train)
    mem_model.fit(X_train, mem_train)

    action_model = DecisionTreeClassifier(max_depth=5, random_state=42, class_weight='balanced')
    action_model.fit(X_train, data.loc[X_train.index, 'scaling_action'])
    anomaly_model = IsolationForest(contamination=0.04, random_state=42, n_estimators=100)
    anomaly_model.fit(X)

    joblib.dump(cpu_model, model_dir / 'cpu_regressor.joblib', compress=3)
    joblib.dump(mem_model, model_dir / 'memory_regressor.joblib', compress=3)
    joblib.dump(action_model, model_dir / 'scaling_classifier.joblib', compress=3)
    joblib.dump(anomaly_model, model_dir / 'anomaly_detector.joblib', compress=3)

    cpu_prediction = cpu_model.predict(X_test)
    mem_prediction = mem_model.predict(X_test)
    action_prediction = action_model.predict(X_test)
    metrics = {
        'rows': int(len(data)),
        'features': FEATURES,
        'cpu_mae': round(float(mean_absolute_error(cpu_test, cpu_prediction)), 3),
        'cpu_r2': round(float(r2_score(cpu_test, cpu_prediction)), 3),
        'memory_mae': round(float(mean_absolute_error(mem_test, mem_prediction)), 3),
        'memory_r2': round(float(r2_score(mem_test, mem_prediction)), 3),
        'action_accuracy': round(float(accuracy_score(data.loc[X_test.index, 'scaling_action'], action_prediction)), 3),
        'action_report': classification_report(data.loc[X_test.index, 'scaling_action'], action_prediction, output_dict=True, zero_division=0),
        'trained_models': ['RandomForestRegressor (CPU)', 'RandomForestRegressor (memory)', 'DecisionTreeClassifier (scaling action)', 'IsolationForest (anomaly detection)'],
    }
    (model_dir / 'training_metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    return metrics


def make_prediction(metric, model_dir):
    """Predict the next interval and return a basic right-sizing recommendation."""
    model_dir = Path(model_dir)
    features = pd.DataFrame([{
        'cpu_utilization': float(metric.cpu_utilization),
        'memory_utilization': float(metric.memory_utilization),
        'disk_utilization': float(metric.disk_utilization),
        'network_mbps': float(metric.network_mbps),
        'requests_per_second': float(metric.requests_per_second),
        'hour': float(metric.recorded_at.hour),
    }], columns=FEATURES)

    cpu_file = model_dir / 'cpu_regressor.joblib'
    mem_file = model_dir / 'memory_regressor.joblib'
    action_file = model_dir / 'scaling_classifier.joblib'
    anomaly_file = model_dir / 'anomaly_detector.joblib'
    if all(path.exists() for path in [cpu_file, mem_file, action_file, anomaly_file]):
        cpu_model = joblib.load(cpu_file)
        mem_model = joblib.load(mem_file)
        action_model = joblib.load(action_file)
        anomaly_model = joblib.load(anomaly_file)
        predicted_cpu = float(np.clip(cpu_model.predict(features)[0], 0, 100))
        predicted_memory = float(np.clip(mem_model.predict(features)[0], 0, 100))
        predicted_action = str(action_model.predict(features)[0])
        anomaly = bool(anomaly_model.predict(features)[0] == -1)
        model_ready = True
    else:
        # Transparent fallback so the app remains usable before model training.
        predicted_cpu = float(np.clip(metric.cpu_utilization * 1.04 + metric.requests_per_second / 500, 0, 100))
        predicted_memory = float(np.clip(metric.memory_utilization * 1.03 + metric.network_mbps / 200, 0, 100))
        predicted_action = 'scale_up' if predicted_cpu >= 75 or predicted_memory >= 80 else ('scale_down' if predicted_cpu < 25 and predicted_memory < 35 else 'maintain')
        anomaly = bool(metric.cpu_utilization >= 95 or metric.memory_utilization >= 95 or metric.disk_utilization >= 97)
        model_ready = False

    current_vm = metric.server.vm_type
    current_index = VM_ORDER.index(current_vm)
    # Translate forecast utilization into approximate demand at 70% CPU / 75% RAM targets.
    required_vcpu = metric.server.vcpu * predicted_cpu / 70.0
    required_ram = metric.server.ram_gb * predicted_memory / 75.0
    astar_result = astar_vm_search(required_vcpu, required_ram)
    best_first_result = best_first_vm_search(required_vcpu, required_ram)
    recommended_vm = astar_result['target']
    action = 'scale_up' if VM_ORDER.index(recommended_vm) > current_index else ('scale_down' if VM_ORDER.index(recommended_vm) < current_index else 'maintain')
    placement_path = path_between_vm_sizes(current_vm, recommended_vm)

    current_rate = float(metric.server.hourly_rate)
    recommended_rate = VM_PLANS[recommended_vm]['rate']
    current_cost = current_rate * HOURS_PER_MONTH
    recommended_cost = recommended_rate * HOURS_PER_MONTH
    savings = current_cost - recommended_cost
    note = {
        'scale_up': 'Forecast workload is high. Consider moving to the next VM size.',
        'scale_down': 'Forecast workload is low. A smaller VM may reduce estimated cost.',
        'maintain': 'Current VM size appears suitable for the predicted workload.',
    }[action]
    note += f' A* placement path: {" → ".join(placement_path)}.'
    note += f' Best-First search candidate: {best_first_result["target"]}.'
    if not astar_result['feasible']:
        note += ' The largest demo VM may still be insufficient; review capacity manually.'
    if predicted_action != action and model_ready:
        note += f' The classifier also evaluated the workload as {predicted_action.replace("_", " ")}; the VM recommendation follows the capacity-search result.'

    return {
        'predicted_cpu': round(predicted_cpu, 1),
        'predicted_memory': round(predicted_memory, 1),
        'action': action,
        'recommended_vm': recommended_vm,
        'current_monthly_cost': round(current_cost, 2),
        'recommended_monthly_cost': round(recommended_cost, 2),
        'estimated_monthly_savings': round(savings, 2),
        'anomaly_detected': anomaly,
        'model_ready': model_ready,
        'note': note[:240],
    }
