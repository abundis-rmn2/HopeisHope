import pandas as pd
import os
from collections import Counter
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# Download required NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


def load_csv_file():
    # Get absolute path to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(script_dir, 'csv', 'equi')
    
    # Verify directory exists
    if not os.path.exists(csv_dir):
        print(f"Directory not found: {csv_dir}")
        return None
        
    try:
        # Load only pfsi file
        df = pd.read_csv(os.path.join(csv_dir, 'pfsi_v2_principal.csv'))
        return df
    
    except FileNotFoundError as e:
        print(f"Error: Could not find PFSI file in {csv_dir}")
        print(f"Detailed error: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None


# Load and verify
df = load_csv_file()
script_dir = os.path.dirname(os.path.abspath(__file__))
if df is not None:
    print(f"PFSI DataFrame shape: {df.shape}")
    print("\nFirst 10 rows of PFSI data:")
    print(df.head(10))

# Filter the DataFrame to exclude rows where 'Tatuajes' is 'No presenta' and remove rows with missing 'ID'
df = df[['ID', 'Tatuajes']][(df['Tatuajes'] != 'No presenta') & df['ID'].notna()]
print("\nFirst 20 rows of filtered PFSI data:")
print(df.head(20))

# Define keywords for categories
keywords = {
    "Figura Humana": ["rostro", "figura", "hombre", "mujer", "persona", "cuerpo"],
    "Letras-Números": ["letra", "números", "leyenda", "palabras", "texto"],
    "Simbolos": ["símbolo", "cruz", "rojo", "negro", "símbolos", "machete", "corazón", "estrella", "cruz", "infinito"],
    "Animales": ["tigre", "león", "zorro", "lobo", "perro", "gallo", "pez", "pájaro", "conejo"],
    "Religiosos": ["santa muerte", "cruz cristiana", "anj", "horus", "dios", "ángel", "santo", "religión"],
    "Otros": ["irreconocible", "indeterminado", "abstracto", "floral", "combinado", "fantasía", "demonio", "manga"]
}

# Create a bag of words
def create_bag_of_words(df):
    # Combine all tattoo descriptions into a single string
    text = ' '.join(df['Tatuajes'].astype(str).tolist())
    
    # Replace "." with space
    text = text.replace('.', ' ')
    
    # Remove any non-alphanumeric characters and split the string into words
    words = re.findall(r'\w+', text.lower())
    
    # Remove stop words
    stop_words = set(stopwords.words('spanish'))
    words = [w for w in words if not w in stop_words]
    
    # Count the frequency of each word
    word_counts = Counter(words)
    
    return word_counts

# Categorize words based on keywords
def categorize_words(word_counts, keywords):
    word_categories = {}
    for category, words in keywords.items():
        word_categories[category] = {}
        for word, count in word_counts.items():
            if word in words:
                word_categories[category][word] = count
    return word_categories

# Function to update keywords based on word counts
def update_keywords(word_counts, keywords, threshold=5):
    for word, count in word_counts.items():
        if count > threshold:
            # Check if the word already exists in any category
            found = False
            for category, word_list in keywords.items():
                if word in word_list:
                    found = True
                    break
            
            if not found:
                # Assign the word to the "Otros" category
                if "Otros" in keywords:
                    keywords["Otros"].append(word)
                else:
                    keywords["Otros"] = [word]
    return keywords

def categorize_tattoos(df):
    # Use the 'Tatuajes' column for categorization
    tattoo_descriptions = df['Tatuajes'].astype(str).tolist()

    # Define categories
    categories = list(keywords.keys())
    
    # Create a dictionary to store the categorized tattoos
    categorized_tattoos = {category: [] for category in categories}

    # Iterate through each tattoo description
    for description in tattoo_descriptions:
        # Tokenize the description
        words = word_tokenize(description.lower(), language='spanish')
        
        # Remove stop words
        stop_words = set(stopwords.words('spanish'))
        words = [w for w in words if not w in stop_words]
        
        # Categorize the tattoo based on keywords
        for category, category_keywords in keywords.items():
            if any(word in category_keywords for word in words):
                categorized_tattoos[category].append(description)
                break  # Assign to only one category

    return categorized_tattoos

# Create and print the bag of words
word_counts = create_bag_of_words(df)

# Update keywords
keywords = update_keywords(word_counts, keywords)

# Categorize the words
word_categories = categorize_words(word_counts, keywords)

# Save word counts to a text file
word_counts_file = os.path.join(script_dir, 'txt', 'word_counts.txt')
os.makedirs(os.path.dirname(word_counts_file), exist_ok=True)

with open(word_counts_file, 'w', encoding='utf-8') as f:
    f.write("Word Counts:\n")
    for word, count in word_counts.items():
        f.write(f"- {word}: {count}\n")

print(f"\nWord counts have been saved to {word_counts_file}")

# Save word categories to a text file
word_categories_file = os.path.join(script_dir, 'txt', 'word_categories.txt')
os.makedirs(os.path.dirname(word_categories_file), exist_ok=True)

with open(word_categories_file, 'w', encoding='utf-8') as f:
    f.write("Word Categories:\n")
    for category, words in word_categories.items():
        f.write(f"\nCategory: {category}\n")
        for word, count in words.items():
            f.write(f"- {word}: {count}\n")

print(f"\nWord categories have been saved to {word_categories_file}")

# Categorize the tattoos
categorized_tattoos = categorize_tattoos(df)

# Save categorized tattoos to a text file
output_file = os.path.join(script_dir, 'txt', 'cat_tattoos.txt')
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("Categorized Tattoos:\n")
    for category, tattoos in categorized_tattoos.items():
        f.write(f"\nCategory: {category}\n")
        for tattoo in tattoos:
            f.write(f"- {tattoo}\n")

print(f"\nCategorized tattoos have been saved to {output_file}")