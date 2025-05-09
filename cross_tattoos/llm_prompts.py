from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# Load the tokenizer and model
model_name = "EleutherAI/gpt-neo-1.3B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,  # Use half-precision for faster inference
    device_map="auto"  # Automatically place layers on GPU/CPU
)

# Add this after loading the tokenizer
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Create a text generation pipeline
generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer
)

# Example tattoo description
tattoo_description = "ANTEBRAZO DERECHO, PIERNA DERECHA EN FORMA DE TRIANGULO"

# Improved prompt
prompt = f"""Eres un médico forense experto en tatuajes. Tu tarea es categorizar los siguientes tatuajes en un arreglo de Python. Para cada tatuaje, proporciona una descripción clara y concisa que incluya su ubicación y diseño.

Tatuajes:
{tattoo_description}

Formato de salida:
[
    {{
        "descripcion": "Descripción detallada del tatuaje",
        "ubicacion": "Parte del cuerpo donde se encuentra el tatuaje",
        "diseño": "Diseño específico del tatuaje"
    }}
]

Ejemplo de salida:
[
    {{
        "descripcion": "Tatuaje en forma de triángulo",
        "ubicacion": "Antebrazo derecho",
        "diseño": "Triángulo"
    }},
    {{
        "descripcion": "Tatuaje en forma de triángulo",
        "ubicacion": "Pierna derecha",
        "diseño": "Triángulo"
    }}
]

Por favor, sigue el formato de salida estrictamente y proporciona la información en español claro y preciso. No incluyas información adicional ni irrelevante."""

# Generate response
response = generator(
    prompt,
    max_new_tokens=250,  # Increase token limit for longer responses
    num_return_sequences=3,
    temperature=0.2,  # Control randomness
    top_p=0.2,  # Nucleus sampling
    pad_token_id=tokenizer.eos_token_id,  # Ensure padding token is used
    repetition_penalty=2.2 # Penalize repetition to avoid gibberish
)

# Print the response
print(response[0]['generated_text'])
