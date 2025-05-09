import pandas as pd
import os
import re

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
        df = pd.read_csv(file_path)
        return df
    
    except FileNotFoundError as e:
        print(f"Error: Could not find file at {file_path}")
        print(f"Detailed error: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

# Function to categorize tattoo descriptions by keywords
def categorize_keywords(tattoo_description):
    """Categorize tattoo description based on keywords."""
    if pd.isna(tattoo_description):
        return [], []
        
    keywords = {
        "Figura Humana": ["rostro", "figura", "hombre", "mujer", "persona", "cuerpo", "ojos", "silueta", "humana", "humano", "cráneo", "calavera", "busto", "caricatura", "personaje"],
        "Letras-Números": ["letra", "números", "leyenda", "palabras", "texto", "nombre", "frase", "cursiva", "manuscrita", "mayúsculas", "cursivo", "tipografía", "tipologia", "script", "leyendas", "numeros", "romanos", "cursivas", "letras", "palabra", "numeros", "tipografia", "mayusculas"],
        "Simbolos": ["símbolo", "cruz", "rojo", "negro", "símbolos", "machete", "corazón", "estrella", "infinito", "triángulo", "cruz cristiana", "cruzpalabras", "corazon", "corazones", "estrellas", "triangulo", "círculo", "circulo", "geométrico", "geométricos", "guadaña", "ancla", "flecha", "espada", "daga", "signo", "trébol", "trebol", "diamante", "asterisco", "asteriscos", "piramide", "playboy", "atrapasueños", "brujula", "mandala", "yin", "yang", "ying", "calendario", "egipcio", "baraja", "carta", "cartas", "reloj", "bandera", "logotipo", "logo", "alegoría", "alegoria"],
        "Animales": ["tigre", "león", "zorro", "lobo", "perro", "gallo", "pez", "pájaro", "conejo", "águila", "aguila", "serpiente", "dragón", "dragon", "mariposa", "pantera", "gato", "felino", "buho", "búho", "aves", "ave", "cobra", "alacrán", "alacran", "escorpión", "araña", "pavo", "paloma", "colibrí", "colibri", "tortuga", "ballena", "delfín", "delfin", "murciélago", "murcielago", "halcón", "halcon", "águila", "aguila", "leopardo", "jaguar", "rinoceronte", "elefante", "tiburón", "tiburon", "orca", "ballena", "delfín", "delfin", "murciélago", "murcielago", "halcón", "halcon", "águila", "aguila", "leopardo", "jaguar", "rinoceronte", "elefante", "tiburón", "tiburon", "orca"],
        "Religiosos": ["santa muerte", "cruz cristiana", "anj", "horus", "dios", "ángel", "santo", "religión", "virgen", "jesús", "jesucristo", "cristo", "maría", "guadalupe", "san", "judas", "sagrado", "oración", "oracion", "rosario", "biblia", "santísima", "santisima", "santos", "ángeles", "demonios", "demonio", "diablo", "infierno", "cielo", "paraíso", "paraiso", "altar", "templo", "iglesia", "católica", "catolica", "buda", "zen", "mandala", "yoga", "meditación", "meditacion", "karma", "chakra", "om", "símbolo religioso", "simbolo religioso"],
        "Nombre": ["jose", "alberto", "juan", "adriana", "carlos", "maria", "luis", "ana", "david", "eduardo", "martha", "victor", "tadeo", "alejandra", "santiago", "alejandro", "laura", "raul", "lopez", "silvia", "jesus", "juan", "maria", "luis", "ana", "david", "eduardo", "martha", "victor", "tadeo", "alejandra", "santiago", "alejandro", "laura", "raul", "lopez", "silvia", "jesus"],
        "Otros": ["irreconocible", "indeterminado", "abstracto", "floral", "combinado", "fantasía", "demonio", "manga", "cuerno", "flores", "planta", "hojas", "ramas", "árbol", "arbol", "paisaje", "naturaleza", "sol", "luna", "estrella", "estrellas", "cielo", "nube", "mar", "océano", "oceano", "montaña", "montana", "fuego", "llamas", "agua", "tierra", "viento", "vientos", "rayo", "rayos", "trueno", "truenos", "arcoíris", "arcoiris", "galaxia", "universo", "planeta", "satélite", "satelite", "cometa", "meteorito", "asteroide", "espacio", "cosmos", "alien", "ovni", "robot", "androide", "cibernético", "cibernetico", "futurista", "retro", "vintage", "moderno", "clásico", "clasico", "arte", "dibujo", "pintura", "escultura", "grafiti", "graffiti", "mural", "cartel", "poster", "bandera", "emblema", "insignia", "medalla", "trofeo", "premio", "trofeo", "copa", "copa", "trofeo", "premio", "trofeo", "copa", "copa"]
    }

    categories = []
    triggering_fragments = []

    # Check each category of keywords
    for category, terms in keywords.items():
        matched_terms = [term for term in terms if term.lower() in tattoo_description.lower()]
        if matched_terms:
            categories.append(category)
            triggering_fragments.append(', '.join(matched_terms))
    
    return categories, triggering_fragments

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

def main():
    # Load the CSV file
    df = load_csv_file()
    if df is None:
        return
        
    print(f"Loaded DataFrame with shape: {df.shape}")
    
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
            categories, keywords = categorize_keywords(tattoo)
            location = extract_location(tattoo)
            text = extract_text_in_quotes(tattoo)
            
            all_tattoos.append({
                'id_persona': person_id,
                'descripcion_original': description,
                'descripcion_tattoo': tattoo,
                'ubicacion': location,
                'texto_extraido': text,
                'categorias': ', '.join(categories),
                'palabras_clave': ', '.join(keywords)
            })
    
    # Create DataFrame of processed tattoos
    result_df = pd.DataFrame(all_tattoos)
    print(f"Created DataFrame with {len(result_df)} individual tattoos")
    
    # Save the results
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv', 'equi')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'tatuajes_procesados_REPD.csv')
    result_df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()