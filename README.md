# SIH
🗺️ GIS + Navigation Process

The GIS + Navigation module helps users find suitable fishing zones and the safest route to reach them.

How it works

1. Get User Location 📍
   Get the user's current GPS location.

2. Find Nearby PFZs 🐟
   Use GIS to find nearby Potential Fishing Zones and calculate their distance and suitability.

3. Check Marine Conditions 🌊
   Check weather, waves, wind, and other marine hazards around the area.

4. Check Restricted Areas 🚫
   Identify protected, restricted, or no-entry zones using geofencing.

5. Create Risk Map 🗺️
   Divide the sea into areas and assign each area a risk score based on marine conditions and hazards.

6. Find Safest Route 🧭
   Use the risk map and A* pathfinding to find a route that avoids dangerous and restricted areas.

7. Show on Map 📍
   Send the route as GeoJSON and display the PFZ, hazards, restricted zones, and route on the interactive map.

8. AI Explanation 🤖
   The AI explains why the PFZ and route were recommended.

Simple Flow

User Location → Nearby PFZ → Marine Conditions → Hazards & Restricted Zones → Risk Map → Safest Route → Map → AI Explanation

«AI handles planning and reasoning, while GIS algorithms perform the exact spatial calculations.»
