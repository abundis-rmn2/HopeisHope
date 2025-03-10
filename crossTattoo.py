import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import time
from tqdm import tqdm  # For progress bars

def load_data():
    """Load and prepare the tattoo datasets."""
    print("Loading PFSI dataset...")
    pfsi_df = pd.read_csv('csv/equi/tatuajes_procesados_PFSI.csv').sample(1100)
    print("Loading REPD dataset...")
    repd_df = pd.read_csv('csv/equi/tatuajes_procesados_REPD.csv').sample(2500)
    
    print("Cleaning and preparing text columns...")
    # Clean and prepare text columns
    for df in [pfsi_df, repd_df]:
        for col in ['descripcion_tattoo', 'ubicacion', 'texto_extraido', 'categorias', 'palabras_clave']:
            df[col] = df[col].fillna('')
            if col in ['descripcion_tattoo', 'ubicacion']:
                df[col] = df[col].str.lower()
    
    return pfsi_df, repd_df

def preprocess_text(text):
    """Clean and standardize text for comparison."""
    if not isinstance(text, str):
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_similarity_scores(pfsi_df, repd_df):
    """Calculate similarity scores between tattoos using multiple features."""
    start_time = time.time()
    results = []
    
    print("Creating combined feature text for each tattoo...")
    # Create a combined feature text for each tattoo
    pfsi_df['combined_features'] = (
        pfsi_df['descripcion_tattoo'] + ' ' + 
        pfsi_df['ubicacion'] + ' ' + 
        pfsi_df['texto_extraido'] + ' ' + 
        pfsi_df['categorias'] + ' ' + 
        pfsi_df['palabras_clave']
    )
    
    repd_df['combined_features'] = (
        repd_df['descripcion_tattoo'] + ' ' + 
        repd_df['ubicacion'] + ' ' + 
        repd_df['texto_extraido'] + ' ' + 
        repd_df['categorias'] + ' ' + 
        repd_df['palabras_clave']
    )
    
    # Apply preprocessing
    print("Preprocessing text features...")
    pfsi_df['combined_features'] = pfsi_df['combined_features'].apply(preprocess_text)
    repd_df['combined_features'] = repd_df['combined_features'].apply(preprocess_text)
    
    # Create TF-IDF vectors
    print("Creating TF-IDF vectors for combined features...")
    vectorizer = TfidfVectorizer(min_df=1)
    all_features = list(pfsi_df['combined_features']) + list(repd_df['combined_features'])
    vectorizer.fit(all_features)
    
    print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    pfsi_vectors = vectorizer.transform(pfsi_df['combined_features'])
    repd_vectors = vectorizer.transform(repd_df['combined_features'])
    
    # Location similarity weight
    print("Creating TF-IDF vectors for location features...")
    location_vectorizer = TfidfVectorizer(min_df=1)
    all_locations = list(pfsi_df['ubicacion']) + list(repd_df['ubicacion'])
    location_vectorizer.fit(all_locations)
    
    print(f"Location vocabulary size: {len(location_vectorizer.vocabulary_)}")
    pfsi_loc_vectors = location_vectorizer.transform(pfsi_df['ubicacion'])
    repd_loc_vectors = location_vectorizer.transform(repd_df['ubicacion'])
    
    # Calculate similarities for all pairs
    total_comparisons = len(pfsi_df) * len(repd_df)
    print(f"Calculating similarities between {len(pfsi_df)} PFSI and {len(repd_df)} REPD tattoos...")
    print(f"Total comparisons to compute: {total_comparisons}")
    
    matches_count = 0
    pbar = tqdm(total=len(pfsi_df), desc="Processing PFSI records")
    
    for i, pfsi_row in enumerate(pfsi_df.itertuples()):
        pfsi_vector = pfsi_vectors[i]
        pfsi_loc_vector = pfsi_loc_vectors[i]
        
        batch_matches = 0
        for j, repd_row in enumerate(repd_df.itertuples()):
            repd_vector = repd_vectors[j]
            repd_loc_vector = repd_loc_vectors[j]
            
            # Calculate overall similarity
            text_similarity = cosine_similarity(pfsi_vector, repd_vector)[0][0]
            
            # Calculate location similarity
            location_similarity = cosine_similarity(pfsi_loc_vector, repd_loc_vector)[0][0]
            
            # Calculate text match similarity
            text_match = 0
            if pfsi_row.texto_extraido and repd_row.texto_extraido:
                if pfsi_row.texto_extraido.lower() == repd_row.texto_extraido.lower():
                    text_match = 1
            
            # Combined similarity score (weighted)
            combined_score = (0.5 * text_similarity) + (0.3 * location_similarity) + (0.2 * text_match)
            
            if combined_score > 0.6:  # Threshold for potential matches
                batch_matches += 1
                matches_count += 1
                results.append({
                    'pfsi_id': pfsi_row.id_persona,
                    'repd_id': repd_row.id_persona,
                    'pfsi_description': pfsi_row.descripcion_tattoo,
                    'repd_description': repd_row.descripcion_tattoo,
                    'pfsi_location': pfsi_row.ubicacion,
                    'repd_location': repd_row.ubicacion,
                    'text_similarity': round(text_similarity, 3),
                    'location_similarity': round(location_similarity, 3),
                    'text_match': text_match,
                    'similarity': round(combined_score, 3)
                })
        
        # Display sample output for first few records
        if i < 3 and batch_matches > 0:
            print(f"\nSample match for PFSI ID {pfsi_row.id_persona}:")
            sample = results[-1]
            print(f"  PFSI: '{sample['pfsi_description']}' at {sample['pfsi_location']}")
            print(f"  REPD: '{sample['repd_description']}' at {sample['repd_location']}")
            print(f"  Scores: text={sample['text_similarity']}, location={sample['location_similarity']}, " 
                  f"exact_match={sample['text_match']}, combined={sample['similarity']}")
        
        pbar.update(1)
        if i > 0 and i % 100 == 0:
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + 1)) * (len(pfsi_df) - i - 1)
            print(f"\nProcessed {i+1}/{len(pfsi_df)} PFSI records. Found {matches_count} matches so far.")
            print(f"Elapsed: {elapsed:.1f}s, Estimated remaining: {remaining:.1f}s")
    
    pbar.close()
    
    processing_time = time.time() - start_time
    print(f"\nSimilarity calculation completed in {processing_time:.1f} seconds")
    print(f"Found {matches_count} matches above threshold (0.6)")
    
    result_df = pd.DataFrame(results).sort_values('similarity', ascending=False)
    return result_df

