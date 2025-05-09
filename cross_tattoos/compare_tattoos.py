import pandas as pd

# Load the CSV files
pfsi_df = pd.read_csv('/home/abundis/PycharmProjects/HopeisHope/ds/csv/equi/llm_tatuajes_procesados_PFSI.csv')
repd_df = pd.read_csv('/home/abundis/PycharmProjects/HopeisHope/ds/csv/equi/llm_tatuajes_procesados_REPD.csv')
matches_df = pd.read_csv('/home/abundis/PycharmProjects/HopeisHope/csv/cross_examples/person_matches_name_age.csv').sample(30000)

# Function to compare locations
def compare_locations(pfsi_id, repd_id):
    pfsi_tattoos = pfsi_df[pfsi_df['id_persona'] == pfsi_id]

    # Skip if no tattoos found for PFSI ID
    if pfsi_tattoos.empty:
        print(f"No tattoos found for PFSI ID {pfsi_id}")
        print(f"PFSI tattoos: {pfsi_tattoos.to_string(index=False)}")
        return
    
    repd_tattoos = repd_df[repd_df['id_persona'] == repd_id]
    print(f"Comparing PFSI ID {pfsi_id} and REPD ID {repd_id}")
    input("Press Enter to continue...")
    
    print(f"PFSI tattoos: {pfsi_tattoos.to_string(index=False)}")
    print(f"REPD tattoos: {repd_tattoos.to_string(index=False)}")

    for _, pfsi_row in pfsi_tattoos.iterrows():
        for _, repd_row in repd_tattoos.iterrows():
            if pfsi_row['ubicacion'] == repd_row['ubicacion']:
                print(f"Match found: PFSI ID {pfsi_id} and REPD ID {repd_id} have a tattoo at {pfsi_row['ubicacion']}")

# Iterate through the matches and compare locations
for _, row in matches_df.iterrows():
    print(f"Caalling comparing functionusing Prev List -> {row}")
    compare_locations(row['body_id'], row['missing_id'])
