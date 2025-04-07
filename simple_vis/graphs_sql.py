import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import mpld3
from sklearn.cluster import DBSCAN
from mpl_toolkits.basemap import Basemap

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

# Extract and transform data
records = data.get('records', [])
fetched_records = []
for record in records:
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
df['edad_momento_desaparicion'] = pd.to_numeric(df['edad_momento_desaparicion'], errors='coerce')

# Prepare HTML storage
plots_html = []
sns.set_style("whitegrid")

# Weekly Gender Distribution Plot
plt.figure(figsize=(12, 6))
df_weekly_gender = df.set_index('fecha_desaparicion').resample('W')['sexo'].value_counts().unstack(fill_value=0)
df_weekly_gender.plot(kind='bar', stacked=True, color=['blue', 'pink'], ax=plt.gca())
plt.title('Weekly Gender Distribution')
plt.xlabel('Date (Week)')
plt.ylabel('Count')
plt.legend(title='Sexo')
plots_html.append(mpld3.fig_to_html(plt.gcf()))
plt.close()

# Weekly Average Age Distribution Plot
plt.figure(figsize=(12, 6))
df_weekly_age = df.set_index('fecha_desaparicion').resample('W')['edad_momento_desaparicion'].mean()
df_weekly_age.plot(ax=plt.gca(), marker='o', linestyle='-')
plt.title('Weekly Average Age Distribution')
plt.xlabel('Date (Week)')
plt.ylabel('Mean Age')
plots_html.append(mpld3.fig_to_html(plt.gcf()))
plt.close()

# Weekly 'condicion_localizacion' Distribution Plot
plt.figure(figsize=(12, 6))
df_weekly_cond = df.set_index('fecha_desaparicion').resample('W')['condicion_localizacion'].value_counts().unstack(
    fill_value=0)
df_weekly_cond.plot(kind='bar', stacked=True, ax=plt.gca())
plt.title('Weekly Condición Localización Distribution')
plt.xlabel('Date (Week)')
plt.ylabel('Count')
plt.legend(title='Condicion Localizacion')
plots_html.append(mpld3.fig_to_html(plt.gcf()))
plt.close()

# Weekly Clusters by Lat-Lng within 1km Plot
coords = df[['lat', 'lon']].dropna().values
kms_per_radian = 6371.0088
epsilon = 0.5 / kms_per_radian

# Calculate clusters
db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
cluster_labels = db.labels_
df['cluster'] = -1
df.loc[df.index.isin(df.dropna(subset=['lat', 'lon']).index), 'cluster'] = cluster_labels

plt.figure(figsize=(12, 6))
df_weekly_clusters = df.dropna(subset=['lat', 'lon']).set_index('fecha_desaparicion').resample('W')[
    'cluster'].value_counts().unstack(fill_value=0)
df_weekly_clusters.plot(kind='bar', stacked=True, ax=plt.gca())
plt.title('Weekly Lat-Lng Clusters Distribution (1km)')
plt.xlabel('Date (Week)')
plt.ylabel('Count')
#plt.legend(title='Cluster')
print(df_weekly_clusters)
plots_html.append(mpld3.fig_to_html(plt.gcf()))
plt.close()

# Create a table with cluster centroids
cluster_centroids = df.groupby('cluster')[['lat', 'lon']].mean().reset_index()
cluster_centroids_html = cluster_centroids.to_html(index=False, header=True, border=1,
                                                   columns=['cluster', 'lat', 'lon'],
                                                   table_id="cluster_centroids_table")

# Save all plots and table as HTML
with open('./output_plots.html', 'w') as f:
    for plot_html in plots_html:
        f.write(plot_html + '\n')
    f.write("<h2>Cluster Centroids</h2>")
    f.write(cluster_centroids_html)

print("All plots and the cluster centroid table have been saved to 'output_plots.html'.")