def analyze_potential_matches(matches_df):
    """Analyze and output potential tattoo matches."""
    print(f"Found {len(matches_df)} potential matches above threshold.")
    
    # Group by person pairs to find individuals with multiple matching tattoos
    print("Grouping matches by person pairs...")
    person_pairs = matches_df.groupby(['pfsi_id', 'repd_id']).agg({
        'similarity': ['count', 'mean', 'max']
    })
    
    person_pairs.columns = ['match_count', 'avg_similarity', 'max_similarity']
    person_pairs = person_pairs.sort_values(['match_count', 'avg_similarity'], ascending=False)
    
    print(f"\nFound {len(person_pairs)} unique person pairs with at least one matching tattoo")
    pairs_with_multiple = person_pairs[person_pairs['match_count'] > 1]
    print(f"Found {len(pairs_with_multiple)} person pairs with multiple tattoo matches")
    
    print("\nTop person matches (multiple tattoo matches):")
    print(person_pairs.head(10))
    
    print("\nTop individual tattoo matches:")
    print(matches_df.head(20))
    
    return person_pairs

def main():
    start_time = time.time()
    print("Starting tattoo matching process...")
    
    pfsi_df, repd_df = load_data()
    print(f"Loaded {len(pfsi_df)} PFSI tattoos and {len(repd_df)} REPD tattoos")
    
    # Print sample data
    print("\nSample PFSI data:")
    print(pfsi_df[['id_persona', 'descripcion_tattoo', 'ubicacion']].head(3))
    print("\nSample REPD data:")
    print(repd_df[['id_persona', 'descripcion_tattoo', 'ubicacion']].head(3))
    
    matches_df = calculate_similarity_scores(pfsi_df, repd_df)
    person_matches = analyze_potential_matches(matches_df)
    
    # Save results
    print("Saving results to CSV files...")
    matches_df.to_csv('./csv/cross_examples/tattoo_matches.csv', index=False)
    person_matches.to_csv('./csv/cross_examples/person_matches.csv')
    
    total_time = time.time() - start_time
    print(f"\nTotal processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print("Results saved to 'tattoo_matches.csv' and 'person_matches.csv'")

if __name__ == "__main__":
    main()