# deepseek_cat_tattoo_REPD.py

import pandas as pd
import os
import json
import argparse
from shared import generate_with_deepseek_api, clean_response, save_results
from dotenv import load_dotenv

def load_csv_file(start_row=12814, end_row=None):
    """Load the REPD CSV file with specified row range.
    
    Args:
        start_row (int): Starting row index (0-based)
        end_row (int, optional): Ending row index (exclusive). If None, read until end.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(script_dir, '..', 'csv', 'equi')
    
    if not os.path.exists(csv_dir):
        print(f"Directory not found: {csv_dir}")
        return None
        
    try:
        file_path = os.path.join(csv_dir, 'repd_vp_cedulas_senas.csv')
        df = pd.read_csv(file_path)
        
        # Slice the DataFrame according to the specified range
        if end_row is None:
            return df.iloc[start_row:]
        else:
            return df.iloc[start_row:end_row]
    except FileNotFoundError:
        print(f"Error: Could not find file at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process a range of tattoo descriptions from REPD dataset.')
    parser.add_argument('--start', type=int, default=12814, 
                        help='Starting row index (0-based)')
    parser.add_argument('--end', type=int, default=None, 
                        help='Ending row index (exclusive). If not specified, process until the end.')
    
    args = parser.parse_args()
    start_row = args.start
    end_row = args.end
    
    df = load_csv_file(start_row, end_row)
    if df is None:
        return
        
    print(f"Loaded DataFrame with shape: {df.shape}")
    print(f"Processing rows {start_row} to {end_row if end_row else 'end'}")
    
    if 'descripcion' not in df.columns:
        print("Error: 'descripcion' column not found in the DataFrame")
        return
    
    df = df[df['tipo_sena'] == 'TATUAJES']
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found in environment variables.")
        return
    
    unique_tattoos = set()
    
    for _, row in df.iterrows():
        id_persona = row['id_cedula_busqueda']
        tattoo_description = row['descripcion']
        if pd.isna(tattoo_description):
            continue
            
        if tattoo_description in unique_tattoos:
            print(f"Skipping duplicate tattoo description: {tattoo_description}")
            continue
        unique_tattoos.add(tattoo_description)
            
        prompt = f"""
        Eres un médico forense experto en tatuajes. Tu tarea es categorizar los siguientes tatuajes en un arreglo de Python. Para cada tatuaje, crea un registro y proporciona una descripción clara y concisa que incluya su ubicación, texto extraído, categorías y palabras clave.

        Instrucciones:
        1. Asegúrate de que cada tatuaje se describa solo una vez. No repitas tatuajes.
        2. Devuelve un arreglo JSON válido y completo.
        3. Si hay múltiples tatuajes, crea un registro separado para cada uno.

        Tatuajes:
        {tattoo_description}

        Formato de salida:
        [
            {{
                "id_persona": "{id_persona}",
                "descripcion_original": "{tattoo_description}",
                "descripcion_tattoo": "Descripción del tatuaje individual",
                "ubicacion": "Ubicación del tatuaje",
                "texto_extraido": "Texto extraído del tatuaje individual",
                "categorias": "Categorías del tatuaje individual",
                "palabras_clave": "Palabras clave del tatuaje individual, separadas por coma",
                "diseño": "Diseño específico del tatuaje individual"
            }}
        ]
        """
        
        response = generate_with_deepseek_api(prompt, api_key)
        
        if response:
            print(f"Raw Response: {response}")
            
            try:
                cleaned_response = clean_response(response)
                print(f"Cleaned Response: {cleaned_response}")
                
                tattoo_array = json.loads(cleaned_response)
                print("Parsed Array:", tattoo_array)
                
                result_df = pd.DataFrame(tattoo_array)
                result_df.drop_duplicates(inplace=True)
                
                save_results(result_df, 'llm_tatuajes_procesados_REPD.csv')
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse response as JSON: {e}")
        else:
            print("Failed to generate response.")
        print("-" * 80)

if __name__ == "__main__":
    main()