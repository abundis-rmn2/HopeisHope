import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import time
from tqdm import tqdm  # For progress bars

def load_data():
    """Load and prepare the tattoo datasets and the list of probable cases."""
    print("Loading PFSI dataset...")
    pfsi_df = pd.read_csv('csv/equi/tatuajes_procesados_PFSI.csv')
    print("Loading REPD dataset...")
    repd_df = pd.read_csv('csv/equi/tatuajes_procesados_REPD.csv')
    print("Loading probable cases dataset...")
    probable_cases_df = pd.read_csv('csv/cross_examples/person_matches_name_age.csv')
    
    print("Cleaning and preparing text columns...")
    # Clean and prepare text columns
    for df in [pfsi_df, repd_df]:
        for col in ['descripcion_tattoo', 'ubicacion', 'texto_extraido', 'categorias', 'palabras_clave']:
            df[col] = df[col].fillna('')
            if col in ['descripcion_tattoo', 'ubicacion']:
                df[col] = df[col].str.lower()
    
    return pfsi_df, repd_df, probable_cases_df

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

def calculate_similarity_scores_strict(pfsi_df, repd_df, probable_cases_df):
    """
    Calculate similarity scores between tattoos only for specific person pairs 
    defined in the probable_cases_df.
    """
    start_time = time.time()
    results = []
    
    print("Preprocessing tattoo data...")
    # Create a combined feature text for each tattoo
    for df in [pfsi_df, repd_df]:
        df['combined_features'] = (
            df['descripcion_tattoo'] + ' ' + 
            df['ubicacion'] + ' ' + 
            df['texto_extraido'] + ' ' + 
            df['categorias'] + ' ' + 
            df['palabras_clave']
        )
        # Apply preprocessing
        df['combined_features'] = df['combined_features'].apply(preprocess_text)
    
    # Create TF-IDF vectors
    print("Creating TF-IDF vectors for combined features...")
    vectorizer = TfidfVectorizer(min_df=1)
    all_features = list(pfsi_df['combined_features']) + list(repd_df['combined_features'])
    vectorizer.fit(all_features)
    print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    
    # Create location TF-IDF vectors
    print("Creating TF-IDF vectors for location features...")
    location_vectorizer = TfidfVectorizer(min_df=1)
    all_locations = list(pfsi_df['ubicacion']) + list(repd_df['ubicacion'])
    location_vectorizer.fit(all_locations)
    print(f"Location vocabulary size: {len(location_vectorizer.vocabulary_)}")
    
    # Process each person pair from probable_cases_df
    print(f"Processing {len(probable_cases_df)} person pairs...")
    matches_count = 0
    pbar = tqdm(total=len(probable_cases_df), desc="Processing person pairs")
    
    for i, pair in enumerate(probable_cases_df.itertuples()):
        body_id = pair.body_id
        missing_id = pair.missing_id
        
        # Get all tattoos for this specific person pair
        body_tattoos = pfsi_df[pfsi_df['id_persona'] == body_id]
        missing_tattoos = repd_df[repd_df['id_persona'] == missing_id]
        
        if len(body_tattoos) == 0 or len(missing_tattoos) == 0:
            # Skip if either person has no tattoos
            pbar.update(1)
            continue
            
        # Transform to vectors
        body_vectors = vectorizer.transform(body_tattoos['combined_features'])
        missing_vectors = vectorizer.transform(missing_tattoos['combined_features'])
        
        body_loc_vectors = location_vectorizer.transform(body_tattoos['ubicacion'])
        missing_loc_vectors = location_vectorizer.transform(missing_tattoos['ubicacion'])
        
        pair_matches = 0
        
        # Compare all tattoos between this person pair
        for bi, body_tattoo in enumerate(body_tattoos.itertuples()):
            body_vector = body_vectors[bi]
            body_loc_vector = body_loc_vectors[bi]
            
            for mi, missing_tattoo in enumerate(missing_tattoos.itertuples()):
                missing_vector = missing_vectors[mi]
                missing_loc_vector = missing_loc_vectors[mi]
                
                # Calculate similarities
                text_similarity = cosine_similarity(body_vector, missing_vector)[0][0]
                location_similarity = cosine_similarity(body_loc_vector, missing_loc_vector)[0][0]
                
                # Calculate text match similarity
                text_match = 0
                if body_tattoo.texto_extraido and missing_tattoo.texto_extraido:
                    if body_tattoo.texto_extraido.lower() == missing_tattoo.texto_extraido.lower():
                        text_match = 1
                
                # Combined similarity score (weighted)
                combined_score = (0.5 * text_similarity) + (0.3 * location_similarity) + (0.2 * text_match)
                
                if combined_score > 0.6:  # Threshold for potential matches
                    pair_matches += 1
                    matches_count += 1
                    
                    results.append({
                        'pfsi_id': body_id,
                        'repd_id': missing_id,
                        'pfsi_description': body_tattoo.descripcion_tattoo,
                        'repd_description': missing_tattoo.descripcion_tattoo,
                        'pfsi_location': body_tattoo.ubicacion,
                        'repd_location': missing_tattoo.ubicacion,
                        'text_similarity': round(text_similarity, 3),
                        'location_similarity': round(location_similarity, 3),
                        'text_match': text_match,
                        'similarity': round(combined_score, 3),
                        'missing_name': pair.missing_name,
                        'missing_age': pair.missing_age,
                        'missing_location': pair.missing_location,
                        'body_name': pair.body_name,
                        'body_age': pair.body_age,
                        'body_location': pair.body_location
                    })
        
        # Display sample output for first few records
        if i < 3 and pair_matches > 0:
            print(f"\nSample match for person pair (Body: {body_id}, Missing: {missing_id}):")
            sample = results[-1]
            print(f"  Body tattoo: '{sample['pfsi_description']}' at {sample['pfsi_location']}")
            print(f"  Missing tattoo: '{sample['repd_description']}' at {sample['repd_location']}")
            print(f"  Scores: text={sample['text_similarity']}, location={sample['location_similarity']}, "
                  f"exact_match={sample['text_match']}, combined={sample['similarity']}")
            print(f"  Missing person: {sample['missing_name']} ({sample['missing_age']}), {sample['missing_location']}")
            print(f"  Body: {sample['body_name']} ({sample['body_age']}), {sample['body_location']}")
        
        pbar.update(1)
        if (i+1) % 100 == 0:
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + 1)) * (len(probable_cases_df) - i - 1)
            print(f"\nProcessed {i+1}/{len(probable_cases_df)} person pairs. Found {matches_count} matches so far.")
            print(f"Elapsed: {elapsed:.1f}s, Estimated remaining: {remaining:.1f}s")
    
    pbar.close()
    
    processing_time = time.time() - start_time
    print(f"\nSimilarity calculation completed in {processing_time:.1f} seconds")
    print(f"Found {matches_count} matches above threshold (0.6)")
    
    if results:
        result_df = pd.DataFrame(results).sort_values('similarity', ascending=False)
    else:
        result_df = pd.DataFrame(results)
    
    return result_df

