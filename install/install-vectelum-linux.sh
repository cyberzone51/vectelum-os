#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
printf '%s\n' 'VECTELUM Local developer preview' 'Requires local Docker Engine, Compose v2, Git, Python 3 and xdg-utils.' '1) Register existing VECTELUM' '2) Fresh installation (build and download dependencies)'
read -r -p 'Choose [1/2]: ' mode
case "$mode" in
  1) python3 vectelum-local.py setup ;;
  2) python3 vectelum-local.py setup --fresh ;;
  *) echo 'Cancelled'; exit 1 ;;
esac
