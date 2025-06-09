# Prometheus Hub Analysis Script

This script processes Prometheus metrics data to analyze and group hub information based on request counts.

## Prerequisites

- Linux/Unix environment
- Required tools:
  - `awk`
  - `curl`
  - `jq`
  - `sudo` (for installing dependencies)

## Required Files

### 1. hub_group_list.csv
This file should be placed in the same directory as the script. The file format should be:
```
/prod/hub/hub-ap-south-1-db11/ashoka,ashoka.digiicampus.com
/prod/hub/hub-ap-south-1-bennett/bennett,bennett.digiicampus.com
```


## Process Flow

1. The script checks for required dependencies and installs them if missing
2. Fetches Prometheus metrics data for the specified date range
3. Processes the hub group list to extract relevant information
4. Calculates request counts and ranks for each hub
5. Generates various output files for analysis

## Notes

- The script requires internet access to fetch data from Prometheus
- Make sure you have the correct permissions to access the Prometheus API
- The script will automatically install missing dependencies if run with sudo privileges

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

```bash
# Add execute permission to the script
chmod +x process_hubs.sh

# Run the script
./process_hubs.sh
```
