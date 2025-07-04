# GPS Tracker Project

A complete GPS tracking solution with Termux logging, server-side processing, and Cloudflare tunnel integration.

## Project Structure

```
gps-tracker/
├── server.py                 # Main Flask application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container build instructions
├── k8s-manifests.yaml       # Kubernetes deployment configuration
├── static/
│   ├── html/
│   │   └── index.html       # Main web interface
│   ├── css/
│   │   └── style.css        # Styling
│   └── js/
│       └── app.js           # Frontend JavaScript
└── README.md               # This file
```

## Setup Instructions

### 1. Build and Push Docker Image

```bash
# Build the Docker image
docker build -t your-registry/gps-tracker:latest .

# Push to your registry
docker push your-registry/gps-tracker:latest
```

### 2. Prepare Cloudflare Tunnel

1. Create a Cloudflare tunnel:
   ```bash
   cloudflared tunnel create gps-tracker
   ```

2. Note the tunnel ID from the output

3. Create credentials file and copy to your tunnel auth PVC location

### 3. Configure Kubernetes Secrets

```bash
# Create the tunnel ID secret
kubectl create secret generic cloudflare-tunnel \
  --from-literal=tunnel-id="your-tunnel-id-here"

# If you want to include credentials in the secret:
kubectl create secret generic cloudflare-tunnel \
  --from-literal=tunnel-id="your-tunnel-id-here" \
  --from-file=credentials.json=/path/to/your/credentials.json
```

### 4. Deploy to Kubernetes

```bash
# Update the image reference in k8s-manifests.yaml
# Then deploy:
kubectl apply -f k8s-manifests.yaml
```

### 5. Set up Tunnel Authentication

Either:
- Mount your `credentials.json` file to the tunnel-auth PVC, or
- Include the credentials in the Kubernetes secret as shown above

### 6. Configure DNS

Point `location.terran.sh` to your Cloudflare tunnel in the Cloudflare dashboard.

## Features

- **Modern Web Interface**: Clean, responsive design with real-time updates
- **Multi-device Support**: Track multiple devices with color-coded paths
- **Auto-refresh**: Updates every 30 seconds
- **Interactive Map**: Click devices to focus, toggle paths, fit all devices
- **Cloudflare Tunnel**: Secure external access without exposing ports
- **Persistent Storage**: Logs stored on PVC for durability
- **Health Checks**: Built-in monitoring and health endpoints

## API Endpoints

- `GET /` - Main web interface
- `GET /api/locations` - All recent location data
- `GET /api/latest` - Latest location per device
- `GET /health` - Health check endpoint

## Environment Variables

- `PORT` - Server port (default: 8080)
- `LOG_DIR` - Directory for GPS logs (default: /logs)
- `MAX_AGE_HOURS` - Maximum age for displayed locations (default: 24)
- `TUNNEL_ID` - Cloudflare tunnel ID

## Log Format

CSV format: `timestamp,device_id,latitude,longitude,accuracy`

Example:
```
2025-07-01T12:00:00,phone-123,37.7749,-122.4194,10.5
```

## Termux Setup

Use the GPS service script from the first artifact to automatically log and sync GPS data from your Android device.

## Security Features

- Non-root container execution
- Security contexts and capability dropping
- Read-only tunnel authentication mounting
- Resource limits and health checks