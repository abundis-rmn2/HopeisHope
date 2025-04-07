import spacy
from spacy.pipeline import EntityRuler
import pandas as pd
from spacy import displacy

# Sample dataset
data = [
    {
        "id_cedula_busqueda": "c1dff4a5-8203-533d-9475-e4ef97a1a4f0",
        "nombre_completo": "EFRAIN ARELLANO VELAZQUEZ",
        "descripcion_desaparicion": "REFIERE LA REPORTANTE QUE EL DÍA 30 DE OCTUBRE DEL 2024 APROXIMADAMENTE A LA 13:00 SU HERMANO SALIÓ DEL DOMICILIO UBICADO EN LA CALLE OTHÓN BLANCO #189 COLONIA NUEVA SANTA MARIA, SAN PEDRO TLAQUEPAQUE SIN MENCIONAR A DONDE SE DIRIGÍA, DESCONOCIENDO DESDE ESE MOMENTO DE SU PARADERO."
    },
    {
        "id_cedula_busqueda": "6f0ff12e-8466-56fd-a73b-11388065c415",
        "nombre_completo": "CAMILA KEILANI NIEVES GARCIA",
        "descripcion_desaparicion": "REFIERE LA REPORTANTE QUE EL DÍA 29 DE OCTUBRE DE 2024 A LAS 8AM SU HIJA SALIÓ DE SU DOMICILIO UBICADO EN CALLE JUAN JOSÉ SEGURA #4145, COLONIA MIRAVALLE EN TLAQUEPAQUE, MENCIONANDO QUE PEDIRÍA UN UBER PARA IRSE A LA ESCUELA, DESCONOCIENDO DESDE ESE MOMENTO SU PARADERO."
    }
]

# Convert the dataset into a pandas DataFrame
df = pd.DataFrame(data)

# Load the specified pre-trained Spanish model from SpaCy
nlp = spacy.load(r'venv/lib/python3.12/site-packages/es_core_news_sm/es_core_news_sm-3.8.0')

# Add EntityRuler to the pipeline
ruler = nlp.add_pipe('entity_ruler', before='ner')

# Define patterns for dates and addresses
patterns = [
    {"label": "DATE", "pattern": [
        {"LOWER": "día"}, {"IS_DIGIT": True},
        {"LOWER": "de"}, {"LOWER": {
            "IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
                   "noviembre", "diciembre"]}},
        {"LOWER": "del"}, {"IS_DIGIT": True}]},
    {"label": "TIME", "pattern": [{"LOWER": {"REGEX": "\\d{1,2}(:\\d{2})?(am|pm)?"}}]},
    {"label": "ADDRESS", "pattern": [
        {"LOWER": "calle"}, {"LOWER": {"REGEX": "\\w+"}}, {"LOWER": {"REGEX": "#\\d+"}}]},
    {"label": "COLONIA", "pattern": [
        {"LOWER": "colonia"}, {"LOWER": {"REGEX": "\\w+"}}]}
]

ruler.add_patterns(patterns)

# Process each disappearance description
for idx, row in df.iterrows():
    description = row['descripcion_desaparicion'].lower()  # Ensure uniform lowercase for pattern matching
    print(f"\nProcessing description for index {idx}:")
    print(f"Text: {description}")

    # Process the description through SpaCy NER pipeline
    print("Processing text with SpaCy...")
    try:
        doc = nlp(description)

        # Extract entities from the description
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        print(f"Extracted entities: {entities}")

        # Optionally, visualize the entities
        print("Rendering entity visualization...")
        displacy.render(doc, style="ent", jupyter=False)

        print("Finished processing this description.\n")
    except Exception as e:
        print(f"Error processing text: {e}")
