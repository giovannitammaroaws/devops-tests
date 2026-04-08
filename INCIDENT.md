# Incident Runbook (Numbered)

## Incident 1: Pods are not Ready or do not start

### Symptoms
- Pod status is not healthy (`Pending`, `ImagePullBackOff`, `CrashLoopBackOff`, `Error`)
- Pod `READY` column is not `1/1` (or expected container count)

### Triage commands
```powershell
k get po -o wide
k describe po <pod-name>
k logs <pod-name> --all-containers=true
k logs <pod-name> --all-containers=true --previous
k get events --sort-by=.metadata.creationTimestamp
```

### What to look for
- Image pull failures (`ErrImagePull`, `ImagePullBackOff`)
- Probe failures (readiness/liveness)
- Crash reasons in logs
- Scheduling issues (resources, taints, node problems)

### Typical fixes
- Use a reachable image/registry.
- Fix container command, env vars, secrets, or config mounts.
- Fix readiness/liveness probe path/port/timeouts.
- Fix requests/limits if scheduling is blocked.

### Exit criteria
- Pods move to `Running`
- Pod readiness becomes healthy (`READY` expected value)

---

## Incident 2: Pods are Running but app is not reachable

### Symptoms
- Pods are `Running`
- External request fails (`404`, `503`, timeout)

### Triage commands (strict order)
```powershell
k get po --show-labels
k get svc myapp-stable -o yaml
k get ep myapp-stable -o wide
k get ing myapp-ing -o yaml
curl.exe -i -H "Host: myapp.local" http://localhost:8080
docker ps --filter "name=k3d-sim-alb-serverlb" --format "table {{.Names}}`t{{.Ports}}"
```

### Decision logic
- If `Endpoints` is `<none>`:
  - `Service -> Pod` mapping is broken (selector mismatch or pods not Ready)
- If `Endpoints` is populated but response is `404`:
  - check Ingress host/path/class/backend mapping
- If request does not reach at all:
  - check LB port mapping and local network path

### Root cause seen in this lab
- `Service/myapp-stable` selector was wrong:
  - `app: wrong-label`
- Real pod labels were:
  - `app: myapp`

Effect:
- service had no endpoints
- ingress had no usable backend
- external request returned `404`

### Fix applied in this lab
Source file:
- `services/myapp-stable.yaml`

Correct definition:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-stable
spec:
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 80
```

Apply and verify:
```powershell
k apply -f .\services\myapp-stable.yaml
k get ep myapp-stable -o wide
curl.exe -i -H "Host: myapp.local" http://localhost:8080
```

### Exit criteria
- Service endpoints are populated
- External request returns `HTTP/1.1 200 OK`

---

## Incident 3: Ingress is broken

### Symptoms
- Pods are `Running`
- Service endpoints are populated
- External request still fails (`404` or `503`)

### Triage commands (strict order)
```powershell
k get po -o wide
k get ep myapp-stable -o wide
k get ing myapp-ing -o yaml
k get svc myapp-stable -o yaml
curl.exe -i -H "Host: myapp.local" http://localhost:8080
```

### Case 3.1: Wrong backend service name in Ingress
Example bad config:
```yaml
backend:
  service:
    name: myapp-stable-typo
    port:
      number: 80
```

Expected behavior:
- Ingress cannot route to the intended service
- request fails (`404` or `503` depending on controller behavior)

Fix:
```yaml
backend:
  service:
    name: myapp-stable
    port:
      number: 80
```

Apply and verify:
```powershell
k apply -f .\ingress\myapp-ing.yaml
curl.exe -i -H "Host: myapp.local" http://localhost:8080
```

### Case 3.2: Wrong backend service port in Ingress
Example bad config:
```yaml
backend:
  service:
    name: myapp-stable
    port:
      number: 81
```

Expected behavior:
- Ingress points to a non-existing/wrong service port
- request fails (`404`, `502`, or `503` depending on controller behavior)

Fix:
```yaml
backend:
  service:
    name: myapp-stable
    port:
      number: 80
```

Apply and verify:
```powershell
k apply -f .\ingress\myapp-ing.yaml
curl.exe -i -H "Host: myapp.local" http://localhost:8080
```

### Exit criteria
- Ingress backend points to `myapp-stable:80`
- Request returns `HTTP/1.1 200 OK`
