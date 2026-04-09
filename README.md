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
5. Incident 5: NetworkPolicy blocks traffic to app pods (`502 Bad Gateway` from Ingress).

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

Realtime steps:
1. Run `k get ingressclass` and confirm the active class is `traefik`.
2. Check `ingressClassName` in `myapp-ing`.
3. If class is wrong (for example `nginx`), requests will fail even if pods and service are healthy.

Important note:
- `PARAMETERS: <none>` in `k get ingressclass` is normal for this Traefik setup.
- Treat class name/controller mismatch as the real issue, not `PARAMETERS: <none>`.

Fix:
- set `ingressClassName: traefik` in `ingress/myapp-ing.yaml`
- re-apply the manifest

## Incident 5 (NetworkPolicy Blocking Pod Traffic)
Use this when Ingress exists and routes, but backend traffic to pods is blocked by policy.

Quick checks:
```powershell
k get netpol
curl.exe -i -H "Host: myapp.local" http://localhost:8080
```

Example from this lab:
```text
NAME                  POD-SELECTOR   AGE
allow-http-to-myapp   app=myapp      71s
deny-all-to-myapp     app=myapp      5m4s
```

Typical symptom:
- request returns `HTTP/1.1 502 Bad Gateway`

Files used in this lab:
- `networkpolicy/deny-myapp.yaml`
- `networkpolicy/allow-http-myapp.yaml`

Commands used:
```powershell
k apply -f .\networkpolicy\deny-myapp.yaml
k apply -f .\networkpolicy\allow-http-myapp.yaml
k get netpol
curl.exe -i -H "Host: myapp.local" http://localhost:8080
```

Recovery shortcut:
```powershell
k delete netpol deny-all-to-myapp
curl.exe -i -H "Host: myapp.local" http://localhost:8080
```

## Traffic flow
`Client -> localhost:8080 -> k3d loadbalancer -> Ingress -> Service -> Pod`

## In-cluster DNS test (from Pod, not from Node)
Use this to validate Kubernetes service discovery and internal service reachability.

Run from a temporary pod:
```powershell
k run -it --rm dns-test --image=busybox:1.36 --restart=Never -- sh
```

Inside the pod:
```sh
nslookup myapp-stable
wget -qO- http://myapp-stable
```

Important:
- run DNS/service tests from a pod, not from a k3d node container
- partial `NXDOMAIN` lines from busybox `nslookup` are normal if the fully-qualified service name resolves successfully

## Known root cause from this lab
- Wrong service selector (`app: wrong-label`) caused:
  - `Endpoints <none>`
  - Ingress had no usable backend
  - external response was `404`

Fix file:
- `services/myapp-stable.yaml`

## Full runbook
See `INCIDENT.md` for the full numbered runbook with decision steps and fixes.
