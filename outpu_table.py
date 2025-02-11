import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
import base64
import io
import random

# URL and parameters for API request
url = 'https://datades.abundis.com.mx/api/specificDate.php'
headers = {
    'API_KEY': 'gNXGJ0hCDavnMHvqbVRhL4yZalLUceQ4ccEHQmB40bQ',
    'Content-Type': 'application/json'
}
params = {
    'start_date': '2023-01-01',
    'end_date': '2023-12-31'
}

# Retrieve data
response = requests.get(url, headers=headers, params=params)
data = response.json()

# Extract and transform filtered data
records = data.get('records', [])
fetched_records = []
for record in records:
    # Filter records based on 'condicion_localizacion'
    if record.get('condicion_localizacion') == "NO APLICA":
        lat, lon = map(float, record['lat_long'].split(',')) if record.get('lat_long') else (None, None)
        fetched_record = {
            'lat': lat,
            'lon': lon,
            'fecha_desaparicion': record.get('fecha_desaparicion'),
            'sexo': record.get('sexo'),
            'edad_momento_desaparicion': record.get('edad_momento_desaparicion'),
            'condicion_localizacion': record.get('condicion_localizacion')
        }
        fetched_records.append(fetched_record)


# Convert to DataFrame
df = pd.DataFrame(fetched_records)
df['fecha_desaparicion'] = pd.to_datetime(df['fecha_desaparicion'], errors='coerce')
df['week'] = df['fecha_desaparicion'].dt.isocalendar().week

# Calculate DBSCAN clusters for all data
coords = df[['lat', 'lon']].dropna().values
kms_per_radian = 6371.0088
epsilon = 0.7 / kms_per_radian
db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
cluster_labels = db.labels_
df['cluster'] = -1
df.loc[df.index.isin(df.dropna(subset=['lat', 'lon']).index), 'cluster'] = cluster_labels

# Calculate cluster sizes
cluster_counts = df['cluster'].value_counts()

# Get clusters with 10 or more entries
valid_clusters = cluster_counts[cluster_counts >= 10].index

# Filter the DataFrame
df_filtered = df[df['cluster'].isin(valid_clusters)]

# Plot Weekly Clusters by Lat-Lng within 500m Plot
plt.figure(figsize=(12, 6))
df_weekly_clusters_plot = df_filtered.dropna(subset=['lat', 'lon']).set_index('fecha_desaparicion').resample('W')[
    'cluster'].value_counts().unstack(fill_value=0)
df_weekly_clusters_plot.plot(kind='bar', stacked=True, ax=plt.gca())
plt.title('Weekly Lat-Lng Clusters Distribution (500m)')
plt.xlabel('Week Number')
plt.ylabel('Count')
plt.legend(title='Cluster', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5, borderaxespad=0., frameon=False)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.xticks(ticks=range(len(df_weekly_clusters_plot.index)), labels=df_weekly_clusters_plot.index.isocalendar().week,
           rotation=45)
plt.tight_layout()

# Save the new plot to a bytes buffer
buffer = io.BytesIO()
plt.savefig(buffer, format='png')
buffer.seek(0)

# Encode the image to base64 to embed in HTML
encoded_image = base64.b64encode(buffer.read()).decode('utf-8')
buffer.close()

# Calculate cluster centroids and totals (for filtered clusters)
cluster_centroids = df_filtered.groupby('cluster').agg(
    lat=('lat', 'mean'),
    lon=('lon', 'mean'),
    total_entries=('cluster', 'size')
).reset_index()

# Generate HTML table for cluster centroids with total entries
cluster_centroids_html = cluster_centroids.to_html(index=False, header=True, border=1,
                                                   columns=['cluster', 'lat', 'lon', 'total_entries'],
                                                   table_id="cluster_centroids_table",
                                                   escape=False)

# Prepare data for pie chart
filtered_out_count = df.shape[0] - df_filtered.shape[0]
pie_data = cluster_centroids['total_entries'].tolist() + [filtered_out_count]
pie_labels = [f'Cluster {c}' for c in cluster_centroids['cluster']] + ['Filtered Out']

# Create pie chart
plt.figure(figsize=(8, 8))
plt.pie(pie_data, labels=pie_labels, autopct='%1.1f%%', startangle=140)
plt.title('Cluster Distribution Including Filtered-out Entries')

# Save the pie chart to a bytes buffer
pie_buffer = io.BytesIO()
plt.savefig(pie_buffer, format='png')
pie_buffer.seek(0)

# Encode the pie chart image to base64 to embed in HTML
encoded_pie_image = base64.b64encode(pie_buffer.read()).decode('utf-8')
pie_buffer.close()


# Assign colors to clusters
def generate_color():
    return "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])


cluster_colors = {str(cluster): generate_color() for cluster in cluster_centroids['cluster']}

# Prepare JavaScript data for map with colors
map_data = cluster_centroids.to_dict(orient='records')
map_data_js = f"var data = {map_data}; var cluster_colors = {cluster_colors};"

# Combine bar chart, pie chart, map, and table into HTML
full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Cluster Distribution and Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <style>
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid black;
            padding: 8px;
            text-align: left;
        }}
        #map {{
            height: 600px;
            width: 100%;
        }}
        .cluster-label {{
            font-size: 12px;
            font-weight: bold;
            color: white;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>Map of Cluster Centroids</h1>
    <div id="map"></div>

    <h2>Weekly Lat-Lng Clusters Distribution (500m)</h2>
    <img src='data:image/png;base64,{encoded_image}' alt='Weekly Lat-Lng Clusters Distribution (500m)' />
   
    <h2>Pie Chart of Cluster Distribution</h2>
    <img src='data:image/png;base64,{encoded_pie_image}' alt='Pie Chart of Cluster Distribution' />

    <h2>Cluster Centroids with Total Entries</h2>
    <div id="centroids_table">{cluster_centroids_html}</div>

    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script>
        // Map initialization
        var map = L.map('map').setView([20.664801, -103.347900], 10);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }}).addTo(map);

        // Data and Cluster Colors
        {map_data_js}

        // Adding circle markers with labels
        data.forEach(function(point) {{
            var clusterStr = point.cluster.toString();
            var circle = L.circle([point.lat, point.lon], {{
                color: cluster_colors[clusterStr],
                fillColor: cluster_colors[clusterStr],
                fillOpacity: 0.5,
                radius: point.total_entries * 100
            }}).addTo(map);

            var marker = L.marker([point.lat, point.lon], {{
                icon: L.divIcon({{
                    className: 'cluster-label',
                    html: '<span>' + clusterStr + '</span>'
                }})
            }}).addTo(map);

            circle.bindPopup('Cluster: ' + point.cluster + '<br>Total Entries: ' + point.total_entries);
        }});
    </script>
</body>
</html>
"""

# Save full HTML output
with open('./weekly_cluster_distribution.html', 'w') as f:
    f.write(full_html)

print(
    "Weekly cluster distribution with graph, centroids, pie chart, and map has been saved to 'weekly_cluster_distribution.html'.")
