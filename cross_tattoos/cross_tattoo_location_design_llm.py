import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import time
import os
from tqdm import tqdm  # For progress bars

def load_data():
    """Load and prepare the LLM-processed tattoo datasets and the list of probable cases."""
    print("Loading LLM-processed PFSI dataset...")
    pfsi_df = pd.read_csv('ds/csv/equi/llm_tatuajes_procesados_PFSI.csv')
    print("Loading LLM-processed REPD dataset...")
    repd_df = pd.read_csv('ds/csv/equi/llm_tatuajes_procesados_REPD.csv')
    print("Loading probable cases dataset...")
    probable_cases_df = pd.read_csv('csv/cross_examples/person_matches_name_age.csv').sample(30000)

    print("Cleaning and preparing text columns...")
    # Clean and prepare text columns
    for df in [pfsi_df, repd_df]:
        columns_to_process = ['ubicacion', 'diseño']
        for col in columns_to_process:
            if col in df.columns:  # Check if column exists
                df[col] = df[col].fillna('')
                df[col] = df[col].str.lower()
    
    return pfsi_df, repd_df, probable_cases_df

def preprocess_text(text):
    """Clean and standardize text for comparison."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_simple_matches(pfsi_df, repd_df, probable_cases_df):
    """
    Calculate simple matches based on location and design only.
    """
    start_time = time.time()
    results = []
    
    print("Preprocessing tattoo data...")
    # Create location vectors
    print("Setting up location matching...")
    location_vectorizer = TfidfVectorizer(min_df=1)
    all_locations = list(pfsi_df['ubicacion']) + list(repd_df['ubicacion'])
    location_vectorizer.fit(all_locations)
    print(f"Location vocabulary size: {len(location_vectorizer.vocabulary_)}")
    
    # Create design vectors if available
    has_design = 'diseño' in pfsi_df.columns and 'diseño' in repd_df.columns
    if has_design:
        print("Setting up design matching...")
        design_vectorizer = TfidfVectorizer(min_df=1)
        all_designs = list(pfsi_df['diseño']) + list(repd_df['diseño'])
        design_vectorizer.fit(all_designs)
        print(f"Design vocabulary size: {len(design_vectorizer.vocabulary_)}")
    
    # Very low threshold to catch even weak matches
    threshold = 0.3
    
    # Process each person pair
    print(f"Processing {len(probable_cases_df)} person pairs...")
    matches_count = 0
    pbar = tqdm(total=len(probable_cases_df), desc="Processing person pairs")
    
    # Track statistics
    processed_pairs = 0
    pairs_with_tattoos = 0
    total_comparisons = 0
    
    debug_samples = []
    
    for i, pair in enumerate(probable_cases_df.itertuples()):
        body_id = pair.body_id
        missing_id = pair.missing_id
        processed_pairs += 1
        
        # Get all tattoos for this specific person pair
        body_tattoos = pfsi_df[pfsi_df['id_persona'] == body_id]
        missing_tattoos = repd_df[repd_df['id_persona'] == missing_id]
        
        if len(body_tattoos) == 0 or len(missing_tattoos) == 0:
            # Skip if either person has no tattoos
            pbar.update(1)
            continue
            
        pairs_with_tattoos += 1
        
        # Transform to location vectors
        body_loc_vectors = location_vectorizer.transform(body_tattoos['ubicacion'])
        missing_loc_vectors = location_vectorizer.transform(missing_tattoos['ubicacion'])
        
        # Transform to design vectors if available
        if has_design:
            body_design_vectors = design_vectorizer.transform(body_tattoos['diseño'])
            missing_design_vectors = design_vectorizer.transform(missing_tattoos['diseño'])
        
        pair_matches = 0
        
        # Compare all tattoos between this person pair
        for bi, body_tattoo in enumerate(body_tattoos.itertuples()):
            body_loc_vector = body_loc_vectors[bi]
            if has_design:
                body_design_vector = body_design_vectors[bi]
            
            for mi, missing_tattoo in enumerate(missing_tattoos.itertuples()):
                missing_loc_vector = missing_loc_vectors[mi]
                if has_design:
                    missing_design_vector = missing_design_vectors[mi]
                
                total_comparisons += 1
                
                # Calculate location similarity
                location_similarity = cosine_similarity(body_loc_vector, missing_loc_vector)[0][0]
                
                # Calculate design similarity if available
                design_similarity = 0
                if has_design:
                    design_similarity = cosine_similarity(body_design_vector, missing_design_vector)[0][0]
                
                # Combined score
                if has_design:
                    combined_score = (0.7 * location_similarity) + (0.3 * design_similarity)
                else:
                    combined_score = location_similarity
                
                # For debugging - collect some samples to see what's happening
                if len(debug_samples) < 10:
                    debug_samples.append({
                        'pfsi_id': body_id,
                        'repd_id': missing_id,
                        'pfsi_location': body_tattoo.ubicacion,
                        'repd_location': missing_tattoo.ubicacion,
                        'location_similarity': location_similarity,
                        'combined_score': combined_score
                    })
                
                if combined_score > threshold:
                    pair_matches += 1
                    matches_count += 1
                    
                    result_dict = {
                        'pfsi_id': body_id,
                        'repd_id': missing_id,
                        'pfsi_location': body_tattoo.ubicacion,
                        'repd_location': missing_tattoo.ubicacion,
                        'location_similarity': round(location_similarity, 3),
                        'similarity': round(combined_score, 3),
                        'missing_name': pair.missing_name,
                        'missing_age': pair.missing_age,
                        'body_name': pair.body_name,
                        'body_age': pair.body_age
                    }
                    
                    # Add design info if available
                    if has_design:
                        result_dict['pfsi_design'] = body_tattoo.diseño
                        result_dict['repd_design'] = missing_tattoo.diseño
                        result_dict['design_similarity'] = round(design_similarity, 3)
                    
                    results.append(result_dict)
        
        pbar.update(1)
        if (i+1) % 100 == 0:
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + 1)) * (len(probable_cases_df) - i - 1)
            print(f"\nProcessed {i+1}/{len(probable_cases_df)} person pairs. Found {matches_count} matches so far.")
            print(f"Elapsed: {elapsed:.1f}s, Estimated remaining: {remaining:.1f}s")
    
    pbar.close()
    
    # Display debug samples
    print("\nDebug samples (random comparisons):")
    for i, sample in enumerate(debug_samples):
        print(f"Sample {i+1}:")
        print(f"  Body location: '{sample['pfsi_location']}'")
        print(f"  Missing location: '{sample['repd_location']}'")
        print(f"  Location similarity: {sample['location_similarity']}")
        print(f"  Combined score: {sample['combined_score']}")
    
    processing_time = time.time() - start_time
    print(f"\nMatching completed in {processing_time:.1f} seconds")
    print(f"Found {matches_count} matches above threshold ({threshold})")
    print(f"Total pairs processed: {processed_pairs}")
    print(f"Pairs with tattoos: {pairs_with_tattoos}")
    print(f"Total tattoo comparisons: {total_comparisons}")
    
    if results:
        result_df = pd.DataFrame(results).sort_values('similarity', ascending=False)
    else:
        result_df = pd.DataFrame(results)
    
    return result_df

def analyze_matches(matches_df):
    """Analyze and output the tattoo matches."""
    print(f"Found {len(matches_df)} potential matches above threshold.")
    
    if len(matches_df) == 0:
        print("No matches found.")
        return pd.DataFrame()
    
    if 'pfsi_id' in matches_df.columns and 'repd_id' in matches_df.columns:
        # Group by person pairs to find individuals with matching tattoos
        print("Grouping matches by person pairs...")
        person_pairs = matches_df.groupby(['pfsi_id', 'repd_id']).agg({
            'similarity': ['count', 'mean', 'max']
        })
        
        person_pairs.columns = ['match_count', 'avg_similarity', 'max_similarity']
        person_pairs = person_pairs.sort_values(['match_count', 'avg_similarity'], ascending=False)
        
        print(f"\nFound {len(person_pairs)} unique person pairs with matching tattoos")
        
        print("\nTop person matches:")
        print(person_pairs.head(10))
        
        print("\nTop individual tattoo matches:")
        print(matches_df.head(10))
        
        return person_pairs
    else:
        print("No matches found with 'pfsi_id' and 'repd_id' columns.")
        return pd.DataFrame()

def main():
    start_time = time.time()
    print("Starting simplified tattoo matching process using location and design only...")
    
    pfsi_df, repd_df, probable_cases_df = load_data()
    print(f"Loaded {len(pfsi_df)} PFSI tattoos, {len(repd_df)} REPD tattoos, and {len(probable_cases_df)} probable cases")
    
    # Print schema to verify columns
    print("\nPFSI columns:", pfsi_df.columns.tolist())
    print("REPD columns:", repd_df.columns.tolist())
    
    # Print data samples
    print("\nSample PFSI data:")
    print(pfsi_df[['id_persona', 'ubicacion', 'diseño' if 'diseño' in pfsi_df.columns else 'descripcion_tattoo']].head(3))
    print("\nSample REPD data:")
    print(repd_df[['id_persona', 'ubicacion', 'diseño' if 'diseño' in repd_df.columns else 'descripcion_tattoo']].head(3))
    
    # Find matches based on location and design
    matches_df = calculate_simple_matches(pfsi_df, repd_df, probable_cases_df)
    person_matches = analyze_matches(matches_df)
    
    # Create output directory if it doesn't exist
    os.makedirs('./ds/csv/cross_examples/', exist_ok=True)
    
    # Save results
    print("Saving results to CSV files...")
    matches_df.to_csv('./ds/csv/cross_examples/tattoo_matches_location_design_llm.csv', index=False)
    if not person_matches.empty:
        person_matches.to_csv('./ds/csv/cross_examples/person_matches_location_design_llm.csv')
    
    total_time = time.time() - start_time
    print(f"\nTotal processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print("Results saved to CSV files")

if __name__ == "__main__":
    main()
