# Prometheus Hub Analysis Script

This script processes Prometheus metrics data to analyze and group hub information based on request counts.

## Prerequisites

- Python 3.6 or higher
- Required Python packages (install using requirements.txt)

## Process Flow

1. Generate hub_group_list.csv file
   - Installs required dependencies from requirements.txt
   - Runs fetch_hub_list.py to generate the hub group list

2. Hub weight calculation
   - Processes Prometheus metrics data for the last 24 hours
   - Calculates request counts for each hub

## Quick Start

### Generate hub_group_list.csv file

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the script to generate hub_group_list.csv:
```bash
python3 fetch_hub_list.py
```

### Hub weight calculation

Run the Python script:
```bash
python3 process_hubs.py
```
