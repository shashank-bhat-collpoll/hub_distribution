#!/usr/bin/env python3

import os
import csv
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import base64

def check_dependencies() -> None:
    """Check if required Python packages are installed."""
    try:
        import requests
    except ImportError:
        print("Installing required dependency: requests")
        os.system("pip install requests")

def create_output_directory() -> str:
    """Create output directory with timestamp."""
    output_dir = "generated"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    return output_dir

def get_credentials() -> Tuple[str, str, str, str]:
    """Get credentials and date range from user."""
    prometheus_username = input("Enter Prometheus username(Refer parameter store): ")
    prometheus_password = input("Enter Prometheus password(Refer parameter store): ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    return prometheus_username, prometheus_password, start_date, end_date

def fetch_prometheus_data(username: str, password: str, date: str) -> Dict:
    """Fetch data from Prometheus API for a specific date."""
    url = "https://prometheus.digiicampus.com/api/v1/query"
    query = "round(sum by (host) (increase(http_nginx_requests_total[24h])))"
    time = f"{date}T00:00:00Z"
    
    try:
        # Create Basic Auth header
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            url,
            headers=headers,
            params={"query": query, "time": time},
            verify=True,
            timeout=300
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Print response status and content for debugging
        print(f"API Response Status: {response.status_code}")
        
        # Try to parse JSON response
        try:
            data = response.json()
            return data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            print(f"Response content: {response.text[:200]}...")  # Print first 200 chars of response
            return {"data": {"result": []}}  # Return empty result on error
            
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Prometheus API: {e}")
        return {"data": {"result": []}}  # Return empty result on error

def process_hub_group_list(file_path: str) -> List[Tuple[str, str, str]]:
    """Process hub_group_list.csv and extract relevant information."""
    processed_data = []
    
    with open(file_path, 'r') as f:
        for line in f:
            # Split by comma and strip whitespace
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 2:
                path = parts[0]
                domain = parts[1]
                
                # Split path into components
                path_parts = path.split('/')
                
                # Extract tenant name (last part of path)
                tenant_name = path_parts[-1].upper()
                
                # Find the database group by looking for the component after 'hub-'
                for i, part in enumerate(path_parts):
                    if part.startswith('hub-'):
                        # Extract db group from the hub- component
                        hub_parts = part.split('-')
                        if len(hub_parts) >= 4:  # hub-ap-south-1-db10
                            db_group = hub_parts[-1]  # Get db10
                            processed_data.append((tenant_name, db_group, domain))
                            break
    
    return processed_data

def calculate_weights(counts: Dict[str, float]) -> Dict[str, int]:
    """Calculate weights based on request counts."""
    return {host: int(count/1000 + 0.5) for host, count in counts.items()}

def main():
    # Check dependencies
    check_dependencies()
    
    # Create output directory
    output_dir = create_output_directory()
    
    # Check if hub_group_list.csv exists
    if not os.path.exists("hub_group_list.csv"):
        print("Error: hub_group_list.csv not found in the current directory")
        print("Please place hub_group_list.csv in the current directory and run the script again")
        return
    
    # Get credentials and date range
    username, password, start_date, end_date = get_credentials()
    
    # Convert dates to datetime objects
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Process data for each day
    all_counts = {}
    current_dt = start_dt
    
    while current_dt <= end_dt:
        current_date = current_dt.strftime("%Y-%m-%d")
        print(f"Processing data for {current_date}")
        
        # Fetch data from Prometheus
        data = fetch_prometheus_data(username, password, current_date)
        
        # Process results
        if 'data' in data and 'result' in data['data']:
            for result in data['data']['result']:
                host = result['metric']['host']
                count = int(float(result['value'][1]))  # Convert to int
                all_counts[host] = all_counts.get(host, 0) + count
        
        current_dt += timedelta(days=1)
    
    # Generate count.csv (aggregated daily counts)
    with open(os.path.join(output_dir, 'count.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        for host, count in all_counts.items():
            writer.writerow([host, int(count)])  # Ensure integer
    
    # Generate sorted_count.csv (sorted by count)
    sorted_counts = sorted(all_counts.items(), key=lambda x: x[1], reverse=True)
    with open(os.path.join(output_dir, 'sorted_count.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        for host, count in sorted_counts:
            writer.writerow([host, int(count)])  # Ensure integer
    
    # Generate ranked.csv (ranked data with count and weight)
    with open(os.path.join(output_dir, 'ranked.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        for host, count in sorted_counts:
            count_int = int(count)  # Ensure integer
            weight = int(count_int/1000 + 0.5)  # Calculate weight (divide by 1000 and round)
            writer.writerow([host, count_int, weight])
    
    # Process hub group list
    processed_hubs = process_hub_group_list("hub_group_list.csv")
    
    # Generate hub_group_processed.csv
    with open(os.path.join(output_dir, 'hub_group_processed.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        for tenant_name, db_group, domain in processed_hubs:
            writer.writerow([tenant_name, db_group, domain])
    
    # Generate merged_schema.csv
    with open(os.path.join(output_dir, 'merged_schema.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        for tenant_name, db_group, domain in processed_hubs:
            count = int(all_counts.get(domain, 0))  # Ensure integer
            weight = int(count/1000 + 0.5)
            writer.writerow([tenant_name, db_group, domain, count, weight])
    
    # Generate grouped_schema.csv
    db_rank_sums = {}
    for tenant_name, db_group, domain in processed_hubs:
        # Get the tenant's count and calculate weight
        tenant_count = int(all_counts.get(domain, 0))
        tenant_weight = int(tenant_count/1000 + 0.5)
        # Add the tenant's weight to its database group
        db_rank_sums[db_group] = db_rank_sums.get(db_group, 0) + tenant_weight
    
    with open(os.path.join(output_dir, 'grouped_schema.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        for db_group, total_weight in sorted(db_rank_sums.items(), key=lambda x: x[1], reverse=True):
            writer.writerow([db_group, int(total_weight)])
    
    # Generate db_requests.csv (total requests per database group)
    db_requests = {}
    for tenant_name, db_group, domain in processed_hubs:
        count = int(all_counts.get(domain, 0))  # Ensure integer
        db_requests[db_group] = db_requests.get(db_group, 0) + count
    
    with open(os.path.join(output_dir, 'db_requests.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        for db_group, total_requests in sorted(db_requests.items(), key=lambda x: x[1], reverse=True):
            writer.writerow([db_group, int(total_requests)])  # Ensure integer
    
    print("\nProcessing complete. Results are available in:", output_dir)
    print("- count.csv (aggregated daily counts)")
    print("- sorted_count.csv (sorted by count)")
    print("- ranked.csv (ranked data with count and rank)")
    print("- merged_schema.csv (merged schema with count and rank)")
    print("- grouped_schema.csv (grouped schema)")
    print("- db_requests.csv (total requests per database group)")

if __name__ == "__main__":
    main() 