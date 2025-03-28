#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cross_llm_tattoo.py - Compares tattoos between two CSV files to find relationships
based on location, figure/category, and description
"""

import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm  # Add tqdm for progress bar

# File paths
PFSI_FILE = '/home/abundis/PycharmProjects/HopeisHope/ds/csv/equi/llm_tatuajes_procesados_PFSI.csv'
REPD_FILE = '/home/abundis/PycharmProjects/HopeisHope/ds/csv/equi/llm_tatuajes_procesados_REPD.csv'
MAX_ROWS = 1  # Number of rows to analyze from PFSI file

def load_data(file_path, limit=None):
    """Load data from CSV and limit to first n rows if limit is specified"""
    try:
        df = pd.read_csv(file_path)
        df = df[df['descripcion_original'].str.lower() != 'no presenta']  # Filter out records with 'No presenta'
        if limit:
            df = df.head(limit)
        print(f"Loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return pd.DataFrame()

def clean_text(text):
    """Clean and normalize text for comparison"""
    if pd.isna(text) or text is None:
        return ""
    
    # Convert to lowercase and remove special characters
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_text_similarity(text1, text2):
    """Calculate similarity between two texts using TF-IDF and cosine similarity"""
    if not text1 or not text2:
        return 0.0
    
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except:
        return 0.0

def is_location_match(loc1, loc2, threshold=0.6):
    """Check if two tattoo locations match"""
    loc1_clean = clean_text(loc1)
    loc2_clean = clean_text(loc2)
    
    # Direct match for common body parts
    body_parts = ['brazo', 'antebrazo', 'pierna', 'pecho', 'espalda', 'mano', 
                 'hombro', 'cuello', 'tobillo', 'muñeca', 'torso', 'abdomen']
    
    for part in body_parts:
        if part in loc1_clean and part in loc2_clean:
            return True
    
    # If no direct match, use similarity score
    return calculate_text_similarity(loc1_clean, loc2_clean) >= threshold

def is_figure_match(cat1, cat2, keys1, keys2, threshold=0.5):
    """Check if tattoo figures/categories match"""
    # Combine categories and keywords for better matching
    text1 = f"{clean_text(cat1)} {clean_text(keys1)}"
    text2 = f"{clean_text(cat2)} {clean_text(keys2)}"
    
    # Check for common categories
    common_categories = ['religiosos', 'figura humana', 'animales', 'letras-números',
                        'plantas', 'símbolos', 'objetos', 'fantasía', 'demoniaco']
    
    for cat in common_categories:
        if cat in text1 and cat in text2:
            return True
    
    # If no common category found, use text similarity
    return calculate_text_similarity(text1, text2) >= threshold

def is_description_match(desc1, desc2, threshold=0.5):
    """Check if tattoo descriptions match"""
    desc1_clean = clean_text(desc1)
    desc2_clean = clean_text(desc2)
    return calculate_text_similarity(desc1_clean, desc2_clean) >= threshold

def find_tattoo_relationships(pfsi_df, repd_df):
    """Find relationships between tattoos in both datasets"""
    relationships = []
    
    for i, pfsi_row in tqdm(pfsi_df.iterrows(), total=pfsi_df.shape[0], desc="Processing PFSI records"):
        for j, repd_row in repd_df.iterrows():
            # Extract data for comparison
            pfsi_id = pfsi_row.get('id_persona', f"Row_{i}")
            repd_id = repd_row.get('id_persona', f"Row_{j}")
            
            # Location comparison
            pfsi_location = pfsi_row.get('ubicacion', "")
            repd_location = repd_row.get('ubicacion', "")
            location_match = is_location_match(pfsi_location, repd_location)
            
            # Figure/category comparison
            pfsi_categories = pfsi_row.get('categorias', "")
            repd_categories = repd_row.get('categorias', "")
            pfsi_keywords = pfsi_row.get('palabras_clave', "")
            repd_keywords = repd_row.get('palabras_clave', "")
            figure_match = is_figure_match(pfsi_categories, repd_categories, 
                                          pfsi_keywords, repd_keywords)
            
            # Description comparison
            pfsi_desc = pfsi_row.get('descripcion_tattoo', "")
            repd_desc = repd_row.get('descripcion_tattoo', "")
            desc_match = is_description_match(pfsi_desc, repd_desc)
            
            # Calculate overall similarity score
            match_score = (location_match + figure_match + desc_match) / 3
            
            # Print match details for debugging
            print(f"\nComparing PFSI ID {pfsi_id} with REPD ID {repd_id}")
            print(f"Location: {pfsi_location} vs {repd_location} -> Match: {location_match}")
            print(f"Categories: {pfsi_categories}/{pfsi_keywords} vs {repd_categories}/{repd_keywords} -> Match: {figure_match}")
            print(f"Description: {pfsi_desc} vs {repd_desc} -> Match: {desc_match}")
            print(f"Overall score: {match_score:.2f}")
            print("-" * 50)
            
            # If any significant match, add to results
            if match_score >= 0.4:  # Lower threshold to catch more potential matches
                relationships.append({
                    'pfsi_id': pfsi_id,
                    'repd_id': repd_id,
                    'overall_score': match_score,
                    'location_match': location_match,
                    'figure_match': figure_match,
                    'description_match': desc_match,
                    'pfsi_location': pfsi_location,
                    'repd_location': repd_location,
                    'pfsi_description': pfsi_desc,
                    'repd_description': repd_desc
                })
    
    return pd.DataFrame(relationships).sort_values('overall_score', ascending=False)

def main():
    print("Cross-LLM Tattoo Analysis")
    print("------------------------")
    
    # Load data
    pfsi_data = load_data(PFSI_FILE, limit=MAX_ROWS)
    repd_data = load_data(REPD_FILE)
    
    if pfsi_data.empty or repd_data.empty:
        print("Error: One or both datasets could not be loaded.")
        return
    
    # Find relationships
    print("\nAnalyzing tattoo relationships...")
    relationships = find_tattoo_relationships(pfsi_data, repd_data)
    
    # Display results
    if relationships.empty:
        print("\nNo significant relationships found between tattoos in the datasets.")
    else:
        print(f"\nFound {len(relationships)} potential relationships between tattoos:")
        
        # Display top matches
        for idx, rel in relationships.head(10).iterrows():
            print("\n" + "="*80)
            print(f"Relationship #{idx+1} - Overall Score: {rel['overall_score']:.2f}")
            print(f"PFSI ID: {rel['pfsi_id']} | REPD ID: {rel['repd_id']}")
            print("-"*80)
            print(f"Location Match: {'Yes' if rel['location_match'] else 'No'}")
            print(f"  PFSI: {rel['pfsi_location']}")
            print(f"  REPD: {rel['repd_location']}")
            print("-"*80)
            print(f"Figure/Category Match: {'Yes' if rel['figure_match'] else 'No'}")
            print("-"*80)
            print(f"Description Match: {'Yes' if rel['description_match'] else 'No'}")
            print(f"  PFSI: {rel['pfsi_description']}")
            print(f"  REPD: {rel['repd_description']}")
        
        # Save results to CSV
        output_file = 'tattoo_relationships.csv'
        relationships.to_csv(output_file, index=False)
        print(f"\nDetailed results saved to {output_file}")

if __name__ == "__main__":
    main()
