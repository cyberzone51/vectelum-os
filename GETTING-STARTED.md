# Getting started with VECTELUM OS

**First-time setup guide · Developer preview · 14 November 2026**

VECTELUM OS is a browser-based, local-first management platform derived from Project NOMAD. It is not a cloud service or a standalone Linux distribution. This guide takes you from installing the software to your first offline AI chat and document-aware search.

> [!IMPORTANT]
> Cloning this repository does not download AI models, Wikipedia archives, regional maps, educational courses or your personal documents. Install the services and download the content you need while online. Your local data is not included in GitHub.

> [!WARNING]
> The management interface has no built-in authentication and can access the host Docker socket. Keep the preview on a trusted machine, bind management ports to loopback and do not expose it to the internet. This is not a production-ready distribution.

## 1. Prepare your computer

- Use an x86-64 Debian-based Linux host. The branded image has been tested on Ubuntu 24.04 LTS with native Docker inside Windows WSL2. Other upstream-supported environments are not independently validated here.
- Install Git, Docker Engine and the Docker Compose v2 plugin. Follow the [Docker Engine installation guide](https://docs.docker.com/engine/install/) for your distribution.
- For Windows, use WSL2 with Ubuntu and follow the [upstream WSL2 guide](https://www.projectnomad.us/install/wsl2). Do not install a second Docker daemon if you already have a compatible one.
- Plan for at least 4 GB RAM and 10 GB free storage for basic upstream runtime use, plus additional build space. Local AI, content, temporary layers and indexes may require much more. 32 GB RAM and a 250 GB SSD are useful upstream AI sizing targets; GPU support and model fit must be checked.
- Keep an internet connection during setup. Run commands in the Linux terminal, not in Windows CMD.

Verify the prerequisites:

```bash
git --version
docker version
docker compose version
df -h
```

## 2. Install the Adaptive AI preview

For new installations, use [VECTELUM Local Setup v0.3.0](install/VECTELUM-LOCAL.md). It builds the pinned Adaptive AI source revision 83b41cd and registers the launcher. The current fresh-install path is a developer preview, not a validated production release. Existing deployments are not automatically upgraded.

The following manual instructions describe the previously tested baseline deployment; use the installer above for the new preview.

### Manual baseline build

If you already have a healthy VECTELUM deployment, skip to step 4.

```bash
git clone https://github.com/cyberzone51/vectelum-os.git
cd vectelum-os
git checkout 56350b3
docker build \
  --build-arg VERSION=1.35.1-vectelum.1 \
  --build-arg VCS_REF=56350b3 \
  -t vectelum-os:56350b3 .
git checkout main
```

This pins the tested source revision. The [VECTELUM Local desktop setup scripts](install/VECTELUM-LOCAL.md) can build the pinned revision and register a one-click launcher. No official VECTELUM registry image is published yet. Building requires downloading dependencies and may take considerable time.

## 3. Start the backend

The verified deployment path replaces the management container of an existing compatible upstream installation, keeping its databases and application storage.

**New computer:** first follow the [upstream installation guide](https://www.projectnomad.us/install) (or the [WSL2 guide](https://www.projectnomad.us/install/wsl2)) to create the upstream-compatible base installation. It installs Project NOMAD, not VECTELUM. Review the installed version for compatibility with the pinned VECTELUM build before proceeding; a fresh install of an arbitrary newer upstream version has not been validated. Alternatively, experienced Docker users can review the [advanced installation notes](README.md#advanced-installation) to configure the Compose template manually. Do not treat that fresh deployment as a tested installer.

**Existing installation:** back up MySQL, Redis, application storage and the original Compose configuration. Verify migration compatibility and backups; do not delete volumes. Restrict the base configuration's exposed ports to loopback where appropriate. Then follow the exact [switch procedure in README](README.md#switch-an-existing-compatible-local-installation), including stopping the upstream updater. Do not run the original core update script or enable core auto-updates.

From the repository root, for an already prepared compatible base installation at `/opt/project-nomad`:

```bash
export VECTELUM_REPO="$(pwd)"
docker compose --project-directory /opt/project-nomad \
  -f /opt/project-nomad/docker-compose.yml \
  -f "$VECTELUM_REPO/install/vectelum-compose.override.yaml" \
  config --images

docker compose --project-directory /opt/project-nomad \
  -f /opt/project-nomad/docker-compose.yml stop updater

docker compose --project-directory /opt/project-nomad \
  -f /opt/project-nomad/docker-compose.yml \
  -f "$VECTELUM_REPO/install/vectelum-compose.override.yaml" \
  up -d --no-deps --pull never admin

docker inspect --format '{{.Config.Image}} {{.State.Health.Status}}' nomad_admin
curl -f http://127.0.0.1:8080/api/health
```

The expected management image is `vectelum-os:56350b3`; wait until it is healthy and the API returns HTTP 200. The existing MySQL and Redis services must be running and healthy before replacing admin. If they are not, resolve that issue first.

## 4. Open the Command Center

Open [http://127.0.0.1:8080/home](http://127.0.0.1:8080/home) in a browser on the host computer. You should see **Command Center – VECTELUM OS**.

After one-time [VECTELUM Local setup](install/VECTELUM-LOCAL.md), **Launch VECTELUM OS** on the public website opens the installed desktop launcher using the vectelum://launch URI. It starts the existing local containers and opens the Command Center. New users must install the prerequisites and software first; the browser may ask for permission to open the local app. The launcher does not require a cloud backend or the local landing preview.

The [standalone launcher](vectelum-launcher/) is optional; it lists 22 shortcuts and does not install services. The actual Command Center is the recommended setup interface.

## 5. Run Easy Setup

In the Command Center, open **Easy Setup** ([local link](http://127.0.0.1:8080/easy-setup)).

1. **Capabilities:** choose Information Library, AI Assistant, Education Platform, Maps, Data Tools and Notes as needed.
2. **Maps:** select only the geographic regions you need.
3. **Content:** choose Essential, Standard or Comprehensive collections. Start with Essential or a small selection to avoid filling your disk.
4. **Review:** check selections and estimated storage; begin the downloads.
5. Monitor installation and download progress. Do not disconnect the internet or shut down the server while needed downloads are incomplete.

The wizard and catalog are inherited from Project NOMAD. Labels and available content may vary with the source revision. See the [in-app walkthrough](admin/docs/getting-started.md).

## 6. Install additional applications

Open **Supply Depot** ([local link](http://127.0.0.1:8080/supply-depot)). Select a needed app, install it, and wait for its **Open** button. Some apps are optional and have their own accounts or configuration. Change default credentials immediately.

| Goal | Install / configure |
|---|---|
| Offline reference material | Information Library (Kiwix), then download ZIM collections |
| AI and document search | AI Assistant (Ollama + Qdrant), models and document indexing |
| Education | Kolibri, then import courses/channels |
| PDF and files | Stirling PDF, File Browser |
| Books and media | Calibre-Web, Jellyfin |
| Productivity | FlatNotes, Excalidraw, Homebox, CyberChef, IT-Tools |
| Credentials | Vaultwarden, with appropriate access control and secure transport |
| Radio communication | Meshtastic Web / MeshCore Web and compatible separate radio hardware |

See [Supply Depot app documentation](admin/docs/supply-depot-apps.md) for first-time app configuration. Radio software alone cannot supply internet connectivity.

## 7. Download and test a local AI model

1. Install **AI Assistant** in Easy Setup or Supply Depot. Wait for Ollama and Qdrant to become available.
2. Open **Settings → Models** ([local link](http://127.0.0.1:8080/settings/models)).
3. Browse available models and their variants. Select a small instruction/chat model that fits your available RAM or VRAM; click **Install**. For a low-memory CPU host, start with a quantized 1–3B model if available; larger models can need much more memory.
4. Wait for it to appear under **Installed Models**. Model downloads are not instant.
5. Open **AI Chat** ([local link](http://127.0.0.1:8080/chat)), select your installed chat model and ask a simple question.
6. For a separate model host, configure the supported Ollama or OpenAI-compatible endpoint in model settings. Download models on that host. A cloud endpoint will require internet and is not a fully local workflow.

A chat model and an embedding model serve different purposes. The inherited RAG service supports local embeddings and recognizes `nomic-embed-text`. Check the Knowledge Base status and ensure the expected compatible embedding model is available; if missing on a local Ollama installation, install it through model management if offered or use the host's Ollama tools with the appropriate model tag. Do not select an embedding-only model as your chat model. Changing embedding configuration may require a full reindex.

AI output may be incorrect. Verify important answers against source documents.

## 8. Build your Knowledge Base (RAG)

The Knowledge Base is a separate searchable index of content, not a pre-trained model or a copy of the complete internet.

1. Open **AI Chat → Knowledge Base** ([local link](http://127.0.0.1:8080/chat?knowledge_base=true)).
2. Check Qdrant and the embedding service are available.
3. Upload a small, non-sensitive PDF or text document you are authorized to use. For example, a short manual containing a known answer.
4. Choose indexing/embedding when prompted and wait until processing finishes. The Knowledge Base panel shows stored files and indexing progress.
5. In chat, enable Knowledge Base retrieval when available, select the chat model, and ask a question whose answer appears in the document.
6. Check the answer and cited source passages against the actual file. If the result is missing, confirm that retrieval is enabled, the document is indexed and the correct collection is selected.
7. Add additional documents gradually. Use collections and manual indexing to control what is searched and avoid indexing unnecessary large archives.

Downloaded Wikipedia/ZIM libraries and maps are not automatically equivalent to a completed AI index. Depending on your auto-index policy, supported ZIM content can be indexed; review estimates before starting. Indexing large libraries can use significant CPU time and extra disk space.

**Do not upload secrets or personal data without an appropriate security configuration.**

## 9. Download offline knowledge, maps and education

- **Information Library:** open [Content Explorer](http://127.0.0.1:8080/settings/zim/remote-explorer), select a small Wikipedia package in your language or another ZIM collection, download it, then open Kiwix and browse it. Check [Content Manager](http://127.0.0.1:8080/settings/zim) for downloaded archives. Larger archives may consume tens or hundreds of GB.
- **Maps:** open [Maps Manager](http://127.0.0.1:8080/settings/maps), download the region you need, then open [Maps](http://127.0.0.1:8080/maps) and check it loads. Maps do not imply live GPS or turn-by-turn navigation.
- **Education:** open Kolibri after installation, create/configure a local facility and user accounts as prompted, then import the desired channels using Kolibri's content tools. Courses must be downloaded before offline use.
- **Translation:** if needed, configure the translated library and download the supported language models before disconnecting.
- **Books/media:** import your own permitted files using the appropriate local library tools; they are not included in the GitHub clone.

## 10. Verify offline operation

Before disconnecting:

- [ ] All required applications are installed and open successfully.
- [ ] At least one chat model is installed and responds.
- [ ] Knowledge Base indexing is complete for the test document.
- [ ] Needed ZIM archives and map regions are downloaded.
- [ ] Required Kolibri channels, books and language models are imported.
- [ ] There is sufficient free storage and the important data is backed up.

Disconnect internet access while keeping the host and local networking available. Repeat the local chat, document retrieval, library search and map viewing tests. Reconnect if more content or troubleshooting is needed. This is a per-deployment verification, not a guarantee that every third-party feature operates offline.

## 11. Restart and troubleshoot

After a reboot, start the Linux/WSL environment and Docker. From the repository root, with the existing compatible configuration and tested image present:

```bash
docker compose --project-directory /opt/project-nomad \
  -f /opt/project-nomad/docker-compose.yml \
  -f "$PWD/install/vectelum-compose.override.yaml" \
  up -d --pull never mysql redis admin
```

This starts the core services using locally available images; installed application containers have their own restart policies. Ensure the upstream updater stays stopped.

| Problem | What to check |
|---|---|
| Command Center unavailable | Docker is running, port 8080 mapping, container health and logs |
| AI model missing | Settings → Models; install a chat model and wait for download |
| Slow AI | Model size, RAM/VRAM, CPU/GPU support and other running apps |
| Knowledge Base unavailable | Qdrant, embedding model, indexing progress, disk space |
| Empty library or maps | Download the relevant ZIM packages or geographic regions |
| Disk space low | Settings → System; reduce planned downloads and avoid unnecessary indexing |
| App does not open | Supply Depot → Manage → Logs; check its service and configuration |

```bash
docker ps
docker logs --tail 100 nomad_admin
curl -f http://127.0.0.1:8080/api/health
```

Do not run upstream core updates over VECTELUM. Follow the [maintenance guidance](README.md#development-and-maintenance) and keep backups. Do not use destructive reset, uninstall or volume removal as routine troubleshooting.

## Further reading

- [Main README — architecture, hardware family and installation](README.md)
- [Developer preview status](VECTELUM.md)
- [In-app getting started walkthrough](admin/docs/getting-started.md)
- [Supply Depot app guide](admin/docs/supply-depot-apps.md)
- [Upstream FAQ](FAQ.md)
- [Report an issue](https://github.com/cyberzone51/vectelum-os/issues)

VECTELUM OS is an independent derivative of Project NOMAD by Crosstalk Solutions and contributors, under [Apache 2.0](LICENSE). Third-party models, applications and content have separate licenses.
