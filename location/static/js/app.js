// GPS Tracker Application
class GPSTracker {
    constructor() {
        this.map = null;
        this.markers = {};
        this.polylines = {};
        this.deviceColors = {};
        this.showPaths = true;
        this.colorPalette = [
            '#e74c3c', '#3498db', '#2ecc71', '#f39c12', 
            '#9b59b6', '#1abc9c', '#e67e22', '#34495e'
        ];
        this.colorIndex = 0;
        
        this.initMap();
        this.loadLocations();
        this.startAutoRefresh();
    }
    
    initMap() {
        // Initialize map centered on US
        this.map = L.map('map').setView([39.8283, -98.5795], 4);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(this.map);
    }
    
    getDeviceColor(deviceId) {
        if (!this.deviceColors[deviceId]) {
            this.deviceColors[deviceId] = this.colorPalette[this.colorIndex % this.colorPalette.length];
            this.colorIndex++;
        }
        return this.deviceColors[deviceId];
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }
    
    formatAccuracy(accuracy) {
        if (accuracy < 1000) {
            return `${Math.round(accuracy)}m`;
        } else {
            return `${(accuracy / 1000).toFixed(1)}km`;
        }
    }
    
    updateStatus(message, type = 'info') {
        const statusEl = document.getElementById('status');
        statusEl.textContent = message;
        statusEl.className = `status ${type}`;
    }
    
    async loadLocations() {
        try {
            this.updateStatus('Loading locations...', 'loading');
            
            const response = await fetch('/api/locations');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.processLocations(data);
            
            this.updateStatus(`Loaded ${data.length} location points`, 'success');
        } catch (error) {
            console.error('Error loading locations:', error);
            this.updateStatus('Failed to load locations', 'error');
        }
    }
    
    processLocations(data) {
        // Clear existing markers and polylines
        this.clearMap();
        
        // Group locations by device
        const deviceLocations = {};
        data.forEach(loc => {
            if (!deviceLocations[loc.device_id]) {
                deviceLocations[loc.device_id] = [];
            }
            deviceLocations[loc.device_id].push(loc);
        });
        
        let bounds = L.latLngBounds();
        let hasLocations = false;
        
        // Process each device
        Object.keys(deviceLocations).forEach(deviceId => {
            const locations = deviceLocations[deviceId];
            if (locations.length === 0) return;
            
            const color = this.getDeviceColor(deviceId);
            
            // Create polyline for path if enabled and multiple points
            if (this.showPaths && locations.length > 1) {
                const latLngs = locations.map(loc => [loc.lat, loc.lon]);
                const polyline = L.polyline(latLngs, {
                    color: color,
                    weight: 3,
                    opacity: 0.6,
                    smoothFactor: 1
                }).addTo(this.map);
                this.polylines[deviceId] = polyline;
            }
            
            // Add marker for latest location
            const latest = locations[locations.length - 1];
            const marker = L.circleMarker([latest.lat, latest.lon], {
                color: '#ffffff',
                fillColor: color,
                fillOpacity: 0.9,
                radius: 8,
                weight: 2
            }).addTo(this.map);
            
            // Create popup content
            const popupContent = `
                <div class="popup-device-name">${deviceId}</div>
                <div class="popup-info">
                    <strong>Time:</strong> ${this.formatTime(latest.timestamp)}<br>
                    <strong>Accuracy:</strong> ${this.formatAccuracy(latest.accuracy)}<br>
                    <strong>Coordinates:</strong> ${latest.lat.toFixed(6)}, ${latest.lon.toFixed(6)}
                </div>
            `;
            marker.bindPopup(popupContent);
            
            this.markers[deviceId] = marker;
            bounds.extend([latest.lat, latest.lon]);
            hasLocations = true;
        });
        
        // Fit map to show all locations
        if (hasLocations) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
        
        // Update device list
        this.updateDeviceList(deviceLocations);
    }
    
    updateDeviceList(deviceLocations) {
        const deviceList = document.getElementById('device-list');
        deviceList.innerHTML = '';
        
        if (Object.keys(deviceLocations).length === 0) {
            deviceList.innerHTML = '<div style="color: #95a5a6; font-style: italic;">No devices found</div>';
            return;
        }
        
        Object.keys(deviceLocations).forEach(deviceId => {
            const locations = deviceLocations[deviceId];
            if (locations.length === 0) return;
            
            const latest = locations[locations.length - 1];
            const color = this.getDeviceColor(deviceId);
            
            const deviceDiv = document.createElement('div');
            deviceDiv.className = 'device-item';
            deviceDiv.style.borderLeftColor = color;
            
            deviceDiv.innerHTML = `
                <div class="device-name">${deviceId}</div>
                <div class="device-time">${this.formatTime(latest.timestamp)}</div>
                <div class="device-accuracy">±${this.formatAccuracy(latest.accuracy)}</div>
            `;
            
            deviceDiv.onclick = () => {
                this.focusDevice(deviceId, latest);
            };
            
            deviceList.appendChild(deviceDiv);
        });
    }
    
    focusDevice(deviceId, location) {
        this.map.setView([location.lat, location.lon], 15);
        if (this.markers[deviceId]) {
            this.markers[deviceId].openPopup();
        }
    }
    
    clearMap() {
        // Remove all markers
        Object.values(this.markers).forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = {};
        
        // Remove all polylines
        Object.values(this.polylines).forEach(polyline => {
            this.map.removeLayer(polyline);
        });
        this.polylines = {};
    }
    
    fitAllDevices() {
        const markerGroup = new L.featureGroup(Object.values(this.markers));
        if (Object.keys(this.markers).length > 0) {
            this.map.fitBounds(markerGroup.getBounds(), { padding: [50, 50] });
        }
    }
    
    togglePaths() {
        this.showPaths = !this.showPaths;
        this.loadLocations(); // Reload to apply path visibility
    }
    
    startAutoRefresh() {
        // Refresh every 30 seconds
        setInterval(() => {
            this.loadLocations();
        }, 30000);
    }
}

// Global functions for HTML event handlers
function refreshLocations() {
    if (window.gpsTracker) {
        window.gpsTracker.loadLocations();
    }
}

function fitAllDevices() {
    if (window.gpsTracker) {
        window.gpsTracker.fitAllDevices();
    }
}

function togglePaths() {
    if (window.gpsTracker) {
        window.gpsTracker.togglePaths();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.gpsTracker = new GPSTracker();
});