import csv
import networkx as nx
import os

def read_csv(filepath):
    with open(filepath, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def create_graph_from_tattoo_matches(tattoo_matches):
    """Create a graph only using tattoo matches data"""
    G = nx.Graph()
    
    # Print column names for debugging
    if tattoo_matches:
        print("Tattoo matches columns:", list(tattoo_matches[0].keys()))
    
    # Process each tattoo match
    for row in tattoo_matches:
        try:
            # Extract IDs
            pfsi_id = row['pfsi_id']
            repd_id = row['repd_id']
            
            # Add nodes if they don't exist yet
            if not G.has_node(f"pfsi_{pfsi_id}"):
                # Create node with available attributes from the row
                G.add_node(f"pfsi_{pfsi_id}", 
                           type='pfsi',
                           name=row.get('body_name', 'Unknown'),
                           age=row.get('body_age', 'Unknown'),
                           location=row.get('body_location', 'Unknown'),
                           description=row.get('pfsi_description', ''))
            if not G.has_node(f"repd_{repd_id}"):
                G.add_node(f"repd_{repd_id}", 
                           type='repd',
                           name=row.get('missing_name', 'Unknown'),
                           age=row.get('missing_age', 'Unknown'),
                           location=row.get('missing_location', 'Unknown'),
                           description=row.get('repd_description', ''))
            # Add edge with all available attributes
            edge_data = {
                'text_similarity': row.get('text_similarity', ''),
                'location_similarity': row.get('location_similarity', ''),
                'text_match': row.get('text_match', ''),
                'similarity': row.get('similarity', '')
            }
            
            G.add_edge(f"pfsi_{pfsi_id}", f"repd_{repd_id}", **edge_data)
            
            # Process PFSI locations (comma-separated)
            if 'pfsi_location' in row and row['pfsi_location']:
                pfsi_locations = [loc.strip() for loc in row['pfsi_location'].split(',')]
                for location in pfsi_locations:
                    if location:  # Skip empty locations
                        location_id = f"loc_{location.replace(' ', '_')}"
                        # Add location node if it doesn't exist
                        if not G.has_node(location_id):
                            G.add_node(location_id, type='location', name=location)
                        # Connect PFSI to location
                        G.add_edge(f"pfsi_{pfsi_id}", location_id, relationship='located_at')
            
            # Process REPD locations (comma-separated)
            if 'repd_location' in row and row['repd_location']:
                repd_locations = [loc.strip() for loc in row['repd_location'].split(',')]
                for location in repd_locations:
                    if location:  # Skip empty locations
                        location_id = f"loc_{location.replace(' ', '_')}"
                        # Add location node if it doesn't exist
                        if not G.has_node(location_id):
                            G.add_node(location_id, type='location', name=location)
                        # Connect REPD to location
                        G.add_edge(f"repd_{repd_id}", location_id, relationship='found_at')
            
        except KeyError as e:
            print(f"Error processing row: {e}")
            print(f"Row data: {row}")
            continue

    return G

def main():
    try:
        # Only read the tattoo matches file
        tattoo_matches = read_csv('/home/abundis/PycharmProjects/HopeisHope/csv/cross_examples/tattoo_matches_strict.csv')
        
        # Create graph using only the tattoo matches
        G = create_graph_from_tattoo_matches(tattoo_matches)
        
        # Print graph stats by node type
        location_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'location']
        pfsi_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'pfsi']
        repd_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'repd']
        
        print(f"Graph created with {G.number_of_nodes()} total nodes:")
        print(f"- {len(pfsi_nodes)} PFSI (missing person) nodes")
        print(f"- {len(repd_nodes)} REPD (unidentified body) nodes")
        print(f"- {len(location_nodes)} location nodes")
        print(f"- {G.number_of_edges()} total edges")
        
        # Create output directory if it doesn't exist
        output_dir = '/home/abundis/PycharmProjects/HopeisHope/output/'
        os.makedirs(output_dir, exist_ok=True)
        
        # Write graph to file
        output_file = os.path.join(output_dir, 'tattoo_matches.graphml')
        nx.write_graphml(G, output_file)
        print(f"Graph saved successfully to {output_file}")
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
