# Kubernetes Troubleshooting Lab (k3d)

## Goal
Practice troubleshooting in a repeatable order, from workload health to external reachability.

Lab stack:
- local `k3d` cluster
- Traefik Ingress controller
- `nginx` app

## Incident index
1. Incident 1: Pods are not `Ready` or do not start.
2. Incident 2: Pods are `Running` but the app is not reachable from outside.
3. Incident 3: Ingress is broken (wrong backend service name or backend service port).
4. Incident 4: Ingress class mismatch (`ingressClassName` does not match the active controller).

## Incident 1 (Pods not Ready / not starting)
Start here when pods are in states like `Pending`, `ImagePullBackOff`, `CrashLoopBackOff`, `Error`.

```powershell
k get po -o wide
k describe po <pod-name>
k logs <pod-name> --all-containers=true
k logs <pod-name> --all-containers=true --previous
k get events --sort-by=.metadata.creationTimestamp
```

Tip:
- If pods are not `Ready`, services can still show empty endpoints.

## Incident 2 (Pods Running, app unreachable)
Use this when pods look healthy but external requests fail (`404`, `503`, timeout).

```powershell
k get po --show-labels
k get svc myapp-stable -o yaml
k get ep myapp-stable -o wide
k get ing myapp-ing -o yaml
curl.exe -i -H "Host: myapp.local" http://localhost:8080
docker ps --filter "name=k3d-sim-alb-serverlb" --format "table {{.Names}}`t{{.Ports}}"
```

## Incident 3 (Broken Ingress)
Use this when pods and service look healthy, but routing through Ingress fails.

Common causes covered in this lab:
- wrong backend service name in Ingress (for example `myapp-stable-typo`)
- wrong backend service port in Ingress (for example `81` instead of `80`)

## Incident 4 (Ingress Class Mismatch)
Use this when Ingress exists but is not processed by the expected controller.

Example:
- expected class: `traefik`
- misconfigured class: `nginx`

Quick checks:
```powershell
k get ingressclass
k get ing myapp-ing -o yaml
curl.exe -i -H "Host: myapp.local" http://localhost:8080
```

Fix:
- set `ingressClassName: traefik` in `ingress/myapp-ing.yaml`
- re-apply the manifest

## Traffic flow
`Client -> localhost:8080 -> k3d loadbalancer -> Ingress -> Service -> Pod`

## Known root cause from this lab
- Wrong service selector (`app: wrong-label`) caused:
  - `Endpoints <none>`
  - Ingress had no usable backend
  - external response was `404`

Fix file:
- `services/myapp-stable.yaml`

## Full runbook
See `INCIDENT.md` for the full numbered runbook with decision steps and fixes.
