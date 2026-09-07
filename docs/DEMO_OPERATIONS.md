# Synthetic demo operations

This release target is a reproducible portfolio demonstration for engineering review. It is not approved for customer records, payroll decisions, or regulated workloads. No hosted URL is provisioned by this repository.

## Start and verify

Run on a Docker host with at least 2 GB free RAM:

```sh
docker compose -f compose.demo.yml config --quiet
docker compose -f compose.demo.yml up --build -d --wait
python scripts/smoke_demo.py
```

Open http://localhost:8080. The standalone Compose file uses the `aws-demo` route profile with the **fake deterministic model**; the profile name does not provision AWS. No credentials or model charges are required. Uploaded documents, payroll uploads, stored-run retrieval, and API explorers are disabled. BankOps and AwardLens use only bundled synthetic fixtures.

The API runs as UID 10001 with a read-only filesystem, a bounded temporary filesystem, dropped Linux capabilities, and limits on memory, CPU, process count, and concurrent connections. The web proxy limits request bodies, request rates, connection counts and timeouts, and sends browser security headers. Logs rotate. Rate limits are per source IP as seen by nginx; behind another proxy, users may share that budget. Do not trust arbitrary forwarded client-IP headers.

Readiness checks the BankOps schema, initializes retrieval and the AwardLens fixture, and verifies the evaluation report checksum. It returns 503 on failure without returning local paths. Liveness stays separate. Readiness does not prove the availability or quality of an optional live model provider.

## Before publishing a hosted URL

1. Choose a host and domain, configure HTTPS, and forward only to the web listener on `127.0.0.1:8080`. Keep the API and database private. Do not expose the default development Compose configuration.
2. Run the smoke check against the actual HTTPS URL and exercise both workflows in a browser. Review the host's firewall, patching, container image vulnerability scan, resource usage and costs.
3. Configure an external uptime check for `/health/ready`, log retention and an owner who receives failures. Container health alone does not restart an unhealthy process; the restart policy covers process exits.
4. Test expected concurrent traffic on the chosen host. The repository's CI smoke test is not a capacity or availability guarantee.
5. Keep the deterministic provider for an anonymous portfolio demo. Switching to a live provider requires separate quality evaluation, explicit timeouts, quotas, credential management and abuse/cost controls.

## Release evidence

CI runs backend tests, frontend tests and build, desktop/mobile browser flows, a real PostgreSQL/pgvector integration test, and both container configurations. The restricted demo smoke check exercises real HTTP responses for readiness, safe routes, chat, audit, browser security headers, oversized-body rejection and rate limiting. It also checks that the API container is not root. The frontend dependency audit fails CI on high-severity findings.

The 40-case evaluation uses a deterministic fake model. Passing it demonstrates the tested routing, guardrails, tools and report integrity; it is not a live-LLM accuracy result. See CI for the result on the commit you intend to run.

## Recovery and rollback

Inspect `docker compose -f compose.demo.yml ps` and `docker compose -f compose.demo.yml logs --tail 100`. Readiness failures require checking fixtures and the bundled report; do not bypass the health check. To roll back, check out the previously verified commit and rerun the build/start command, then repeat the smoke and browser checks. This is a single-host restart with downtime, not a zero-downtime deployment.

Stop with `docker compose -f compose.demo.yml down`. The demo holds no customer data and requires no persistent database volume.
