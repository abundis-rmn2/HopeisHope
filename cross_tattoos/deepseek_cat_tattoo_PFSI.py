import pandas as pd
import os
from openai import OpenAI
import json
import re
from dotenv import load_dotenv

def load_csv_file():
    """Load the pfsi_v2_principal CSV file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(script_dir, 'csv', 'equi')
    
    if not os.path.exists(csv_dir):
        print(f"Directory not found: {csv_dir}")
        return None
        
    try:
        file_path = os.path.join(csv_dir, 'pfsi_v2_principal.csv')
        return pd.read_csv(file_path).sample(100)
    except FileNotFoundError:
        print(f"Error: Could not find file at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    return None

def generate_with_deepseek_api(prompt, api_key):
    """Send a prompt to the DeepSeek API and return the generated response."""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres un médico forense experto en tatuajes. Responde solo con el arreglo en formato Python, sin explicaciones adicionales."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5000,
            temperature=0.7,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return None

def clean_response(response):
    """Clean the response to extract only the JSON array."""
    response = re.sub(r"```python|```", "", response).strip()
    if not response.startswith("[") or not response.endswith("]"):
        raise ValueError("Response is not a valid JSON array")
    return response

def main():
    df = load_csv_file()
    if df is None:
        return
        
    print(f"Loaded DataFrame with shape: {df.shape}")
    
    if 'Tatuajes' not in df.columns:
        print("Error: 'Tatuajes' column not found in the DataFrame")
        return
    
    df = df[df['Tatuajes'].notna()]
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found in environment variables.")
        return
    
    unique_tattoos = set()
    
    for _, row in df.iterrows():
        id_persona = row['ID']
        tattoo_description = row['Tatuajes']
        if pd.isna(tattoo_description):
            continue
            
        if tattoo_description in unique_tattoos:
            print(f"Skipping duplicate tattoo description: {tattoo_description}")
            continue
        unique_tattoos.add(tattoo_description)
            
        prompt = f"""Eres un médico forense experto en tatuajes. Tu tarea es categorizar los siguientes tatuajes en un arreglo de Python. Para cada tatuaje, crea un registro y proporciona una descripción clara y concisa que incluya su ubicación, texto extraído, categorías y palabras clave.

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
        "descripcion_original": "{row['Tatuajes']}",
        "descripcion_tattoo": "Descripción del tatuaje individual",
        "ubicacion": "Ubicación del tatuaje",
        "texto_extraido": "Texto extraído del tatuaje individual",
        "categorias": "Categorías del tatuaje individual",
        "palabras_clave": "Palabras clave del tatuaje individual, separadas por coma",
        "diseño": "Diseño específico del tatuaje individual"
    }}
]"""
        print(f"Prompt: {prompt}")
        
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
                
                output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv', 'equi')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, 'llm_tatuajes_procesados_PFSI.csv')
                result_df.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
                print(f"Results saved to {output_path}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse response as JSON: {e}")
        else:
            print("Failed to generate response.")
        print("-" * 80)

if __name__ == "__main__":
    main()
