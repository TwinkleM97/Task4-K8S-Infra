# Task 4 - K8s Infra Monitoring with SigNoz

This project demonstrates how to deploy telemetry infrastructure in Kubernetes using the **SigNoz `k8s-infra` Helm chart**, and send logs, traces, and metrics from your apps to a SigNoz instance running separately via Docker.

---

## Purpose

The goal of this task was to:
- Deploy the `k8s-infra` Helm chart to Kubernetes using Ansible
- Configure telemetry to flow from Kubernetes to a standalone SigNoz instance
- Monitor a sample instrumented application (`rolldice`) and a demo app (`HotROD`)
- Use SigNoz to observe traces and metrics in a central dashboard

---

## What We Achieved

- Installed SigNoz via Docker (`signoz/deploy/docker`) on the local machine
- Deployed Kubernetes using `kind`
- Automated `k8s-infra` Helm chart install using Ansible (`up.yaml`)
- Deployed and instrumented two applications:
  - `HotROD` (pre-instrumented demo app)
  - `RollDice` (custom Flask app with OpenTelemetry)
- Successfully forwarded telemetry from Kubernetes to the external SigNoz
- Accessed:
  - RollDice API at [http://localhost:8088](http://localhost:8088)
  - SigNoz dashboard at [http://localhost:8080](http://localhost:8080)

---

## Setup Commands

```bash
# 1. Clone SigNoz and run Docker-based backend
git clone https://github.com/SigNoz/signoz.git
cd signoz/deploy/docker
docker-compose up -d

# Return back to the main folder

cd "$(git rev-parse --show-toplevel)"
cd ..

# 2. Install Ansible
sudo apt update
sudo apt install -y ansible

# 3. Install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# 4. Create kind cluster
kind create cluster --name kind
kubectl get nodes

# 5. Run Ansible playbook to install k8s-infra and apps
ansible-playbook ansible/up.yml

# 6. Port forward RollDice app and SigNoz UI
kubectl port-forward svc/rolldice -n platform 8088:5000
```

---

## SigNoz Dashboards

- You can view collected telemetry in SigNoz under:
  - **Traces** → Filter by `service.name = rolldice`
  - **Metrics** → View request count, latency, and errors
  - **Logs** (if configured)

---

## Cleanup

To uninstall all resources:

```bash
ansible-playbook ansible/down.yml
kind delete cluster
docker-compose down
```

---

## Notes

- This setup uses `signoz/k8s-infra` to ship telemetry **from K8s to external SigNoz**
- The SigNoz frontend runs via Docker and is **not** deployed inside Kubernetes
