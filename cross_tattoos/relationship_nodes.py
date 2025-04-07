import csv
#create the node files to visualize the tattoo matches
def read_tattoo_matches(file_path):
    pfsi_set = set()
    repd_set = set()

    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            pfsi_set.add(row['pfsi_id'])
            repd_set.add(row['repd_id'])

    return pfsi_set, repd_set

def filter_and_save(input_file, output_file, filter_set, key_column):
    with open(input_file, mode='r', encoding='utf-8') as infile, open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row[key_column] in filter_set:
                writer.writerow(row)

if __name__ == "__main__":
    file_path = './fromServer/tattoo_matches_all.csv'  # Updated file path
    pfsi_set, repd_set = read_tattoo_matches(file_path)

    print("PFSI Records:", pfsi_set)
    print("REPD Records:", repd_set)

    # Filter and save PFSI records
    filter_and_save('./fromServer/pfsi_v2_principal.csv', './fromServer/pfsi_tats.csv', pfsi_set, 'ID')  # Updated column name

    # Filter and save REPD records
    filter_and_save('./fromServer/repd_vp_cedulas_principal.csv', './fromServer/repd_principal_tats.csv', repd_set, 'id_cedula_busqueda')  # Updated column name
    filter_and_save('./fromServer/repd_vp_inferencia3.csv', './fromServer/repd_tats_inferencia.csv', repd_set, 'id_cedula_busqueda')  # Updated column name
