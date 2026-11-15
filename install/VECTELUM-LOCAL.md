# VECTELUM Local — desktop launcher and installation (developer preview)

The public **Launch VECTELUM OS** button uses the local URI `vectelum://launch`. It does not connect to a cloud demo. After one-time setup, it starts the installed core containers and opens the local Command Center. The browser may show its normal confirmation dialog before opening a desktop application.

## Before installing

- Windows: Windows 10/11 with WSL2 and Ubuntu 24.04, Python 3.10+ on Windows, Git and Python 3 inside Ubuntu, native Docker Engine with Compose v2 in Ubuntu. Follow the [WSL2 guide](https://www.projectnomad.us/install/wsl2) and [Docker Engine instructions](https://docs.docker.com/engine/install/ubuntu/). Do not install another daemon if you already have one. Ensure the WSL Docker service starts normally; the launcher does not change system services.
- Linux: x86-64 Ubuntu 24.04 (target), Python 3.10+, Git, Docker Engine + Compose v2, xdg-utils and a graphical desktop. The user must already have access to the local Docker socket. Docker access is equivalent to powerful host privileges.
- Internet is required for the first build and downloads. Allow at least 30 GiB for building, preferably 50 GB or more, plus storage for models and content. In WSL check free space on the physical Windows drive too.
- The program is an experimental developer preview. Keep it on a trusted local computer/network. The inherited admin has no built-in authentication and accesses Docker. Do not expose ports publicly. Optional applications can have their own ports and credentials.
- Setup does NOT silently install Docker, enable WSL, change firewall rules, request administrator rights, or delete existing data. Install prerequisites using their official documentation first.

## One-time setup

Download the installer ZIP from the VECTELUM website or clone this repository.

**Windows:** Extract the ZIP, double-click `INSTALL-VECTELUM-WINDOWS.cmd`, choose mode 1 for an existing compatible VECTELUM deployment, or 2 for a new computer. The default WSL distribution is Ubuntu-24.04. For a different existing distro, run:

```powershell
python .\vectelum-local.py setup --distro Ubuntu-24.04
```

Add `--fresh` only on a new host.

**Linux:** in the extracted folder, run:

```bash
bash install-vectelum-linux.sh
```

Or run `python3 vectelum-local.py setup` (existing) or `python3 vectelum-local.py setup --fresh` (new).

The fresh path builds the tested source revision 56350b3, creates separate local storage under ~/.local/share/vectelum/backend, generates unique credentials, and starts MySQL, Redis and the VECTELUM admin container. Only the core is installed initially. An existing NOMAD deployment or previous setup directory is never overwritten. If a fresh setup fails partway, review the logs and existing files before attempting recovery. Do not delete storage.

## After setup

- Click **Launch VECTELUM OS** on https://vectelum.netlify.app/ and approve the browser's external-app prompt if shown.
- Windows: open **VECTELUM Local** from the Start menu without internet.
- Linux: open **VECTELUM Local** from your desktop application menu, or run `xdg-open vectelum://launch`.
- The launcher only accepts the exact URI, validates the existing container image, starts the core services, waits for healthy status, then opens http://127.0.0.1:8080/home. It will not pull images during normal launch.
- Once the Command Center opens, follow [GETTING-STARTED.md](../GETTING-STARTED.md) to install optional apps, download AI models, maps and knowledge before disconnecting.

## Verification and limitations

The existing Windows/WSL2 deployment has been tested with the launcher. A clean installation on a separate machine and the Linux desktop association have not yet been end-to-end validated. The setup scripts are not a signed MSI, an OS installer, or a production-ready distribution. No AI models/content are bundled. No independent updater is provided. Normal launch is local; it does not require the website, a hosted backend, or a continuously running Windows landing server.

VECTELUM OS is an independent derivative of Project NOMAD, under Apache 2.0. See [LICENSE](../LICENSE). Third-party services and models have their own licenses.
