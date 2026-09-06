"""
Generate high-resolution visual assets for EcoAir-Forecast Review I PPT:
1. architecture_flowchart.png: End-to-end system pipeline flowchart.
2. gantt_chart.png: Official MCA Review timeline according to Presidency University schedule.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import os

os.makedirs('static/ppt_assets', exist_ok=True)

# -------------------------------------------------------------
# 1. Architecture & Pipeline Flowchart
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
ax.set_facecolor('#0B132B')
fig.patch.set_facecolor('#0B132B')

# Title
ax.text(7, 7.6, "EcoAir-Forecast: End-to-End System Architecture & Pipeline Flow", 
        ha='center', va='center', color='#38BDF8', fontsize=16, fontweight='bold')

# Function to draw styled box
def draw_box(x, y, w, h, title, subtitle, color, edgecolor='#38BDF8'):
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", 
                                  facecolor=color, edgecolor=edgecolor, linewidth=2, zorder=2)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2 + 0.18, title, ha='center', va='center', color='#FFFFFF', 
            fontsize=10.5, fontweight='bold', zorder=3)
    ax.text(x + w/2, y + h/2 - 0.22, subtitle, ha='center', va='center', color='#94A3B8', 
            fontsize=8.5, style='italic', zorder=3)

# Function to draw arrow
def draw_arrow(x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color='#38BDF8', lw=2, shrinkA=5, shrinkB=5))
    if label:
        ax.text((x1 + x2)/2, (y1 + y2)/2 + 0.15, label, ha='center', va='center',
                color='#F1F5F9', fontsize=8, fontweight='semibold', zorder=4)

# Top Layer: User / Search Layer
draw_box(0.6, 5.8, 3.2, 1.2, "User Web Dashboard", "City Search & Model Selection\n(Bengaluru, Delhi, London...)", "#1C2541")
draw_box(4.8, 5.8, 3.2, 1.2, "Nominatim Geocoder", "OpenStreetMap Geocoding\nQuery -> Lat & Lon Coords", "#1C2541")
draw_box(9.0, 5.8, 3.8, 1.2, "Open-Meteo Live APIs", "Parallel Weather & Air Quality\nPM2.5, PM10, CO, Temp, Wind", "#1C2541")

draw_arrow(3.8, 6.4, 4.8, 6.4, "City Query")
draw_arrow(8.0, 6.4, 9.0, 6.4, "Lat / Lon")

# Middle Layer: ML Inference Suite & SQLite Database
draw_box(0.6, 3.2, 3.2, 1.4, "SQLite Database", "data/ecoair.db\nLogs search history & analytics\nQuery recall & persistence", "#1E293B", "#10B981")
draw_box(4.8, 3.2, 3.8, 1.4, "3-Model Machine Learning Engine", "Scikit-Learn Regression Suite:\n• Random Forest (Ensemble)\n• Linear Regression (Interpretable)\n• Decision Tree (Rule-Based)", "#111E38", "#38BDF8")
draw_box(9.5, 3.2, 3.5, 1.4, "Calibration & Forecast Engine", "Blends ML Weather Sensitivity\nwith 7-Day Atmospheric Trends\nCalculates EPA AQI & Health Advisory", "#1E293B", "#F59E0B")

draw_arrow(9.5, 5.8, 8.6, 4.6, "Live Weather Feat.")
draw_arrow(4.8, 6.4, 2.2, 4.6, "Log Location")
draw_arrow(6.7, 4.6, 6.7, 5.8, "") # Feedback
draw_arrow(8.6, 3.9, 9.5, 3.9, "Predicted Baseline")

# Bottom Layer: Outputs & UI Rendering
draw_box(1.5, 0.8, 3.2, 1.3, "GIS Risk Map & Leaflet", "Live visual marker & popup\nColor-coded risk radius\nCoordinates auto-zoom", "#1C2541")
draw_box(5.3, 0.8, 3.2, 1.3, "Chart.js Trend Visualizer", "7-Day Predicted AQI curve\nHealth risk threshold zones\nInteractive tooltips", "#1C2541")
draw_box(9.1, 0.8, 3.8, 1.3, "Comparative Analytics Suite", "Side-by-side Model Metrics\n(R2 Score, RMSE, Formula)\nEPA Health Advisory Cards", "#1C2541")

draw_arrow(11.2, 3.2, 11.0, 2.1, "7-Day Forecast")
draw_arrow(11.2, 3.2, 6.9, 2.1, "Daily AQI Curve")
draw_arrow(11.2, 3.2, 3.1, 2.1, "Location Marker")

ax.set_xlim(0, 13.5)
ax.set_ylim(0, 8.2)
ax.axis('off')
plt.tight_layout()
flowchart_path = 'static/ppt_assets/architecture_flowchart.png'
plt.savefig(flowchart_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {flowchart_path}")

# -------------------------------------------------------------
# 2. Project Timeline (Gantt Chart)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
ax.set_facecolor('#FFFFFF')
fig.patch.set_facecolor('#FFFFFF')

tasks = [
    "Phase 1: Title Confirmation & Abstract Approval",
    "Phase 2: Literature Review & Review I Preparation",
    "Phase 3: System Architecture & Data Pipeline Setup",
    "Phase 4: ML Models Training & Evaluation (Review II)",
    "Phase 5: SQLite Database & Backend API Integration",
    "Phase 6: Frontend GIS Dashboard & Review III",
    "Phase 7: Final Documentation & Viva Voce Review"
]

start_days = [0, 9, 23, 45, 66, 86, 101]
durations  = [9, 14, 22, 21, 20, 15, 15]
colors     = ['#F59E0B', '#EF4444', '#8B5CF6', '#3B82F6', '#10B981', '#06B6D4', '#6366F1']

y_pos = range(len(tasks)-1, -1, -1)

for i in range(len(tasks)):
    ax.barh(y_pos[i], durations[i], left=start_days[i], height=0.55, 
            color=colors[i], edgecolor='#334155', linewidth=1, alpha=0.9, zorder=3)
    # Text on bar
    ax.text(start_days[i] + durations[i]/2, y_pos[i], f"{durations[i]} Days", 
            ha='center', va='center', color='#FFFFFF', fontweight='bold', fontsize=8, zorder=4)

ax.set_yticks(y_pos)
ax.set_yticklabels(tasks, fontsize=9, fontweight='semibold', color='#0F172A')

# X-ticks with official review milestones
milestones = [0, 9, 23, 45, 66, 86, 101, 116]
milestone_labels = ['17-Aug', '26-Aug\n(Review I)', '10-Sep', '21-Oct\n(Review II)', '11-Nov', '25-Nov\n(Review III)', '01-Dec\n(Doc Submit)', '10-Dec\n(Final Viva)']

ax.set_xticks(milestones)
ax.set_xticklabels(milestone_labels, fontsize=8, color='#334155', fontweight='bold')

ax.grid(axis='x', linestyle='--', alpha=0.6, zorder=1)
ax.set_title("MCA Project Review Timeline (Presidency University Schedule)", 
             fontsize=12, fontweight='bold', color='#1E293B', pad=12)
ax.set_xlabel("Project Schedule (Aug 2026 – Dec 2026)", fontsize=9, fontweight='bold', color='#475569')

plt.tight_layout()
gantt_path = 'static/ppt_assets/gantt_chart.png'
plt.savefig(gantt_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {gantt_path}")
