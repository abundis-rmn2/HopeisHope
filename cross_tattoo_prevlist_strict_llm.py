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
    print("\n" + "="*80)
    print("DEBUG: Starting load_data()")
    
    print("Loading LLM-processed PFSI dataset...")
    try:
        pfsi_df = pd.read_csv('ds/csv/equi/llm_tatuajes_procesados_PFSI.csv')
        print(f"DEBUG: PFSI dataset loaded successfully with shape: {pfsi_df.shape}")
        print(f"DEBUG: PFSI columns: {pfsi_df.columns.tolist()}")
    except Exception as e:
        print(f"ERROR loading PFSI dataset: {e}")
        return None, None, None
    
    print("Loading LLM-processed REPD dataset...")
    try:
        repd_df = pd.read_csv('ds/csv/equi/llm_tatuajes_procesados_REPD.csv')
        print(f"DEBUG: REPD dataset loaded successfully with shape: {repd_df.shape}")
        print(f"DEBUG: REPD columns: {repd_df.columns.tolist()}")
    except Exception as e:
        print(f"ERROR loading REPD dataset: {e}")
        return None, None, None
    
    print("Loading probable cases dataset...")
    try:
        probable_cases_df = pd.read_csv('csv/cross_examples/person_matches_name_age.csv').sample(60000)
        print(f"DEBUG: Probable cases dataset loaded successfully with shape: {probable_cases_df.shape}")
        print(f"DEBUG: Probable cases columns: {probable_cases_df.columns.tolist()}")
    except Exception as e:
        print(f"ERROR loading probable cases dataset: {e}")
        return None, None, None
    
    print("Cleaning and preparing text columns...")
    # Clean and prepare text columns
    for df_name, df in [("PFSI", pfsi_df), ("REPD", repd_df)]:
        # Add handling for the new 'diseño' column
        columns_to_process = ['descripcion_tattoo', 'ubicacion', 'texto_extraido', 'categorias', 'palabras_clave', 'diseño']
        available_columns = []
        for col in columns_to_process:
            if col in df.columns:  # Check if column exists
                available_columns.append(col)
                null_count_before = df[col].isna().sum()
                df[col] = df[col].fillna('')
                null_count_after = df[col].isna().sum()
                print(f"DEBUG: {df_name} - Filled {null_count_before - null_count_after} NaN values in '{col}'")
                
                if col in ['descripcion_tattoo', 'ubicacion', 'diseño']:
                    df[col] = df[col].str.lower()
                    print(f"DEBUG: {df_name} - Converted '{col}' to lowercase")
        
        print(f"DEBUG: {df_name} - Processed columns: {available_columns}")
        if set(available_columns) != set(columns_to_process):
            print(f"DEBUG: {df_name} - Missing expected columns: {set(columns_to_process) - set(available_columns)}")
    
    # Show sample rows for verification
    print("\nDEBUG: Sample PFSI data:")
    print(pfsi_df.head(2).to_string())
    print("\nDEBUG: Sample REPD data:")
    print(repd_df.head(2).to_string())
    print("\nDEBUG: Sample probable cases data:")
    print(probable_cases_df.head(2).to_string())
    
    print("DEBUG: Completed load_data()")
    return pfsi_df, repd_df, probable_cases_df

def preprocess_text(text):
    """Clean and standardize text for comparison."""
    debug_output = False  # Set to True for verbose text processing debugging
    
    if debug_output:
        print(f"DEBUG: preprocess_text() input: '{text}' ({type(text)})")
    
    if not isinstance(text, str):
        if debug_output:
            print(f"DEBUG: preprocess_text() not a string, returning empty string")
        return ""
    
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text_before = text
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    if debug_output:
        print(f"DEBUG: preprocess_text() output: '{text}'")
    
    return text