def analyze_potential_matches(matches_df):
    """Analyze and output potential tattoo matches."""
    print(f"Found {len(matches_df)} potential matches above threshold.")
    
    if len(matches_df) == 0:
        print("No matches found.")
        return pd.DataFrame()
    
    if 'pfsi_id' in matches_df.columns and 'repd_id' in matches_df.columns:
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
    else:
        print("No matches found with 'pfsi_id' and 'repd_id' columns.")
        return pd.DataFrame()

def main():
    start_time = time.time()
    print("Starting STRICT tattoo matching process (only comparing linked person pairs)...")
    
    pfsi_df, repd_df, probable_cases_df = load_data()
    print(f"Loaded {len(pfsi_df)} PFSI tattoos, {len(repd_df)} REPD tattoos, and {len(probable_cases_df)} probable case pairs")
    
    # Print sample data
    print("\nSample PFSI data:")
    print(pfsi_df[['id_persona', 'descripcion_tattoo', 'ubicacion']].head(3))
    print("\nSample REPD data:")
    print(repd_df[['id_persona', 'descripcion_tattoo', 'ubicacion']].head(3))
    print("\nSample probable case pairs:")
    print(probable_cases_df[['missing_id', 'body_id', 'missing_name', 'body_name']].head(3))
    
    # Calculate similarity scores only for the specific person pairs
    matches_df = calculate_similarity_scores_strict(pfsi_df, repd_df, probable_cases_df)
    person_matches = analyze_potential_matches(matches_df)
    
    # Save results
    print("Saving results to CSV files...")
    matches_df.to_csv('./csv/cross_examples/tattoo_matches_strict.csv', index=False)
    if not person_matches.empty:
        person_matches.to_csv('./csv/cross_examples/person_matches_strict.csv')
    
    total_time = time.time() - start_time
    print(f"\nTotal processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print("Results saved to 'tattoo_matches_strict.csv' and 'person_matches_strict.csv'")

if __name__ == "__main__":
    main()