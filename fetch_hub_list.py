#!/usr/bin/env python3

import boto3
import csv
import os
import json
from botocore.exceptions import ClientError

def get_parameters_by_path(prefix):
    """
    Fetch all parameters that start with the given prefix
    """
    try:
        ssm = boto3.client('ssm')
        parameters = []
        paginator = ssm.get_paginator('get_parameters_by_path')
        
        for page in paginator.paginate(
            Path=prefix,
            Recursive=True,
            WithDecryption=True
        ):
            parameters.extend(page['Parameters'])
            
        return parameters
    except ClientError as e:
        print(f"Error fetching parameters: {e}")
        return []

def extract_cp_url(parameter_value):
    """
    Extract cpUrl from the parameter value
    """
    try:
        # First, clean up the string by removing extra quotes and spaces
        cleaned_value = parameter_value.strip().replace('""', '"')
        
        # If the string starts and ends with quotes, remove them
        if cleaned_value.startswith('"') and cleaned_value.endswith('"'):
            cleaned_value = cleaned_value[1:-1]
            
        # Parse the JSON string
        data = json.loads(cleaned_value)
        
        # If data is a string, try to parse it again
        if isinstance(data, str):
            data = json.loads(data)
            
        return data.get('cpUrl', '')
    except Exception as e:
        print(f"Error parsing parameter value: {e}")
        print(f"Raw value: {parameter_value}")
        return ''

def save_to_csv(data, output_file):
    """
    Save the data to a CSV file
    """
    try:
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
            for row in data:
                # Add space after comma by joining with ', '
                writer.writerow([row[0], ' ' + row[1]])
        print(f"Successfully saved data to {output_file}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    # Get all parameters starting with /prod/
    parameters = get_parameters_by_path('/prod/')
    
    # Filter parameters with exactly 4 slashes and extract cpUrl
    filtered_data = []
    for param in parameters:
        key = param['Name']
        if key.count('/') == 4:  # Check for exactly 4 slashes
            cp_url = extract_cp_url(param['Value'])
            if cp_url:  # Only add rows that have a cpUrl value
                filtered_data.append([key, cp_url])
    
    # Save to CSV
    output_file = 'hub_group_list.csv'
    save_to_csv(filtered_data, output_file)

if __name__ == "__main__":
    main() 