def analyze_similarity_distribution(pfsi_df, repd_df, probable_cases_df, sample_size=100):
    """
    Analyze the distribution of similarity scores to help determine appropriate thresholds
    and understand why matches might not be found.
    """
    print("\n" + "="*80)
    print("ANALYZING SIMILARITY DISTRIBUTION")
    print("This will help understand why matches are not being found")
    
    # First, pre-filter probable cases to those who actually have tattoos in both datasets
    print("Finding person pairs with tattoos in both datasets...")
    valid_pairs = []
    
    # Check a subset of probable cases to find those with tattoos
    check_limit = min(500, len(probable_cases_df))  # Check more pairs to ensure we find matches
    for i, pair in enumerate(probable_cases_df.head(check_limit).itertuples()):
        body_id = pair.body_id
        missing_id = pair.missing_id
        
        # Quick check if both persons have tattoos
        body_tattoos_count = len(pfsi_df[pfsi_df['id_persona'] == body_id])
        missing_tattoos_count = len(repd_df[repd_df['id_persona'] == missing_id])
        
        if body_tattoos_count > 0 and missing_tattoos_count > 0:
            valid_pairs.append({'body_id': body_id, 'missing_id': missing_id, 
                               'body_tattoos': body_tattoos_count, 
                               'missing_tattoos': missing_tattoos_count})
        
        if i % 100 == 0 and len(valid_pairs) > 0:
            print(f"Checked {i+1} pairs, found {len(valid_pairs)} valid pairs so far")
            
        # Stop once we have enough valid pairs
        if len(valid_pairs) >= sample_size:
            break
    
    if not valid_pairs:
        print("\nERROR: Could not find any person pairs with tattoos in both datasets.")
        print("This suggests there might be an issue with ID matching or the datasets don't have overlapping records.")
        print("Suggestions:")
        print("1. Check that the IDs in probable_cases_df match those in pfsi_df and repd_df")
        print("2. Print some sample IDs from each dataset to verify they're in the expected format")
        print("3. Check if any records in both datasets have the same ID format but no tattoos")
        
        # Sample some IDs from each dataset for debugging
        print("\nSample IDs from PFSI dataset:")
        pfsi_ids = pfsi_df['id_persona'].sample(min(5, len(pfsi_df))).tolist()
        print(pfsi_ids)
        print("\nSample IDs from REPD dataset:")
        repd_ids = repd_df['id_persona'].sample(min(5, len(repd_df))).tolist()
        print(repd_ids)
        print("\nSample IDs from probable cases:")
        if 'body_id' in probable_cases_df.columns and 'missing_id' in probable_cases_df.columns:
            body_ids = probable_cases_df['body_id'].sample(min(5, len(probable_cases_df))).tolist()
            missing_ids = probable_cases_df['missing_id'].sample(min(5, len(probable_cases_df))).tolist()
            print(f"Body IDs: {body_ids}")
            print(f"Missing IDs: {missing_ids}")
            
            # Check if these IDs exist in respective datasets
            print("\nChecking if sample body IDs exist in PFSI dataset:")
            for bid in body_ids:
                matches = len(pfsi_df[pfsi_df['id_persona'] == bid])
                print(f"  Body ID {bid}: {'Found' if matches > 0 else 'NOT FOUND'} ({matches} records)")
            
            print("\nChecking if sample missing IDs exist in REPD dataset:")
            for mid in missing_ids:
                matches = len(repd_df[repd_df['id_persona'] == mid])
                print(f"  Missing ID {mid}: {'Found' if matches > 0 else 'NOT FOUND'} ({matches} records)")
        
        # Return an empty dataframe as we can't analyze anything
        return pd.DataFrame()
    
    print(f"\nFound {len(valid_pairs)} valid person pairs with tattoos in both datasets")
    
    # Convert valid pairs to DataFrame for analysis
    valid_pairs_df = pd.DataFrame(valid_pairs)
    
    # Sample from valid pairs
    if len(valid_pairs) > sample_size:
        sample_pairs = valid_pairs_df.sample(sample_size)
    else:
        sample_pairs = valid_pairs_df
    
    print(f"Selected {len(sample_pairs)} pairs for detailed analysis")
    
    # Store raw similarity scores for analysis
    all_scores = {
        'text_similarity': [],
        'location_similarity': [],
        'text_match': [],
        'combined_score': [],
        'pfsi_desc': [],
        'repd_desc': [],
        'pfsi_loc': [],
        'repd_loc': []
    }
    
    vectorizer = TfidfVectorizer(min_df=1)
    location_vectorizer = TfidfVectorizer(min_df=1)
    
    # Create a combined corpus of all text for better vectorization
    all_desc = list(pfsi_df['descripcion_tattoo']) + list(repd_df['descripcion_tattoo'])
    all_loc = list(pfsi_df['ubicacion']) + list(repd_df['ubicacion'])
    
    print("Fitting vectorizers on all text data...")
    vectorizer.fit(all_desc)
    location_vectorizer.fit(all_loc)
    
    print(f"Analyzing similarity scores for {len(sample_pairs)} sample pairs...")
    
    # For direct text comparison
    analyzed_pairs = 0
    tattoo_compared = 0
    
    # Use iterrows for the DataFrame
    for i, (_, pair) in enumerate(sample_pairs.iterrows()):
        body_id = pair.body_id
        missing_id = pair.missing_id
        
        # Get all tattoos for this specific person pair
        body_tattoos = pfsi_df[pfsi_df['id_persona'] == body_id]
        missing_tattoos = repd_df[repd_df['id_persona'] == missing_id]
        
        if len(body_tattoos) == 0 or len(missing_tattoos) == 0:
            # This should not happen since we pre-filtered
            print(f"WARNING: Pair {i+1} unexpectedly has no tattoos despite pre-filtering.")
            continue
        
        analyzed_pairs += 1
        
        # Print pair information
        print(f"\n--- Pair {i+1}: Body ID {body_id} vs Missing ID {missing_id} ---")
        print(f"Body has {len(body_tattoos)} tattoos, Missing has {len(missing_tattoos)} tattoos")
        
        # Sample and show tattoo descriptions
        if len(body_tattoos) > 0 and len(missing_tattoos) > 0:
            print("\nBody tattoos:")
            for idx, row in body_tattoos.head(3).iterrows():
                print(f"  - '{row['descripcion_tattoo']}' at '{row['ubicacion']}'")
            print("\nMissing tattoos:")
            for idx, row in missing_tattoos.head(3).iterrows():
                print(f"  - '{row['descripcion_tattoo']}' at '{row['ubicacion']}'")
        
        # Transform descriptions to vectors
        body_desc_vectors = vectorizer.transform(body_tattoos['descripcion_tattoo'])
        missing_desc_vectors = vectorizer.transform(missing_tattoos['descripcion_tattoo'])
        
        body_loc_vectors = location_vectorizer.transform(body_tattoos['ubicacion'])
        missing_loc_vectors = location_vectorizer.transform(missing_tattoos['ubicacion'])
        
        # Calculate similarities for all combinations
        for bi, body_tattoo in enumerate(body_tattoos.itertuples()):
            body_desc_vector = body_desc_vectors[bi]
            body_loc_vector = body_loc_vectors[bi]
            
            for mi, missing_tattoo in enumerate(missing_tattoos.itertuples()):
                missing_desc_vector = missing_desc_vectors[mi]
                missing_loc_vector = missing_loc_vectors[mi]
                tattoo_compared += 1
                
                # Calculate similarities
                text_similarity = cosine_similarity(body_desc_vector, missing_desc_vector)[0][0]
                location_similarity = cosine_similarity(body_loc_vector, missing_loc_vector)[0][0]
                
                # Text match (exact match of extracted text)
                text_match = 0
                if hasattr(body_tattoo, 'texto_extraido') and hasattr(missing_tattoo, 'texto_extraido'):
                    if body_tattoo.texto_extraido and missing_tattoo.texto_extraido:
                        if body_tattoo.texto_extraido.lower() == missing_tattoo.texto_extraido.lower():
                            text_match = 1
                
                # Calculate combined score with original weights
                combined_score = (0.6 * text_similarity) + (0.25 * location_similarity) + (0.15 * text_match)
                
                # Collect all scores
                all_scores['text_similarity'].append(text_similarity)
                all_scores['location_similarity'].append(location_similarity)
                all_scores['text_match'].append(text_match)
                all_scores['combined_score'].append(combined_score)
                all_scores['pfsi_desc'].append(body_tattoo.descripcion_tattoo)
                all_scores['repd_desc'].append(missing_tattoo.descripcion_tattoo)
                all_scores['pfsi_loc'].append(body_tattoo.ubicacion)
                all_scores['repd_loc'].append(missing_tattoo.ubicacion)
                
                # Print detailed comparison for potentially similar tattoos
                if (text_similarity > 0.3 or location_similarity > 0.5):
                    print("\nPOTENTIAL MATCH FOUND:")
                    print(f"  Body: '{body_tattoo.descripcion_tattoo}' at '{body_tattoo.ubicacion}'")
                    print(f"  Missing: '{missing_tattoo.descripcion_tattoo}' at '{missing_tattoo.ubicacion}'")
                    print(f"  Scores - Text: {text_similarity:.3f}, Location: {location_similarity:.3f}, Text match: {text_match}")
                    print(f"  Combined score: {combined_score:.3f}")
                    # Check against threshold
                    if combined_score <= 0.5:
                        print("  BELOW THRESHOLD - Would NOT be matched!")
    
    # Create DataFrame for analysis
    scores_df = pd.DataFrame(all_scores)
    
    print("\n" + "="*80)
    print("SIMILARITY SCORE ANALYSIS")
    print(f"Analyzed {analyzed_pairs} person pairs with a total of {tattoo_compared} tattoo comparisons")
    
    # Check if we have data to analyze
    if tattoo_compared == 0:
        print("\nERROR: No tattoo comparisons were made. Cannot perform statistical analysis.")
        return pd.DataFrame()
    
    # Analyze score distribution
    for col in ['text_similarity', 'location_similarity', 'combined_score']:
        print(f"\n{col.UPPER()} STATISTICS:")
        print(f"  Mean: {scores_df[col].mean():.3f}")
        print(f"  Median: {scores_df[col].median():.3f}")
        print(f"  Min: {scores_df[col].min():.3f}")
        print(f"  Max: {scores_df[col].max():.3f}")
        
        # Analyze percentiles
        percentiles = [0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9]
        for p in percentiles:
            try:
                val = np.percentile(scores_df[col], p)
                print(f"  {p}th percentile: {val:.3f}")
            except Exception as e:
                print(f"  Error calculating {p}th percentile: {e}")
    
    # Show examples of high text similarity but not matched
    threshold = 0.5  # Current threshold
    high_text_sim = scores_df[(scores_df['text_similarity'] > 0.4) & (scores_df['combined_score'] <= threshold)]
    
    print("\nEXAMPLES OF HIGH TEXT SIMILARITY BUT NOT MATCHED:")
    if len(high_text_sim) > 0:
        for i, row in high_text_sim.head(10).iterrows():
            print(f"\nExample {i+1}:")
            print(f"  Body: '{row['pfsi_desc']}' at '{row['pfsi_loc']}'")
            print(f"  Missing: '{row['repd_desc']}' at '{row['repd_loc']}'")
            print(f"  Text similarity: {row['text_similarity']:.3f}")
            print(f"  Location similarity: {row['location_similarity']:.3f}")
            print(f"  Combined score: {row['combined_score']:.3f} (Threshold: {threshold})")
    else:
        print("  No examples found with high text similarity but low combined score.")
    
    # Recommend threshold based on analysis
    print("\nRECOMMENDED THRESHOLDS BASED ON ANALYSIS:")
    # Find potential thresholds at different percentiles
    for p in [50, 75, 90, 95]:
        try:
            val = np.percentile(scores_df['combined_score'], p)
            matching_pairs = len(scores_df[scores_df['combined_score'] > val])
            print(f"  {p}th percentile: {val:.3f} - would match {matching_pairs} tattoo pairs ({matching_pairs/len(scores_df)*100:.1f}%)")
        except Exception as e:
            print(f"  Error calculating {p}th percentile threshold: {e}")

    return scores_df

