# VECTELUM OS — developer preview

Independent experimental derivative of Project NOMAD by Crosstalk Solutions and contributors, licensed Apache-2.0. Original LICENSE, copyright notices, README (UPSTREAM-README.md), and attribution are retained. No affiliation or endorsement is claimed. Upstream revision: c903da48c97bc02f5cdfeff2ebcde00a82dfec8e.

Changes: VECTELUM name, logo, application title, command center layout and footer; a separate VECTELUM launcher for the existing local service installation. The launcher does not change container configuration or data and is not a replacement backend. The modified admin source has not yet been built into a production image. Upstream update mechanisms must not be used to distribute the branded version without review.

Local launcher: http://127.0.0.1:8082/os/ (served by VECTELUM landing preview).
Existing service backend: http://127.0.0.1:8080/ (original runtime).
Do not expose these unauthenticated administrative tools to the public internet. Local developer preview only.

Brand assets: admin/public/vectelum-os.svg (icon), admin/public/vectelum-wordmark.svg (wordmark), and favicon PNGs match the landing-page identity. Legacy technical identifiers and upstream attribution remain for compatibility.
