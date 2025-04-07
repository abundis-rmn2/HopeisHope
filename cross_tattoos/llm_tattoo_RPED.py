import pandas as pd
import os
import re
from transformers import pipeline

def load_csv_file():
    """Load the cedulas_senas CSV file."""
    # Get absolute path to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(script_dir, 'csv', 'equi')
    
    # Verify directory exists
    if not os.path.exists(csv_dir):
        print(f"Directory not found: {csv_dir}")
        return None
        
    try:
        # Load repd_vp_cedulas_senas.csv file
        file_path = os.path.join(csv_dir, 'repd_vp_cedulas_senas.csv')
        df = pd.read_csv(file_path).sample(300)
        return df
    
    except FileNotFoundError as e:
        print(f"Error: Could not find file at {file_path}")
        print(f"Detailed error: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

# Function to categorize tattoo descriptions by keywords
def categorize_keywords(tattoo_description, classifier):
    """Categorize tattoo description based on keywords using a language model."""
    if pd.isna(tattoo_description):
        return [], []
        
    # Use the classifier to get entities
    entities = classifier(tattoo_description)
    categories = []
    keywords = []
    
    for entity in entities:
        entity_group = entity.get('entity_group', entity.get('entity'))
        if entity_group == 'MISC':
            categories.append('Otros')
        elif entity_group == 'PER':
            categories.append('Nombre')
        elif entity_group == 'LOC':
            categories.append('Ubicación')
        elif entity_group == 'ORG':
            categories.append('Organización')
        keywords.append(entity['word'])
    
    return list(set(categories)), list(set(keywords))

# Function to extract tattoo locations from descriptions
def extract_location(description):
    """Extract body locations from tattoo descriptions."""
    if pd.isna(description):
        return ""
        
    locations = [
        'ROSTRO', 'CUERPO', 'BRAZO', 'HOMBRO', 'MANO', 'PIERNA', 'TORSO', 'ESCAPULA', 
        'CABEZA', 'CLAVICULA', 'PECTORAL', 'FLANCO', 'ANTEBRAZO', 'OJO', 'CARA', 'CUELLO', 
        'ESPALDA', 'EXTREMIDAD', 'MUSLO', 'RODILLA', 'DORSO', 'ABDOMEN', 'TORAX', 
        'MUÑECA', 'OREJA', 'PECHO', 'COSTADO', 'PANTORRILLA', 'DORSAL', 'CRANEO', 'PULGAR', 
        'DEDOS', 'INDICE', 'MEÑIQUE', 'TOBILLO', 'CADERA', 'LENGUA', 'NARIZ', 'CEJA', 
        'BUSTO', 'CODO', 'FALANGE', 'LUMBAR', 'TALON', 'PLANTA', 'NUCA', 'OMBLIGO', 
        'PALMA', 'GLÚTEO', 'ENTREPIERNA', 'INGLE', 'ESPINILLA', 'LABIO', 'MEJILLA', 
        'SENO', 'HUESO', 'TRAPECIO', 'INTERCOSTAL', 'AXILA', 'PIE', 'TALÓN', 'EMPEINE', 
        'DEDO GORDO', 'NUDILLO', 'COSTILLAS'
    ]
    
    laterality = ['DERECHO', 'DERECHA', 'IZQUIERDO', 'IZQUIERDA']
    
    found_locations = []
    description_upper = description.upper()
    
    for loc in locations:
        if loc in description_upper:
            # Check for laterality near the location
            position = description_upper.find(loc)
            context = description_upper[max(0, position-10):min(len(description_upper), position+25)]
            side = ""
            for lat in laterality:
                if lat in context:
                    side = lat
                    break
                    
            complete_loc = f"{loc} {side}".strip()
            found_locations.append(complete_loc)
    
    return ', '.join(found_locations)

# Function to split tattoo descriptions into individual tattoos
def split_tattoos(text):
    """Split multiple tattoo descriptions into individual tattoos."""
    if pd.isna(text):
        return []
        
    # Replace special characters and normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    
    # If description has numbered items (1.-, 2.-, etc.)
    if re.search(r'\d+\.-|\d+\)', text):
        parts = re.split(r'\d+\.-|\d+\)', text)
    # Split by comma or "y" when multiple tattoos are described
    elif "," in text:
        parts = [p.strip() for p in text.split(",")]
    # Split by descriptions between quotes (likely separate tattoos)
    elif '"' in text:
        parts = []
        fragments = re.split(r'[""]', text)
        for i in range(0, len(fragments)-1, 2):
            if i+1 < len(fragments):
                item = fragments[i].strip()
                quoted_part = fragments[i+1].strip()
                if item:  # If there's context before the quoted part
                    parts.append(f"{item} \"{quoted_part}\"")
                else:  # Just the quoted part
                    parts.append(quoted_part)
    else:
        # If we can't split, treat as a single tattoo
        parts = [text]
    
    # Clean up parts
    clean_parts = []
    for part in parts:
        part = part.strip()
        if part and not re.match(r'^\d{1,4}$', part):
            # Remove "EN" from the beginning if present
            if part.upper().startswith("EN "):
                part = part[3:].strip()
            clean_parts.append(part)
            
    return clean_parts

def extract_text_in_quotes(text):
    """Extract text inside quotes from description."""
    if pd.isna(text):
        return ""
        
    # Find all text inside quotes (either "" or "")
    matches = re.findall(r'[""]([^""]+)[""]', text)
    return ', '.join(matches) if matches else ""

def complete_description(tattoo_description, generator):
    """Complete the tattoo description using a language model."""
    prompt = f"Actúa como médico forense y retoma: {tattoo_description} para sintetizar y completar la descripción del tatuaje."
    completion = generator(prompt, max_new_tokens=10, num_return_sequences=1)
    print(f"Prompt: {prompt}")
    print(f"Completion: {completion[0]['generated_text']}")
    return completion[0]['generated_text']

def main():
    # Load the CSV file
    df = load_csv_file()
    if df is None:
        return
        
    print(f"Loaded DataFrame with shape: {df.shape}")
    
    # Initialize the language model classifier and generator
    classifier = pipeline('ner', model='mrm8488/bert-spanish-cased-finetuned-ner', tokenizer='mrm8488/bert-spanish-cased-finetuned-ner')
    generator = pipeline('text-generation', model='datificate/gpt2-small-spanish', tokenizer='datificate/gpt2-small-spanish')
    
    # Filter for tattoo entries
    tattoo_df = df[df['tipo_sena'] == 'TATUAJES'].copy()
    print(f"Found {len(tattoo_df)} tattoo entries")
    
    # Lists for collecting individual tattoo data
    all_tattoos = []
    
    # Process each tattoo entry
    for _, row in tattoo_df.iterrows():
        person_id = row['id_cedula_busqueda']
        description = row['descripcion']
        
        # Split description into individual tattoos
        individual_tattoos = split_tattoos(description)
        
        for tattoo in individual_tattoos:
            # Skip very short descriptions
            if len(tattoo) < 3:
                continue
                
            # Extract information
            categories, keywords = categorize_keywords(tattoo, classifier)
            location = extract_location(tattoo)
            text = extract_text_in_quotes(tattoo)
            completed_description = complete_description(tattoo, generator)
            
            all_tattoos.append({
                'id_persona': person_id,
                'descripcion_original': description,
                'descripcion_tattoo': tattoo,
                'ubicacion': location,
                'texto_extraido': text,
                'descripcion_completa': completed_description,
                'categorias': ', '.join(categories),
                'palabras_clave': ', '.join(keywords)
            })
    
    # Create DataFrame of processed tattoos
    result_df = pd.DataFrame(all_tattoos)
    print(f"Created DataFrame with {len(result_df)} individual tattoos")
    
    # Save the results
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv', 'equi')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'llm_tatuajes_procesados_REPD.csv')
    result_df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
