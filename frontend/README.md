# Ocean Agentic AI — Marine Intelligence Frontend

Lightweight, modern dashboard for SIH 2026 Ocean/Marine Agentic AI (Phase 9 Unified Marine Data Service).

## How to Run
1. Ensure the FastAPI backend is running:
   ```powershell
   cd "c:\Users\Supiiii\Documents\FINAL SIH"
   .\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
2. Open `index.html` in your browser:
   - Double-click `index.html`, OR
   - Start a local HTTP server:
     ```powershell
     cd "c:\Users\Supiiii\Documents\FINAL SIH\frontend"
     python -m http.server 3000
     ```
     Then navigate to `http://localhost:3000`.

## Features
- **Location Presets**: Preconfigured coordinates for Mumbai Coast, Chennai/Bay of Bengal, Miami/Atlantic, San Francisco Bay, and Kochi.
- **Unified Section Display**: Weather conditions, Wave & Swell height/period, Sea Surface Temperature (SST), Currents, and Tides.
- **Preserved Discrepancy Viewer**: Highlights differences between conflicting provider observations.
- **Provider Health & Latency**: Real-time status diagnostics across Open-Meteo, IMD, NOAA NWS, NOAA NDBC, NOAA CO-OPS, TidesAtlas, and NASA Ocean Color.
- **Official Bulletins**: Coastal warnings, sea area bulletins, nowcasts, and NWS weather alerts.
