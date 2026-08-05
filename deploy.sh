#!/usr/bin/env bash
set -euo pipefail

# ─── Colors ────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BLUE='\033[1;34m'; NC='\033[0m'
log()   { echo -e "${CYAN}[deploy]${NC}  $*"; }
ok()    { echo -e "${GREEN}[  ok  ]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[warn ]${NC}  $*"; }
fail()  { echo -e "${RED}[fail ]${NC}  $*" >&2; exit 1; }
step()  { echo ""; echo -e "${BLUE}══════ $* ══════${NC}"; }

# ─── Config ────────────────────────────────────────────
REGION="ap-south-1"
CLUSTER_NAME="pokemission"
NAMESPACE="pokemission"
TERRAFORM_DIR="$(cd "$(dirname "$0")" && pwd)/terraform"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_DIR"

# ─── Spinner ───────────────────────────────────────────
spinner() {
  local pid=$1; local msg=$2; local delay=0.3
  local chars=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local i=0
  while kill -0 "$pid" 2>/dev/null; do
    printf "\r${CYAN}[deploy]${NC}  %s ${chars[$i]} " "$msg"
    i=$(( (i + 1) % 10 ))
    sleep $delay
  done
  printf "\r${CYAN}[deploy]${NC}  %s ✓\n" "$msg"
  wait "$pid"
  return $?
}

# ─── Cleanup ───────────────────────────────────────────
cleanup() {
  echo ""
  step "CLEANUP"

  if kubectl get ns "$NAMESPACE" &>/dev/null 2>&1; then
    log "Deleting Kubernetes namespace '$NAMESPACE' (this drains all pods)..."
    kubectl delete namespace "$NAMESPACE" --timeout=120s
    ok "Namespace '$NAMESPACE' deleted"
  else
    log "Namespace '$NAMESPACE' not found, skipping"
  fi

  log "Destroying all Terraform-managed infrastructure..."
  cd "$TERRAFORM_DIR"
  terraform destroy -auto-approve
  ok "Terraform destroy complete"

  cd "$PROJECT_DIR"
  echo ""
  echo -e "${GREEN}══════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  Cleanup complete — all AWS resources removed${NC}"
  echo -e "${GREEN}══════════════════════════════════════════════${NC}"
  exit 0
}

# ─── Help ──────────────────────────────────────────────
usage() {
  echo "Usage: $0 [deploy|cleanup]"
  echo ""
  echo "  deploy   (default) Provision infrastructure and deploy app"
  echo "  cleanup  Delete namespace + terraform destroy"
  exit 1
}

ACTION="${1:-deploy}"

case "$ACTION" in
  cleanup) cleanup ;;
  deploy)  ;;
  *)       usage ;;
esac

# ═══════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}  ╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ║       PokéMission — AWS EKS Deploy          ║${NC}"
echo -e "${GREEN}  ╚══════════════════════════════════════════════╝${NC}"
echo ""

# ═══════════════════════════════════════════════════════
step "0 — PREREQUISITES"

log "Checking: terraform..."
command -v terraform >/dev/null 2>&1 || fail "terraform not found"
ok "terraform $(terraform --version | head -1)"

log "Checking: kubectl..."
command -v kubectl >/dev/null 2>&1 || fail "kubectl not found"
ok "kubectl $(kubectl version --client --short 2>&1)"

log "Checking: docker..."
command -v docker >/dev/null 2>&1 || fail "docker not found"
ok "docker $(docker --version)"

log "Checking: aws CLI..."
command -v aws >/dev/null 2>&1 || fail "aws CLI not found"
ACCOUNT_ID=$(aws sts get-caller-identity --no-cli-pager --query Account --output text)
ok "aws CLI authenticated — Account: $ACCOUNT_ID"

# ═══════════════════════════════════════════════════════
step "1 — TERRAFORM APPLY (VPC, EKS, RDS, ECR, IAM)"

log "Initializing Terraform..."
cd "$TERRAFORM_DIR"
terraform init -upgrade
ok "Terraform initialized"

log "Applying Terraform (this takes ~10-15 min for EKS + RDS)..."
echo ""
terraform apply -auto-approve
echo ""
ok "Terraform apply complete — all AWS resources created"

# ═══════════════════════════════════════════════════════
step "2 — CAPTURE OUTPUTS"

log "Reading Terraform outputs..."
ECR_FRONTEND=$(terraform output -raw ecr_frontend_url)
ECR_MISSION=$(terraform output -raw ecr_mission_service_url)
ECR_SUBSCRIBER=$(terraform output -raw ecr_subscriber_service_url)
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
KUBECONFIG_CMD=$(terraform output -raw configure_kubectl)
CREATE_SECRET_CMD=$(terraform output -raw create_db_secret_command)
ECR_LOGIN_CMD=$(terraform output -raw login_to_ecr_command)

echo ""
log "ECR Frontend:          $ECR_FRONTEND"
log "ECR Mission Service:   $ECR_MISSION"
log "ECR Subscriber Service: $ECR_SUBSCRIBER"
log "RDS PostgreSQL:        $RDS_ENDPOINT"
ok "Outputs captured"

