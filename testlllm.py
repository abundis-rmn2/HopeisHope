from transformers import pipeline

# Replace with an open model without access restrictions
generator = pipeline('text-generation', model="facebook/opt-350m")

# Generate text
response = generator("Puedes revisar como se llama el presidente de México", 
                    max_length=200,
                    temperature=0.7)

print(response[0]['generated_text'])