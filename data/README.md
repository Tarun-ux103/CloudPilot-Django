# CloudPilot sample data

`cloud_workload_training.csv` contains 1,200 synthetic workload observations and labels. It is included so the project can train and run offline after Python dependencies are installed.

Columns:

- `cpu_utilization`, `memory_utilization`, `disk_utilization`: current utilization percentages.
- `network_mbps`: network throughput estimate.
- `requests_per_second`: simulated application request rate.
- `hour`: hour of day (0–23).
- `next_cpu_utilization`, `next_memory_utilization`: synthetic next-interval targets.
- `scaling_action`: synthetic target label (`scale_up`, `maintain`, or `scale_down`).

These values are generated for demonstration and are not measurements from AWS, Azure, Google Cloud or a production environment.

For academic extensions, public cloud workload traces can be collected from sources such as the Alibaba Cluster Trace Program or Google ClusterData. Inspect each source's terms and format before using or redistributing its files. The included training pipeline expects the column names above; preprocess external traces into this schema before training.