cd "$PROJECT_DIR"

# ═══════════════════════════════════════════════════════
step "3 — KUBECTL CONFIG"

log "Running: aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION"
eval "$KUBECONFIG_CMD"
ok "kubectl configured — context: $(kubectl config current-context)"

log "Checking cluster nodes..."
kubectl get nodes -o wide
NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
ok "$NODE_COUNT node(s) ready"

# ═══════════════════════════════════════════════════════
step "4 — ECR LOGIN"

log "Running: aws ecr get-login-password | docker login..."
eval "$ECR_LOGIN_CMD"
ok "Docker authenticated with ECR"

# ═══════════════════════════════════════════════════════
step "5 — BUILD & PUSH DOCKER IMAGES"

log "Building frontend image..."
docker build -t pokemission-frontend "$PROJECT_DIR/frontend"
log "Tagging: $ECR_FRONTEND:latest"
docker tag pokemission-frontend "$ECR_FRONTEND:latest"
log "Pushing to ECR..."
docker push "$ECR_FRONTEND:latest"
ok "Frontend image pushed"

log "Building mission-service image..."
docker build -t pokemission-mission-service "$PROJECT_DIR/mission-service"
log "Tagging: $ECR_MISSION:latest"
docker tag pokemission-mission-service "$ECR_MISSION:latest"
log "Pushing to ECR..."
docker push "$ECR_MISSION:latest"
ok "Mission-service image pushed"

log "Building subscriber-service image..."
docker build -t pokemission-subscriber-service "$PROJECT_DIR/subscriber-service"
log "Tagging: $ECR_SUBSCRIBER:latest"
docker tag pokemission-subscriber-service "$ECR_SUBSCRIBER:latest"
log "Pushing to ECR..."
docker push "$ECR_SUBSCRIBER:latest"
ok "Subscriber-service image pushed"

# ═══════════════════════════════════════════════════════
step "6 — KUBERNETES NAMESPACE"

log "Creating namespace '$NAMESPACE'..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
ok "Namespace '$NAMESPACE' ready"

# ═══════════════════════════════════════════════════════
step "7 — DATABASE SECRET"

log "Creating K8s secret 'db-secret' from Terraform-generated credentials..."
eval "$CREATE_SECRET_CMD" --dry-run=client -o yaml | kubectl apply -f -
ok "Secret 'db-secret' created"

# ═══════════════════════════════════════════════════════
step "8 — PROCESS MANIFESTS"

log "Copying manifests to temp dir..."
TMPDIR=$(mktemp -d)
cp "$PROJECT_DIR/k8s/"*.yaml "$TMPDIR/"
log "Temp dir: $TMPDIR"

