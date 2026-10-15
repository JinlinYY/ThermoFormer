# Agent-assisted separation design

The article describes ThermoEqui-Agent as a ThermoFormer-based workflow that converts natural-language separation requests into preliminary column specifications. It uses predicted relative volatility, deterministic Fenske--Underwood--Gilliland calculations, and DWSIM-compatible `.dwxmz` export for the IPA--water and EA/NPA+DMSO case studies.

The deterministic case calculations are available under `ThermoAgent/`. The optional orchestration and DWSIM export implementation is available under `Web/ThermoFormer-web/backend/`; its installation and recalculation requirements are documented in [`docs/guides/dwsim/`](../../../guides/dwsim/). A generated `.dwxmz` file is a reproducible starting point, not a claim that every DWSIM version will converge without GUI review.
