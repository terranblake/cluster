#!/bin/bash
# gps_service.sh - Place in ~/.termux/boot/ to auto-start
# Single device GPS tracker - configure variables below

# ===== CONFIGURATION - EDIT THESE VALUES =====
USER_NAME="john"                    # Your name 
DEVICE_NAME="phone"                 # This device name
SERVER_HOST="your-server.com"       # SSH hostname or IP
SERVER_PATH="/logs/"                # Path on server for logs
INTERVAL=30                         # Seconds between GPS readings
SYNC_INTERVAL=300                   # Seconds between syncs to server
# ============================================

# Single device configuration
LOG_FILE="$HOME/gps_locations.log"
DEVICE_ID="${USER_NAME}_${DEVICE_NAME}"

# Function to log GPS data
log_gps() {
    local location=$(termux-location -p gps 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$location" ]; then
        local timestamp=$(date -Iseconds)
        local lat=$(echo "$location" | grep -o '"latitude":[^,]*' | cut -d':' -f2 | tr -d ' ')
        local lon=$(echo "$location" | grep -o '"longitude":[^,]*' | cut -d':' -f2 | tr -d ' ')
        local accuracy=$(echo "$location" | grep -o '"accuracy":[^,]*' | cut -d':' -f2 | tr -d ' ')
        
        if [ -n "$lat" ] && [ -n "$lon" ]; then
            echo "$timestamp,$DEVICE_ID,$lat,$lon,$accuracy" >> "$LOG_FILE"
            echo "$(date): GPS logged - $lat,$lon"
        fi
    else
        echo "$(date): Failed to get GPS location"
    fi
}

# Function to sync logs to server
sync_logs() {
    if [ -f "$LOG_FILE" ]; then
        rsync -av "$LOG_FILE" "$SERVER_HOST:$SERVER_PATH/" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "$(date): Logs synced successfully"
        else
            echo "$(date): Sync failed"
        fi
    fi
}

# Main loop
counter=0
echo "$(date): GPS service started for device: $DEVICE_ID"

while true; do
    log_gps
    
    # Sync every SYNC_INTERVAL seconds
    if [ $((counter % (SYNC_INTERVAL / INTERVAL))) -eq 0 ]; then
        sync_logs
    fi
    
    counter=$((counter + 1))
    sleep $INTERVAL
done