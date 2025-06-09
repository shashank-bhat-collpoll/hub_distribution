#!/bin/bash

# Check if required tools are installed
check_dependencies() {
    local missing_deps=()
    
    for cmd in awk curl jq; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "Installing missing dependencies: ${missing_deps[*]}"
        sudo apt-get update
        sudo apt-get install -y ${missing_deps[@]}
    fi
}

# Create output directory with timestamp
output_dir="generated"
mkdir -p "$output_dir"
echo "Created output directory: $output_dir"

# Check if hub_group_list.csv exists
if [ ! -f "hub_group_list.csv" ]; then
    echo "Error: hub_group_list.csv not found in the current directory"
    echo "Please place hub_group_list.csv in the current directory and run the script again"
    exit 1
fi

# Install dependencies
check_dependencies

# Get credentials and parameters from user
read -p "Enter Prometheus username(Refer parameter store): " prometheus_username
read -s -p "Enter Prometheus password(Refer parameter store): " prometheus_password
echo  # Add a newline after password input
read -p "Enter start date (YYYY-MM-DD): " start_date
read -p "Enter end date (YYYY-MM-DD): " end_date

# Convert dates to timestamps
start_timestamp=$(date -d "$start_date" +%s)
end_timestamp=$(date -d "$end_date" +%s)

# Process data for each day
current_timestamp=$start_timestamp
while [ $current_timestamp -le $end_timestamp ]; do
    current_date=$(date -d "@$current_timestamp" +%Y-%m-%d)
    echo "Processing data for $current_date"
    
    # Fetch count for current date
    curl -s -u "${prometheus_username}:${prometheus_password}" "https://prometheus.digiicampus.com/api/v1/query" \
        --data-urlencode "query=round(sum by (host) (increase(http_nginx_requests_total[24h])))" \
        --data-urlencode "time=${current_date}T00:00:00Z" | \
        jq -r '.data.result[] | [.metric.host, .value[1]] | join(",")' > "$output_dir/count_${current_date}.csv"
    
    # Move to next day
    current_timestamp=$((current_timestamp + 86400))
done

# Combine all daily counts into final count.csv
cat "$output_dir"/count_*.csv | awk -F',' '
{
    sum[$1] += $2
}
END {
    for (host in sum) {
        print host "," sum[host]
    }
}' | sort -t',' -k2,2nr > "$output_dir/count.csv"

echo "Processing daily counts complete. Starting schema processing..."

# Process hub_group_list.csv
awk -F '[,/ \t]+' '
{
  if ($4 ~ /ap-south-1/) {
    split($4, parts, "-");
    for (i = 1; i <= length(parts); i++) {
      if (parts[i] == "1") {
        db = parts[i+1];
        break;
      }
    }
    if (db != "" && $5 != "" && $6 != "") {
      print toupper($5) "," db "," $6;
    }
  }
}' hub_group_list.csv > "$output_dir/hub_group_processed.csv"

# Sort by count
sort -t, -k2,2nr "$output_dir/count.csv" > "$output_dir/sorted_count.csv"

# Generate ranked data with both count and rank
awk -F',' '
{
    # Keep original count
    count = $2
    # Calculate rank (divide count by 1000 and round to nearest integer)
    weight = int(count/1000 + 0.5)
    print $1 "," count "," weight
}' "$output_dir/sorted_count.csv" > "$output_dir/ranked.csv"

# Generate merged schema
awk -F ',' 'NR==FNR {count[$1] = $2; rank[$1] = $3; next} {c = (count[$3] ? count[$3] : 0); r = (rank[$3] ? rank[$3] : 0); print $1 "," $2 "," $3 "," c "," r}' \
    "$output_dir/ranked.csv" "$output_dir/hub_group_processed.csv" > "$output_dir/merged_schema.csv"

# Generate grouped schema
awk -F ',' '
{
    rank_sum[$2] += $5;
}
END {
    for (db in rank_sum) {
        print db "," rank_sum[db];
    }
}' "$output_dir/merged_schema.csv" | sort -t',' -k2,2nr > "$output_dir/grouped_schema.csv"

# Calculate total requests per database group
echo "Calculating total requests per database group..."
awk -F ',' '
{
    db = $2;
    count = $4;
    total_requests[db] += count;
}
END {
    for (db in total_requests) {
        print db "," total_requests[db];
    }
}' "$output_dir/merged_schema.csv" | sort -t',' -k2,2nr > "$output_dir/db_requests.csv"

echo "Processing complete. Results are available in: $output_dir"
echo "- count.csv (aggregated daily counts)"
echo "- sorted_count.csv (sorted by count)"
echo "- ranked.csv (ranked data with count and rank)"
echo "- merged_schema.csv (merged schema with count and rank)"
echo "- grouped_schema.csv (grouped schema)"
echo "- db_requests.csv (total requests per database group)" 