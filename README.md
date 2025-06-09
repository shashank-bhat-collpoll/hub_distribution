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


## Script Execution

1. Place the `hub_group_list.csv` file in the script directory
2. Run the script:
```bash
chmod +x process_hubs.sh 
./process_hubs.sh
```

3. When prompted, provide:
   - Prometheus username (from parameter store)
   - Prometheus password (from parameter store)
   - Start date (YYYY-MM-DD)
   - End date (YYYY-MM-DD)
   - Total number of hubs

## Output Files

The script generates several output files:

1. `count_[DATE].csv`
   - Format: `host,count`
   - Contains daily request counts for each host

2. `count.csv`
   - Format: `host,total_count`
   - Aggregated daily counts for all hosts

3. `sorted_count.csv`
   - Format: `host,total_count`
   - Sorted version of count.csv by count in descending order

4. `ranked.csv`
   - Format: `host,rank`
   - Contains host rankings based on request counts

5. `hub_group_processed.csv`
   - Format: `HUB_NAME,db_number,hub_id`
   - Processed version of hub_group_list.csv

6. `merged_schema.csv`
   - Format: `HUB_NAME,db_number,hub_id,rank`
   - Combined data from ranked.csv and hub_group_processed.csv

7. `grouped_schema.csv`
   - Format: `db_number,total_rank`
   - Aggregated ranks by database number

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

To quickly get started, run these commands:

```bash
# Add execute permission to the script
chmod +x process_hubs.sh

# Run the script
./process_hubs.sh
```
