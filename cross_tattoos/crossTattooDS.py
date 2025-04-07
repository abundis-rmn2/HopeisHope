import pandas as pd
import unidecode

def normalize_text(text):
    """Normalize text by lowercasing, removing accents, and trimming"""
    if pd.isna(text):
        return ''
    return unidecode.unidecode(text.strip().lower())

def preprocess_list_field(field):
    """Convert comma-separated values into a list of normalized strings"""
    if pd.isna(field):
        return []
    return [normalize_text(item) for item in field.split(',')]

# Read both CSV files
df1 = pd.read_csv('./csv/equi/tatuajes_procesados_PFSI.csv').sample(700)
df2 = pd.read_csv('./csv/equi/tatuajes_procesados_REPD.csv').sample(1500)

# Preprocess data
for df in [df1, df2]:
    df['ubicacion_processed'] = df['ubicacion'].apply(
        lambda x: preprocess_list_field(x) if pd.notna(x) else [])
    df['categorias_processed'] = df['categorias'].apply(preprocess_list_field)
    df['palabras_clave_processed'] = df['palabras_clave'].apply(preprocess_list_field)
    df['texto_extraido_processed'] = df['texto_extraido'].apply(normalize_text)

matches = []
threshold = 5  # Minimum similarity score to consider a match

# Compare each tattoo from PFSI with each tattoo from REPD
for idx1, row1 in df1.iterrows():
    for idx2, row2 in df2.iterrows():
        # Calculate matches in different categories
        common_ubicacion = set(row1['ubicacion_processed']).intersection(row2['ubicacion_processed'])
        common_cats = set(row1['categorias_processed']).intersection(row2['categorias_processed'])
        common_keywords = set(row1['palabras_clave_processed']).intersection(row2['palabras_clave_processed'])
        
        # Check text match (either contains or is contained)
        text_match = False
        text1 = row1['texto_extraido_processed']
        text2 = row2['texto_extraido_processed']
        if text1 and text2:
            text_match = text1 in text2 or text2 in text1
        
        # Calculate similarity score
        score = len(common_ubicacion) + len(common_cats) + len(common_keywords) + (2 if text_match else 0)
        
        if score >= threshold:
            matches.append({
                'PFSI_ID': row1['id_persona'],
                'REPD_ID': row2['id_persona'],
                'PFSI_Description': row1['descripcion_tattoo'],
                'REPD_Description': row2['descripcion_tattoo'],
                'Common_Locations': ', '.join(common_ubicacion),
                'Common_Categories': ', '.join(common_cats),
                'Common_Keywords': ', '.join(common_keywords),
                'Text_Match': 'Yes' if text_match else 'No',
                'Similarity_Score': score
            })

# Convert matches to DataFrame and save
if matches:
    matches_df = pd.DataFrame(matches)
    # Sort by highest score first
    matches_df = matches_df.sort_values(by='Similarity_Score', ascending=False)
    matches_df.to_csv('./csv/cross_examples/tattoo_matches_ds.csv', index=False)
    print(f"Found {len(matches)} matches. Saved to tattoo_matches_ds.csv")
else:
    print("No matches found meeting the threshold")