def manual_inspection(pfsi_df, repd_df, body_id=None, missing_id=None):
    """
    Manually inspect tattoos for a specific person pair to verify matching behavior.
    If no IDs provided, tries to find a person pair with similar tattoos.
    """
    print("\n" + "="*80)
    print("MANUAL TATTOO INSPECTION")
    
    if body_id is None or missing_id is None:
        print("No specific IDs provided. Finding a promising pair...")
        # Try to find promising pairs
        for _, row in pfsi_df.head(500).iterrows():
            body_id = row['id_persona']
            # Get all tattoos for this body
            body_tattoos = pfsi_df[pfsi_df['id_persona'] == body_id]
            if len(body_tattoos) >= 2:  # At least 2 tattoos
                # Find possible matches in REPD
                for _, row2 in repd_df.head(1000).iterrows():
                    missing_id = row2['id_persona']
                    missing_tattoos = repd_df[repd_df['id_persona'] == missing_id]
                    if len(missing_tattoos) >= 2:  # At least 2 tattoos
                        print(f"Found pair for inspection: Body ID {body_id} and Missing ID {missing_id}")
                        break
                break
    
    if body_id is None or missing_id is None:
        print("Could not find suitable pair for inspection.")
        return
    
    print(f"Inspecting tattoos for Body ID {body_id} and Missing ID {missing_id}")
    
    # Get all tattoos
    body_tattoos = pfsi_df[pfsi_df['id_persona'] == body_id]
    missing_tattoos = repd_df[repd_df['id_persona'] == missing_id]
    
    print(f"\nFound {len(body_tattoos)} tattoos for Body ID {body_id}")
    for i, row in body_tattoos.iterrows():
        print(f"  {i+1}. '{row['descripcion_tattoo']}' at '{row['ubicacion']}'")
        if 'texto_extraido' in row and row['texto_extraido']:
            print(f"     Text: '{row['texto_extraido']}'")
    
    print(f"\nFound {len(missing_tattoos)} tattoos for Missing ID {missing_id}")
    for i, row in missing_tattoos.iterrows():
        print(f"  {i+1}. '{row['descripcion_tattoo']}' at '{row['ubicacion']}'")
        if 'texto_extraido' in row and row['texto_extraido']:
            print(f"     Text: '{row['texto_extraido']}'")
    
    # Perform detailed similarity checks
    vectorizer = TfidfVectorizer(min_df=1)
    location_vectorizer = TfidfVectorizer(min_df=1)
    
    # Fit on combined corpus
    all_desc = list(body_tattoos['descripcion_tattoo']) + list(missing_tattoos['descripcion_tattoo'])
    all_loc = list(body_tattoos['ubicacion']) + list(missing_tattoos['ubicacion'])
    
    vectorizer.fit(all_desc)
    location_vectorizer.fit(all_loc)
    
    # Transform
    body_vectors = vectorizer.transform(body_tattoos['descripcion_tattoo'])
    missing_vectors = vectorizer.transform(missing_tattoos['descripcion_tattoo'])
    
    body_loc_vectors = location_vectorizer.transform(body_tattoos['ubicacion'])
    missing_loc_vectors = location_vectorizer.transform(missing_tattoos['ubicacion'])
    
    print("\nSimilarity Analysis:")
    
    # Compare all combinations
    for bi, body_tattoo in enumerate(body_tattoos.itertuples()):
        body_vector = body_vectors[bi]
        body_loc_vector = body_loc_vectors[bi]
        
        for mi, missing_tattoo in enumerate(missing_tattoos.itertuples()):
            missing_vector = missing_vectors[mi]
            missing_loc_vector = missing_loc_vectors[mi]
            
            # Calculate similarities
            text_similarity = cosine_similarity(body_vector, missing_vector)[0][0]
            location_similarity = cosine_similarity(body_loc_vector, missing_loc_vector)[0][0]
            
            # Text match
            text_match = 0
            if hasattr(body_tattoo, 'texto_extraido') and hasattr(missing_tattoo, 'texto_extraido'):
                if body_tattoo.texto_extraido and missing_tattoo.texto_extraido:
                    if body_tattoo.texto_extraido.lower() == missing_tattoo.texto_extraido.lower():
                        text_match = 1
            
            # Calculate combined scores with different weights
            original_score = (0.6 * text_similarity) + (0.25 * location_similarity) + (0.15 * text_match)
            alt_score1 = (0.7 * text_similarity) + (0.2 * location_similarity) + (0.1 * text_match)
            alt_score2 = (0.5 * text_similarity) + (0.3 * location_similarity) + (0.2 * text_match)
            
            print(f"\nComparison {bi+1}/{mi+1}:")
            print(f"  Body: '{body_tattoo.descripcion_tattoo}' at '{body_tattoo.ubicacion}'")
            print(f"  Missing: '{missing_tattoo.descripcion_tattoo}' at '{missing_tattoo.ubicacion}'")
            print(f"  Text similarity: {text_similarity:.3f}")
            print(f"  Location similarity: {location_similarity:.3f}")
            print(f"  Text match: {text_match}")
            print(f"  Original score (0.6/0.25/0.15): {original_score:.3f}")
            print(f"  Alternative 1 (0.7/0.2/0.1): {alt_score1:.3f}")
            print(f"  Alternative 2 (0.5/0.3/0.2): {alt_score2:.3f}")
            
            # Check against different thresholds
            thresholds = [0.3, 0.4, 0.5, 0.6]
            for t in thresholds:
                print(f"  Would match with threshold {t}: {original_score > t}")

