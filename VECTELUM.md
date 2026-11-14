# VECTELUM OS — developer preview

Independent experimental derivative of [Project NOMAD](https://github.com/Crosstalk-Solutions/project-nomad) by Crosstalk Solutions and contributors, licensed Apache-2.0. Original [LICENSE](LICENSE), copyright notices and [upstream README](UPSTREAM-README.md) are retained. No affiliation or endorsement is claimed. Upstream baseline: `c903da48c97bc02f5cdfeff2ebcde00a82dfec8e`.

## Verified local deployment — 14 November 2026

- Source image: `vectelum-os:56350b3`
- Version: `1.35.1-vectelum.1`
- Image ID prefix: `f5114642c890`
- Host: Ubuntu 24.04 under Windows WSL2, native Docker
- Command Center: healthy; `/api/health` returned HTTP 200
- Existing MySQL, Redis and application containers retained
- Database backed up before replacement; upstream updater stopped

The branded backend was built and launched successfully. Individual app functionality, offline operation, backup restoration, hardware performance and security still require comprehensive testing. No independently published image or production installer is available.

## Changes

VECTELUM name, logo, application title, Command Center layout, documentation, favicon and footer; a separate browser launcher; [local Compose override](install/vectelum-compose.override.yaml) for selecting a branded image without changing existing service names or persistent data paths.

Brand assets: `admin/public/vectelum-os.svg` (icon), `admin/public/vectelum-wordmark.svg` (wordmark). Legacy internal identifiers and some image metadata remain upstream-branded for compatibility or pending cleanup.

## Runtime

- Local Command Center: http://127.0.0.1:8080/home
- Local landing preview launcher (when served separately): http://127.0.0.1:8082/os/
- [Standalone launcher source](vectelum-launcher/)

Use the deployment instructions in [README.md](README.md#installation--quickstart). Do not use legacy upstream core update scripts or enable the inherited core auto-updater on the branded deployment. The launcher links to services; it does not start containers.

Do not expose unauthenticated administrative tools to the public internet. The management container has Docker socket access. Dependency vulnerabilities remain under review. Hardware concepts and planned CORE, VAULT and MESH integrations are not validated products.