log "Replacing image placeholders with ECR URLs..."
for f in "$TMPDIR"/*.yaml; do
  sed -i "s|<ECR_ACCOUNT>\.dkr\.ecr\.${REGION}\.amazonaws\.com/pokemission-frontend:latest|${ECR_FRONTEND}:latest|g" "$f"
  sed -i "s|<ECR_ACCOUNT>\.dkr\.ecr\.${REGION}\.amazonaws\.com/pokemission-mission-service:latest|${ECR_MISSION}:latest|g" "$f"
  sed -i "s|<ECR_ACCOUNT>\.dkr\.ecr\.${REGION}\.amazonaws\.com/pokemission-subscriber-service:latest|${ECR_SUBSCRIBER}:latest|g" "$f"
  log "  Processed: $(basename "$f")"
done
ok "Image placeholders replaced"

log "Final manifest contents:"
echo ""
for f in "$TMPDIR"/*.yaml; do
  echo -e "${YELLOW}--- $(basename "$f") ---${NC}"
  cat "$f"
  echo ""
done

# ═══════════════════════════════════════════════════════
step "9 — APPLY MANIFESTS"

log "Running: kubectl apply -f $TMPDIR/..."
kubectl apply -f "$TMPDIR/"
rm -rf "$TMPDIR"
ok "All manifests applied"

# ═══════════════════════════════════════════════════════
step "10 — WAIT FOR PODS"

log "Waiting for pods to reach Ready state..."
(
  while true; do
    NUM_PODS=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
    READY=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '$2 == $3' | wc -l)
    if [ "$NUM_PODS" -gt 0 ] && [ "$READY" -eq "$NUM_PODS" ] 2>/dev/null; then
      exit 0
    fi
    sleep 5
  done
) &
spinner $! "Waiting for pods (3 pods: frontend, mission-service, subscriber-service)..."
ok "All pods Ready"

echo ""
kubectl get pods -n "$NAMESPACE" -o wide

# ═══════════════════════════════════════════════════════
step "11 — WAIT FOR ALB DNS"

log "Waiting for AWS Load Balancer to be provisioned..."
(
  for i in $(seq 1 60); do
    URL=$(kubectl get ingress -n "$NAMESPACE" pokemission -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
    if [ -n "$URL" ]; then
      echo "$URL"
      exit 0
    fi
    sleep 10
  done
  exit 1
) &
ALB_URL=$(spinner $! "Waiting for ALB DNS (checking every 10s, up to 10 min)...") || {
  echo ""
  warn "ALB not provisioned after 10 min. Check: kubectl describe ingress -n $NAMESPACE pokemission"
  kubectl describe ingress -n "$NAMESPACE" pokemission
  fail "Giving up"
}

echo ""
log "ALB DNS: $ALB_URL"
ok "Load Balancer provisioned"

# ═══════════════════════════════════════════════════════
step "12 — DNS RESOLUTION"

log "Resolving ALB DNS name..."
for i in $(seq 1 15); do
  IPS=$(dig +short "$ALB_URL" 2>/dev/null | grep '^[0-9]' | paste -sd, || true)
  if [ -n "$IPS" ]; then
    ok "DNS resolved — $ALB_URL → $IPS"
    break
  fi
  if [ "$i" -eq 15 ]; then
    warn "DNS not resolving yet, continuing anyway..."
  else
    log "  Waiting for DNS (attempt $i/15)..."
    sleep 5
  fi
done

# ═══════════════════════════════════════════════════════
step "13 — TARGET GROUP HEALTH"

log "Checking ALB target group health..."
ALB_ARN=$(aws elbv2 describe-load-balancers --region "$REGION" \
  --query "LoadBalancers[?DNSName=='$ALB_URL'].LoadBalancerArn" --output text)
log "ALB ARN: $ALB_ARN"

for i in $(seq 1 30); do
  ALL_HEALTHY=true
  TG_NAMES=$(aws elbv2 describe-target-groups --region "$REGION" \
    --load-balancer-arn "$ALB_ARN" --query 'TargetGroups[*].TargetGroupName' --output text)
  echo ""
  for tg_name in $TG_NAMES; do
    TG_ARN=$(aws elbv2 describe-target-groups --region "$REGION" --names "$tg_name" \
      --query 'TargetGroups[0].TargetGroupArn' --output text)
    STATE=$(aws elbv2 describe-target-health --region "$REGION" --target-group-arn "$TG_ARN" \
      --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text 2>/dev/null || echo "unknown")
    TARGET=$(aws elbv2 describe-target-health --region "$REGION" --target-group-arn "$TG_ARN" \
      --query 'TargetHealthDescriptions[0].Target.Id' --output text 2>/dev/null || echo "-")
    if [ "$STATE" != "healthy" ]; then
      ALL_HEALTHY=false
    fi
    log "  TG: $tg_name → target $TARGET → state: $STATE"
  done
  if [ "$ALL_HEALTHY" = true ]; then
    echo ""
    ok "All target groups healthy"
    break
  fi
  if [ "$i" -lt 30 ]; then
    log "  Not all targets healthy yet, retrying in 10s... (attempt $i/30)"
    sleep 10
  fi
done


# ═══════════════════════════════════════════════════════
step "— DEPLOY COMPLETE —"

echo ""
echo -e "${GREEN}  ╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ║              PokéMission is live!                        ║${NC}"
echo -e "${GREEN}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}  ║  URL:      http://${ALB_URL}${NC}"
echo -e "${GREEN}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}  ║  Endpoints:                                            ║${NC}"
if [ -n "$MISSION_STATUS" ]; then
  echo -e "${GREEN}  ║    ${ALB_URL}/api/mission/health     ${MISSION_STATUS}${NC}"
else
  echo -e "${RED}  ║    /api/mission/health     UNREACHABLE${NC}"
fi
if [ -n "$SUB_STATUS" ]; then
  echo -e "${GREEN}  ║    ${ALB_URL}/api/subscriber/health  ${SUB_STATUS}${NC}"
else
  echo -e "${RED}  ║    /api/subscriber/health  UNREACHABLE${NC}"
fi
if [ "$FRONT_STATUS" = "200" ] || [ "$FRONT_STATUS" = "304" ]; then
  echo -e "${GREEN}  ║    / → HTTP ${FRONT_STATUS}${NC}"
else
  echo -e "${RED}  ║    / → HTTP ${FRONT_STATUS:-UNREACHABLE}${NC}"
fi
echo -e "${GREEN}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}  ║  Cluster:  ${CLUSTER_NAME}${NC}"
echo -e "${GREEN}  ║  Region:   ${REGION}${NC}"
echo -e "${GREEN}  ║  Nodes:    ${NODE_COUNT:-?}${NC}"
echo -e "${GREEN}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}  ║  Commands:                                            ║${NC}"
echo -e "${GREEN}  ║    kubectl get all -n ${NAMESPACE}${NC}"
echo -e "${GREEN}  ║    kubectl logs -n ${NAMESPACE} -l app=mission-service -f${NC}"
echo -e "${GREEN}  ║    kubectl logs -n ${NAMESPACE} -l app=subscriber-service -f${NC}"
echo -e "${GREEN}  ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}  ║  Cleanup:  $0 cleanup                                 ║${NC}"
echo -e "${GREEN}  ╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