def calculate_similarity_scores_strict(pfsi_df, repd_df, probable_cases_df):
    """
    Calculate similarity scores between tattoos only for specific person pairs 
    defined in the probable_cases_df.
    """
    print("\n" + "="*80)
    print("DEBUG: Starting calculate_similarity_scores_strict()")
    start_time = time.time()
    results = []
    
    print("Preprocessing tattoo data...")
    # Create a combined feature text for each tattoo
    for df_name, df in [("PFSI", pfsi_df), ("REPD", repd_df)]:
        print(f"DEBUG: Processing {df_name} tattoos")
        
        # Verify ID column exists
        if 'id_persona' not in df.columns:
            print(f"ERROR: 'id_persona' column not found in {df_name} dataframe")
            print(f"Available columns: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Include 'diseño' column if it exists
        if 'diseño' in df.columns:
            print(f"DEBUG: {df_name} - 'diseño' column found and will be included")
            df['combined_features'] = (
                df['descripcion_tattoo'] + ' ' + 
                df['ubicacion'] + ' ' + 
                df['texto_extraido'] + ' ' + 
                df['categorias'] + ' ' + 
                df['palabras_clave'] + ' ' +
                df['diseño']
            )
        else:
            print(f"DEBUG: {df_name} - 'diseño' column NOT found")
            df['combined_features'] = (
                df['descripcion_tattoo'] + ' ' + 
                df['ubicacion'] + ' ' + 
                df['texto_extraido'] + ' ' + 
                df['categorias'] + ' ' + 
                df['palabras_clave']
            )
            
        # Apply preprocessing
        print(f"DEBUG: {df_name} - Applying text preprocessing...")
        df['combined_features'] = df['combined_features'].apply(preprocess_text)
        
        # Check for empty features
        empty_features = (df['combined_features'] == '').sum()
        if empty_features > 0:
            print(f"DEBUG: {df_name} - Found {empty_features} empty combined features")
        
        # Print some examples
        print(f"\nDEBUG: {df_name} - Sample combined features:")
        for i, (idx, row) in enumerate(df.head(3).iterrows()):
            print(f"  {i+1}. ID: {row['id_persona']}")
            print(f"     Original: '{row['descripcion_tattoo']}' at '{row['ubicacion']}'")
            print(f"     Combined: '{row['combined_features']}'")
    
    # Create TF-IDF vectors
    print("\nCreating TF-IDF vectors for combined features...")
    vectorizer = TfidfVectorizer(min_df=1)
    all_features = list(pfsi_df['combined_features']) + list(repd_df['combined_features'])
    print(f"DEBUG: Total features for TF-IDF: {len(all_features)}")
    
    try:
        vectorizer.fit(all_features)
        print(f"DEBUG: TF-IDF vectorizer fitted successfully")
        print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    except Exception as e:
        print(f"ERROR: Failed to fit TF-IDF vectorizer: {e}")
        return pd.DataFrame()
    
    # Create location TF-IDF vectors
    print("Creating TF-IDF vectors for location features...")
    location_vectorizer = TfidfVectorizer(min_df=1)
    all_locations = list(pfsi_df['ubicacion']) + list(repd_df['ubicacion'])
    print(f"DEBUG: Total locations for TF-IDF: {len(all_locations)}")
    
    try:
        location_vectorizer.fit(all_locations)
        print(f"DEBUG: Location TF-IDF vectorizer fitted successfully")
        print(f"Location vocabulary size: {len(location_vectorizer.vocabulary_)}")
    except Exception as e:
        print(f"ERROR: Failed to fit location TF-IDF vectorizer: {e}")
        return pd.DataFrame()
    
    # Process each person pair from probable_cases_df
    print(f"Processing {len(probable_cases_df)} person pairs...")
    matches_count = 0
    pbar = tqdm(total=len(probable_cases_df), desc="Processing person pairs")
    
    # Track statistics
    processed_pairs = 0
    pairs_with_tattoos = 0
    total_comparisons = 0
    empty_body_ids = 0
    empty_missing_ids = 0
    
    # Define threshold here, outside the loop
    threshold = 0.4  # Lower from 0.5 to catch more potential matches
    print(f"Using similarity threshold of {threshold} (lowered from original 0.5)")
    
    # Debug sample frequency
    debug_sample_freq = max(1, len(probable_cases_df) // 10)  # Debug every ~10% 
    
    for i, pair in enumerate(probable_cases_df.itertuples()):
        if i % debug_sample_freq == 0:
            print(f"\nDEBUG: Processing pair {i}/{len(probable_cases_df)} ({i/len(probable_cases_df)*100:.1f}%)")
        
        try:
            body_id = pair.body_id
            missing_id = pair.missing_id
            
            if i % debug_sample_freq == 0:
                print(f"DEBUG: Comparing body_id={body_id} with missing_id={missing_id}")
            
            processed_pairs += 1
            
            # Get all tattoos for this specific person pair
            body_tattoos = pfsi_df[pfsi_df['id_persona'] == body_id]
            missing_tattoos = repd_df[repd_df['id_persona'] == missing_id]
            
            if len(body_tattoos) == 0:
                if i % debug_sample_freq == 0:
                    print(f"DEBUG: No tattoos found for body_id {body_id}")
                empty_body_ids += 1
                pbar.update(1)
                continue
                
            if len(missing_tattoos) == 0:
                if i % debug_sample_freq == 0:
                    print(f"DEBUG: No tattoos found for missing_id {missing_id}")
                empty_missing_ids += 1
                pbar.update(1)
                continue
                
            pairs_with_tattoos += 1
            
            if i % debug_sample_freq == 0:
                print(f"DEBUG: Found {len(body_tattoos)} tattoos for body_id {body_id}")
                print(f"DEBUG: Found {len(missing_tattoos)} tattoos for missing_id {missing_id}")
            
            # Transform to vectors
            try:
                body_vectors = vectorizer.transform(body_tattoos['combined_features'])
                missing_vectors = vectorizer.transform(missing_tattoos['combined_features'])
                
                body_loc_vectors = location_vectorizer.transform(body_tattoos['ubicacion'])
                missing_loc_vectors = location_vectorizer.transform(missing_tattoos['ubicacion'])
                
                if i % debug_sample_freq == 0:
                    print(f"DEBUG: Transformed to vectors successfully - shapes: body={body_vectors.shape}, missing={missing_vectors.shape}")
            except Exception as e:
                print(f"ERROR: Failed to transform vectors for pair {i}: {e}")
                pbar.update(1)
                continue
            
            pair_matches = 0
            
            # Compare all tattoos between this person pair
            for bi, body_tattoo in enumerate(body_tattoos.itertuples()):
                body_vector = body_vectors[bi]
                body_loc_vector = body_loc_vectors[bi]
                
                for mi, missing_tattoo in enumerate(missing_tattoos.itertuples()):
                    missing_vector = missing_vectors[mi]
                    missing_loc_vector = missing_loc_vectors[mi]
                    total_comparisons += 1
                    
                    # Calculate similarities
                    try:
                        text_similarity = cosine_similarity(body_vector, missing_vector)[0][0]
                        location_similarity = cosine_similarity(body_loc_vector, missing_loc_vector)[0][0]
                    except Exception as e:
                        print(f"ERROR: Failed to calculate similarity: {e}")
                        continue
                    
                    # Calculate text match similarity
                    text_match = 0
                    if hasattr(body_tattoo, 'texto_extraido') and hasattr(missing_tattoo, 'texto_extraido'):
                        if (body_tattoo.texto_extraido and missing_tattoo.texto_extraido and 
                            body_tattoo.texto_extraido.lower() == missing_tattoo.texto_extraido.lower()):
                            text_match = 1
                    
                    # Combined similarity score
                    combined_score = (0.6 * text_similarity) + (0.25 * location_similarity) + (0.15 * text_match)
                    
                    # Verbose debug for selected pairs
                    if i < 5 and bi < 2 and mi < 2:
                        print(f"\nDETAILED DEBUG - Pair {i}, Body Tattoo {bi}, Missing Tattoo {mi}:")
                        print(f"  Body: '{body_tattoo.descripcion_tattoo}' at '{body_tattoo.ubicacion}'")
                        print(f"  Missing: '{missing_tattoo.descripcion_tattoo}' at '{missing_tattoo.ubicacion}'")
                        print(f"  Similarity scores: text={text_similarity:.3f}, location={location_similarity:.3f}, text_match={text_match}")
                        print(f"  Combined score: {combined_score:.3f}")
                    
                    if combined_score > threshold:  
                        pair_matches += 1
                        matches_count += 1
                        
                        results.append({
                            'pfsi_id': body_id,
                            'repd_id': missing_id,
                            'pfsi_description': body_tattoo.descripcion_tattoo,
                            'repd_description': missing_tattoo.descripcion_tattoo,
                            'pfsi_location': body_tattoo.ubicacion,
                            'repd_location': missing_tattoo.ubicacion,
                            'pfsi_text': body_tattoo.texto_extraido if hasattr(body_tattoo, 'texto_extraido') else '',
                            'repd_text': missing_tattoo.texto_extraido if hasattr(missing_tattoo, 'texto_extraido') else '',
                            'text_similarity': round(text_similarity, 3),
                            'location_similarity': round(location_similarity, 3),
                            'text_match': text_match,
                            'similarity': round(combined_score, 3),
                            'missing_name': pair.missing_name if hasattr(pair, 'missing_name') else '',
                            'missing_age': pair.missing_age if hasattr(pair, 'missing_age') else '',
                            'missing_location': pair.missing_location if hasattr(pair, 'missing_location') else '',
                            'body_name': pair.body_name if hasattr(pair, 'body_name') else '',
                            'body_age': pair.body_age if hasattr(pair, 'body_age') else '',
                            'body_location': pair.body_location if hasattr(pair, 'body_location') else ''
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

        except Exception as e:
            print(f"ERROR: Exception processing pair {i}: {e}")
        
        pbar.update(1)
        if (i+1) % 100 == 0:
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + 1)) * (len(probable_cases_df) - i - 1)
            print(f"\nProcessed {i+1}/{len(probable_cases_df)} person pairs. Found {matches_count} matches so far.")
            print(f"Elapsed: {elapsed:.1f}s, Estimated remaining: {remaining:.1f}s")
    
    pbar.close()
    
    processing_time = time.time() - start_time
    print(f"\nSimilarity calculation completed in {processing_time:.1f} seconds")
    print(f"Found {matches_count} matches above threshold ({threshold})")
    print(f"Total pairs processed: {processed_pairs}")
    print(f"Pairs with tattoos: {pairs_with_tattoos}")
    print(f"Pairs missing body tattoos: {empty_body_ids}")
    print(f"Pairs missing person tattoos: {empty_missing_ids}")
    print(f"Total tattoo comparisons: {total_comparisons}")
    
    if results:
        print("DEBUG: Creating result dataframe")
        result_df = pd.DataFrame(results).sort_values('similarity', ascending=False)
        print(f"DEBUG: Result dataframe shape: {result_df.shape}")
        print("DEBUG: Result dataframe columns:")
        print(result_df.columns.tolist())
    else:
        print("DEBUG: No results found")
        result_df = pd.DataFrame(results)
    
    return result_df

def analyze_potential_matches(matches_df):
    """Analyze and output potential tattoo matches."""
    print("\n" + "="*80)
    print("DEBUG: Starting analyze_potential_matches()")
    print(f"Found {len(matches_df)} potential matches above threshold.")
    
    if len(matches_df) == 0:
        print("DEBUG: No matches found, returning empty DataFrame")
        return pd.DataFrame()
    
    print(f"DEBUG: Matches dataframe has columns: {matches_df.columns.tolist()}")
    
    if 'pfsi_id' in matches_df.columns and 'repd_id' in matches_df.columns:
        # Group by person pairs to find individuals with multiple matching tattoos
        print("Grouping matches by person pairs...")
        try:
            person_pairs = matches_df.groupby(['pfsi_id', 'repd_id']).agg({
                'similarity': ['count', 'mean', 'max']
            })
            
            person_pairs.columns = ['match_count', 'avg_similarity', 'max_similarity']
            person_pairs = person_pairs.sort_values(['match_count', 'avg_similarity'], ascending=False)
            
            print(f"DEBUG: Person pairs dataframe shape: {person_pairs.shape}")
            print(f"\nFound {len(person_pairs)} unique person pairs with at least one matching tattoo")
            pairs_with_multiple = person_pairs[person_pairs['match_count'] > 1]
            print(f"Found {len(pairs_with_multiple)} person pairs with multiple tattoo matches")
            
            print("\nDEBUG: Distribution of match counts:")
            match_count_dist = person_pairs['match_count'].value_counts().sort_index()
            for count, freq in match_count_dist.items():
                print(f"  {count} match(es): {freq} person pairs")
            
            print("\nDEBUG: Top person matches by match count:")
            print(person_pairs.head(10))
            
            print("\nDEBUG: Top individual tattoo matches by similarity score:")
            print(matches_df[['pfsi_id', 'repd_id', 'pfsi_description', 'repd_description', 
                              'pfsi_location', 'repd_location', 'similarity']].head(10))
            
            return person_pairs
        except Exception as e:
            print(f"ERROR: Failed to analyze matches: {e}")
            return pd.DataFrame()
    else:
        print("DEBUG: No matches found with 'pfsi_id' and 'repd_id' columns.")
        print(f"Available columns: {matches_df.columns.tolist()}")
        return pd.DataFrame()

def verify_id_matches(pfsi_df, repd_df, probable_cases_df):
    """
    Verify ID matches between datasets and fix format issues if needed.
    """
    print("\n" + "="*80)
    print("VERIFYING ID MATCHES BETWEEN DATASETS")
    
    # Check ID data types
    print("\nID column data types:")
    if 'id_persona' in pfsi_df.columns:
        print(f"PFSI id_persona type: {pfsi_df['id_persona'].dtype}")
        print(f"PFSI id_persona example: {pfsi_df['id_persona'].iloc[0]} ({type(pfsi_df['id_persona'].iloc[0]).__name__})")
    
    if 'id_persona' in repd_df.columns:
        print(f"REPD id_persona type: {repd_df['id_persona'].dtype}")
        print(f"REPD id_persona example: {repd_df['id_persona'].iloc[0]} ({type(repd_df['id_persona'].iloc[0]).__name__})")
    
    if 'body_id' in probable_cases_df.columns:
        print(f"Probable cases body_id type: {probable_cases_df['body_id'].dtype}")
        print(f"Probable cases body_id example: {probable_cases_df['body_id'].iloc[0]} ({type(probable_cases_df['body_id'].iloc[0]).__name__})")
    
    if 'missing_id' in probable_cases_df.columns:
        print(f"Probable cases missing_id type: {probable_cases_df['missing_id'].dtype}")
        print(f"Probable cases missing_id example: {probable_cases_df['missing_id'].iloc[0]} ({type(probable_cases_df['missing_id'].iloc[0]).__name__})")
    
    # Attempt to fix any inconsistencies
    modified = False
    
    # Ensure all ID columns are strings for consistent comparison
    if 'id_persona' in pfsi_df.columns and pfsi_df['id_persona'].dtype != 'object':
        pfsi_df['id_persona'] = pfsi_df['id_persona'].astype(str)
        print("Converted PFSI id_persona to string")
        modified = True
    
    if 'id_persona' in repd_df.columns and repd_df['id_persona'].dtype != 'object':
        repd_df['id_persona'] = repd_df['id_persona'].astype(str)
        print("Converted REPD id_persona to string")
        modified = True
    
    if 'body_id' in probable_cases_df.columns and probable_cases_df['body_id'].dtype != 'object':
        probable_cases_df['body_id'] = probable_cases_df['body_id'].astype(str)
        print("Converted probable_cases body_id to string")
        modified = True
    
    if 'missing_id' in probable_cases_df.columns and probable_cases_df['missing_id'].dtype != 'object':
        probable_cases_df['missing_id'] = probable_cases_df['missing_id'].astype(str)
        print("Converted probable_cases missing_id to string")
        modified = True
        
    # Try checking for matches again after conversion
    pfsi_ids = set(pfsi_df['id_persona'].unique())
    repd_ids = set(repd_df['id_persona'].unique())
    body_ids = set(probable_cases_df['body_id'].unique())
    missing_ids = set(probable_cases_df['missing_id'].unique())
    
    # Check if body_ids are found in PFSI
    body_ids_in_pfsi = pfsi_ids.intersection(body_ids)
    print(f"\nBody IDs found in PFSI dataset (after conversion): {len(body_ids_in_pfsi)} out of {len(body_ids)} ({len(body_ids_in_pfsi)/len(body_ids)*100:.1f}%)")
    
    # Check if missing_ids are found in REPD
    missing_ids_in_repd = repd_ids.intersection(missing_ids)
    print(f"Missing IDs found in REPD dataset (after conversion): {len(missing_ids_in_repd)} out of {len(missing_ids)} ({len(missing_ids_in_repd)/len(missing_ids)*100:.1f}%)")
    
    # If still no matches, check format patterns
    if len(body_ids_in_pfsi) == 0:
        print("\nStill no body_id matches found. Checking ID formats...")
        # Sample and compare ID formats
        pfsi_id_samples = list(pfsi_ids)[:5]
        body_id_samples = list(body_ids)[:5]
        
        print(f"PFSI ID samples: {pfsi_id_samples}")
        print(f"Body ID samples: {body_id_samples}")
        
        # Check if body_ids might be a subset of PFSI IDs (missing leading zeros, etc.)
        for bid in body_id_samples:
            potential_matches = [pid for pid in pfsi_ids if pid.endswith(bid) or bid.endswith(pid)]
            if potential_matches:
                print(f"Body ID {bid} has potential PFSI matches: {potential_matches}")
    
    # Return whether we found matches and modified the dataframes
    return len(body_ids_in_pfsi) > 0, len(missing_ids_in_repd) > 0, modified

def main():
    print("\n" + "="*80)
    print("DEBUG: Script starting")
    start_time = time.time()
    print("Starting STRICT tattoo matching process using LLM-processed datasets (only comparing linked person pairs)...")
    
    # Load data with more debug info
    print("\nDEBUG: Step 1 - Loading data")
    pfsi_df, repd_df, probable_cases_df = load_data()
    
    if pfsi_df is None or repd_df is None or probable_cases_df is None:
        print("ERROR: Failed to load one or more datasets. Exiting.")
        return
    
    print(f"Loaded {len(pfsi_df)} LLM-processed PFSI tattoos, {len(repd_df)} LLM-processed REPD tattoos, and {len(probable_cases_df)} probable case pairs")
    
    # Print schema to verify columns
    print("\nDEBUG: PFSI columns:", pfsi_df.columns.tolist())
    print("DEBUG: REPD columns:", repd_df.columns.tolist())
    print("DEBUG: Probable cases columns:", probable_cases_df.columns.tolist())
    
    # Check for key columns
    for df_name, df, req_cols in [
        ("PFSI", pfsi_df, ['id_persona', 'descripcion_tattoo', 'ubicacion']),
        ("REPD", repd_df, ['id_persona', 'descripcion_tattoo', 'ubicacion']),
        ("Probable cases", probable_cases_df, ['body_id', 'missing_id'])
    ]:
        missing = [col for col in req_cols if col not in df.columns]
        if missing:
            print(f"ERROR: {df_name} is missing required columns: {missing}")
            return
    
    # Add this after checking key columns and before running similarity analysis
    # Check for any overlapping IDs between datasets to validate the data
    print("\nChecking for matching IDs between datasets...")
    pfsi_ids = set(pfsi_df['id_persona'].unique())
    repd_ids = set(repd_df['id_persona'].unique())
    body_ids = set(probable_cases_df['body_id'].unique())
    missing_ids = set(probable_cases_df['missing_id'].unique())
    
    # Check if body_ids are found in PFSI
    body_ids_in_pfsi = pfsi_ids.intersection(body_ids)
    print(f"Body IDs found in PFSI dataset: {len(body_ids_in_pfsi)} out of {len(body_ids)} ({len(body_ids_in_pfsi)/len(body_ids)*100:.1f}%)")
    
    # Check if missing_ids are found in REPD
    missing_ids_in_repd = repd_ids.intersection(missing_ids)
    print(f"Missing IDs found in REPD dataset: {len(missing_ids_in_repd)} out of {len(missing_ids)} ({len(missing_ids_in_repd)/len(missing_ids)*100:.1f}%)")
    
    # Check for valid pairs (both IDs exist)
    valid_count = 0
    sample_size = min(1000, len(probable_cases_df))
    for _, row in probable_cases_df.head(sample_size).iterrows():
        body_id = row['body_id']
        missing_id = row['missing_id']
        
        body_exists = len(pfsi_df[pfsi_df['id_persona'] == body_id]) > 0
        missing_exists = len(repd_df[repd_df['id_persona'] == missing_id]) > 0
        
        if body_exists and missing_exists:
            valid_count += 1
    
    print(f"Valid pairs in sample (both IDs exist): {valid_count} out of {sample_size} ({valid_count/sample_size*100:.1f}%)")
    
    if valid_count == 0:
        print("\nWARNING: No valid pairs found in the sample. There might be an ID mismatch issue.")
        print("The analysis will likely fail since there are no valid comparisons to make.")
        
        # Print ID format examples to help debug
        print("\nID format examples:")
        if len(pfsi_df) > 0:
            print(f"PFSI ID example: {pfsi_df['id_persona'].iloc[0]} (type: {type(pfsi_df['id_persona'].iloc[0]).__name__})")
        if len(repd_df) > 0:
            print(f"REPD ID example: {repd_df['id_persona'].iloc[0]} (type: {type(repd_df['id_persona'].iloc[0]).__name__})")
        if len(probable_cases_df) > 0:
            print(f"Body ID example: {probable_cases_df['body_id'].iloc[0]} (type: {type(probable_cases_df['body_id'].iloc[0]).__name__})")
            print(f"Missing ID example: {probable_cases_df['missing_id'].iloc[0]} (type: {type(probable_cases_df['missing_id'].iloc[0]).__name__})")
            
        # Suggest potential solutions
        print("\nPossible solutions:")
        print("1. Check the ID formats - they might need type conversion")
        print("2. Verify the ID column names are correct")
        print("3. Check if the datasets actually contain overlapping records")
    
    # Continue with existing analysis
    # Analyze a sample of tattoo pairs to understand similarity distributions
    scores_df = analyze_similarity_distribution(pfsi_df, repd_df, probable_cases_df, sample_size=20)
    
    # Manual inspection of specific pairs (replace with actual IDs if known)
    manual_inspection(pfsi_df, repd_df)
    
    # Calculate similarity scores only for the specific person pairs
    print("\nDEBUG: Step 2 - Calculating similarity scores")
    matches_df = calculate_similarity_scores_strict(pfsi_df, repd_df, probable_cases_df)
    
    # Analyze the results
    print("\nDEBUG: Step 3 - Analyzing potential matches")
    person_matches = analyze_potential_matches(matches_df)
    
    # Create directories if they don't exist
    print("\nDEBUG: Step 4 - Saving results")
    try:
        os.makedirs('./ds/csv/cross_examples/', exist_ok=True)
        print("DEBUG: Created ./ds/csv/cross_examples/ directory if it didn't exist")
    except Exception as e:
        print(f"ERROR: Failed to create directories: {e}")
    
    # Save results
    print("Saving results to CSV files...")
    try:
        matches_df.to_csv('./ds/csv/cross_examples/tattoo_matches_strict_llm.csv', index=False)
        print(f"DEBUG: Saved {len(matches_df)} tattoo matches to CSV")
        
        if not person_matches.empty:
            person_matches.to_csv('./ds/csv/cross_examples/person_matches_strict_llm.csv')
            print(f"DEBUG: Saved {len(person_matches)} person matches to CSV")
    except Exception as e:
        print(f"ERROR: Failed to save results: {e}")
    
    total_time = time.time() - start_time
    print(f"\nDEBUG: Total processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print("Results saved to 'ds/csv/cross_examples/tattoo_matches_strict_llm.csv' and 'ds/csv/cross_examples/person_matches_strict_llm.csv'")

if __name__ == "__main__":
    main()
