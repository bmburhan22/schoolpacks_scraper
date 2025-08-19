import requests
import json
import csv
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def fetch_schools():
    url = "https://schoolpacks.co.nz/graphql"
    headers = { 
        "Authorization": f"Bearer {os.getenv('TOKEN')}", 
        "Content-Type": "application/json" 
    }

    all_schools = []
    cursor = None
    has_next_page = True
    query = open("school.graphql").read()

    while has_next_page:
        payload = {
            "query": query,
            "variables": {
                "cursor": cursor
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        products = data['data']['site']['category']['products']
        
        for edge in products['edges']:
            all_schools.append(edge['node'])
        
        page_info = products['pageInfo']
        has_next_page = page_info.get('hasNextPage', False)
        
        if products['edges']:
            cursor = products['edges'][-1]['cursor']
        
        print(f"Total schools: {len(all_schools)}")

    json.dump(all_schools, open("schools.json", "w"), indent=2)
    return all_schools

def fetch_school_pack(school_obj):
    school_path = school_obj.get('path', '')
    school_name = school_obj.get('name', 'Unknown School')
    url = f"https://schoolpacks.co.nz{school_path}"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find the React component with the data
    # open("soup.html", "w", encoding="utf-8").write(soup.prettify())
    react_component = soup.find('div', {'id': 'ReactProductComponent'})
    if react_component:
        pack_data = json.loads(json.loads(react_component.get('data-react-product-content')).get('description'))
    else:
        pack_data = json.loads( soup.find('div', {'id': 'tab-description'}).text)

    # Extract the required data
    extracted_data = []
    for section in pack_data.get('sections', []):
        year = section.get('title', '')
        for subject in section.get('subjects', []):
            subject_name = subject.get('title', '')
            pack_notes = subject.get('pack_notes', '')
            teacher = subject.get('teacher', '')
            classroom = subject.get('classroom', '')
            compulsory = subject.get('compulsory', False)
            
            for product in subject.get('products', []):
                extracted_data.append({
                    'school': school_name,
                    'school_path': school_path,
                    'year': year,
                    'subject': subject_name,
                    'pack_notes': pack_notes,
                    'teacher': teacher,
                    'classroom': classroom,
                    'compulsory': compulsory,
                    'product_name': product.get('key', ''),
                    'sku': product.get('sku', ''),
                    'product_type': product.get('type', ''),
                    'description': product.get('description', ''),
                    'variant': product.get('variant', ''),
                    'deduplicate': product.get('deduplicate', False),
                    'locked': product.get('locked', False),
                    'quantity': product.get('quantity', 0)
                })
    
    print(f"Extracted {len(extracted_data)} products from {school_name}")
    return extracted_data
        
def fetch_all_school_packs(schools):
    
    all_packs = []
    
    for school in schools:
        school_name = school.get('name', 'Unknown School')
        school_path = school.get('path', '')
        
        print(f"Fetching pack for: {school_name} {school_path}")
        
        pack_data = fetch_school_pack(school)
        if pack_data:
            all_packs.extend(pack_data)
            print(f"Added {len(pack_data)} products from {school_name}")
        else:
            print(f"No pack data found for {school_name}")
    
    # Save all accumulated data to JSON and CSV
    print(f"\nSaving {len(all_packs)} total products...")
    
    # Save to JSON
    json.dump(all_packs, open("all_school_packs.json", "w"), indent=2)
    
    # Save to CSV
    with open("all_school_packs.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ['school', 'school_path', 'year', 'subject', 'pack_notes', 'teacher', 'classroom', 'compulsory', 'product_name', 'sku', 'product_type', 'description', 'variant', 'deduplicate', 'locked', 'quantity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_packs:
            writer.writerow(row)
    
    print("Done! Saved to all_school_packs.json and all_school_packs.csv")
    return all_packs

if __name__ == "__main__":
    # schools = fetch_schools()
    schools = json.load(open("schools.json", encoding="utf-8"))
    fetch_all_school_packs(schools)