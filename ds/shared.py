# deepseek_shared.py

import os
import json
import re
from openai import OpenAI

# Shared system prompt
SHARED_SYSTEM_PROMPT = {
    "role": "system",
    "content": "Eres un médico forense experto en tatuajes. Tu tarea es analizar descripciones de tatuajes y categorizarlos de manera consistente. Responde solo con un arreglo en formato Python, sin explicaciones adicionales."
}

def generate_with_deepseek_api(prompt, api_key):
    """Send a prompt to the DeepSeek API and return the generated response."""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                SHARED_SYSTEM_PROMPT,  # Use the shared system prompt
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
    # Remove markdown code blocks (```json or ```python)
    response = re.sub(r"```json|```python|```", "", response).strip()
    
    # Ensure the response is a valid JSON array
    if not response.startswith("[") or not response.endswith("]"):
        raise ValueError("Response is not a valid JSON array")
    
    return response

def save_results(result_df, output_filename):
    """Save the results to a CSV file."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv', 'equi')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    result_df.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
    print(f"Results saved to {output_path}")