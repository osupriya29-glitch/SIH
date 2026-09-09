# SIH
IDEAS:

Workflow A — Marine Safety
"Is it safe to go fishing tomorrow morning?"

Workflow B — PFZ
"Where is the nearest suitable fishing zone today?"

Workflow C — Safer Alternative
"If my area is unsafe, find a safer nearby fishing zone."

Workflow D — Geofence
"Alert me if I'm approaching a restricted area."



P1 → Agent/tool architecture

P2 → SST(Sea Surface Temp) + chlorophyll + PFZ data

P3 → Weather + warning data + risk model

P4 → PostGIS + boundaries + geofencing

P5 → Chat + map UI using mock data

P6 → FastAPI + DB + integration skeleton
running GIS database


/*AI reads the unified data.
Generates marine analysis.
Save the AI analysis/results into the marine_analyses table.

Phase 11 — Alerts & Recommendations

Save generated alerts into the alerts table.
Recommendations can be stored along with analyses/alerts depending on the design.*/
