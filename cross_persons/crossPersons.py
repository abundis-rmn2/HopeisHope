import pandas as pd
import re
from datetime import datetime
from difflib import SequenceMatcher
from tqdm import tqdm  # Add tqdm for progress bar

def match_missing_persons_with_bodies():
    """Find potential matches between missing persons and unidentified bodies"""
    
    # Load datasets
    missing_df = pd.read_csv('/home/abundis/PycharmProjects/HopeisHope/csv/equi/repd_vp_cedulas_principal.csv')
    bodies_df = pd.read_csv('/home/abundis/PycharmProjects/HopeisHope/csv/equi/pfsi_v2_principal.csv')
    
    # Filter out records where people have been found alive
    missing_filtered = missing_df[missing_df['condicion_localizacion'] != 'CON VIDA'].copy()
    
    # Convert date columns to datetime format
    missing_filtered['fecha_desaparicion'] = pd.to_datetime(missing_filtered['fecha_desaparicion'])
    bodies_df['Fecha_Ingreso'] = pd.to_datetime(bodies_df['Fecha_Ingreso'])
    
    matches = []
    
    # For each missing person
    for _, missing in tqdm(missing_filtered.iterrows(), total=missing_filtered.shape[0], desc="Processing missing persons"):
        # For each unidentified body
        for _, body in tqdm(bodies_df.iterrows(), total=bodies_df.shape[0], desc="Processing bodies", leave=False):
            score = 0
            match_reasons = []
            
            # MANDATORY: Check if disappearance date is before forensic intake
            if missing['fecha_desaparicion'] >= body['Fecha_Ingreso']:
                continue
                
            # MANDATORY: Check if sex matches
            if missing['sexo'].upper() != body['Sexo'].upper():
                continue
            
            # Check age similarity (within 10 years range)
            missing_age = missing['edad_momento_desaparicion']
            body_age = body['Edad']
            
            if isinstance(body_age, str) and "-" in body_age:
                # Handle age range format (e.g., "66-70 años")
                age_range = re.findall(r'(\d+)-(\d+)', body_age)
                if age_range:
                    min_age, max_age = map(int, age_range[0])
                    if min_age - 10 <= missing_age <= max_age + 10:
                        score += 1
                        match_reasons.append(f"Age within range")
            
            # Name similarity check (only if body's name isn't just "PFSI")
            body_name = body['Probable_nombre']
            missing_name = missing['nombre_completo']
            
            if "PFSI" not in body_name:
                name_similarity = SequenceMatcher(None, missing_name.upper(), body_name.upper()).ratio()
                if name_similarity > 0.5:  # Threshold for name similarity
                    score += name_similarity * 2  # Weight name similarity higher
                    match_reasons.append(f"Name similarity: {name_similarity:.2f}")
            
            # Add location match bonus
            if missing['municipio'].upper() in body['Delegacion_IJCF'].upper():
                score += 0.5
                match_reasons.append("Same municipality")
            
            # Calculate days between disappearance and body discovery
            days_between = (body['Fecha_Ingreso'] - missing['fecha_desaparicion']).days
            
            # Add to potential matches if score > 0
            if score > 0:
                matches.append({
                    'missing_id': missing['id_cedula_busqueda'],
                    'missing_name': missing_name,
                    'missing_age': missing_age,
                    'missing_date': missing['fecha_desaparicion'].strftime('%Y-%m-%d'),
                    'missing_location': missing['municipio'],
                    'body_id': body['ID'],
                    'body_name': body_name,
                    'body_age': body_age,
                    'body_date': body['Fecha_Ingreso'].strftime('%Y-%m-%d'),
                    'body_location': body['Delegacion_IJCF'],
                    'days_between': days_between,
                    'score': score,
                    'match_reasons': ", ".join(match_reasons)
                })
    
    # Convert to DataFrame and sort by score
    results_df = pd.DataFrame(matches).sort_values('score', ascending=False)
    return results_df

if __name__ == "__main__":
    results = match_missing_persons_with_bodies()
    print(f"Found {len(results)} potential matches")
    if not results.empty:
        print(results.head(10))  # Show top 10 matches
        results.to_csv('./csv/cross_examples/person_matches_name_age.csv', index=False)