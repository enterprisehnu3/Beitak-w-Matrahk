/**
 * Maps & Location Logic
 * Handles Leaflet map picker and coordinate extraction
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Map Picker (for create/edit pages)
    const mapPickerContainer = document.getElementById('map-picker');
    if (mapPickerContainer) {
        initMapPicker(mapPickerContainer);
    }

    // 2. Static View Map (for detail page)
    const staticMapContainer = document.getElementById('map');
    if (staticMapContainer) {
        initStaticMap(staticMapContainer);
    }
});

/**
 * Initializes the interactive map picker
 */
function initMapPicker(container) {
    const latData = container.getAttribute('data-lat');
    const lngData = container.getAttribute('data-lng');
    const hasInitial = container.getAttribute('data-has-initial') === 'true';

    const initialLat = parseFloat(latData || 30.0444);
    const initialLng = parseFloat(lngData || 31.2357);

    const map = L.map(container.id).setView([initialLat, initialLng], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    let marker;
    if (hasInitial) {
        marker = L.marker([initialLat, initialLng]).addTo(map);
    }

    function updateMarker(lat, lng) {
        lat = parseFloat(lat); 
        lng = parseFloat(lng);
        if (isNaN(lat) || isNaN(lng)) return;

        if (marker) marker.setLatLng([lat, lng]);
        else marker = L.marker([lat, lng]).addTo(map);
        
        map.setView([lat, lng], 15);
        
        const latInput = document.getElementById('lat-input');
        const lngInput = document.getElementById('lng-input');
        if (latInput) latInput.value = lat.toFixed(6);
        if (lngInput) lngInput.value = lng.toFixed(6);
    }

    map.on('click', function (e) {
        updateMarker(e.latlng.lat, e.latlng.lng);
    });

    // Google Maps Link Resolver
    const gmapsLink = document.getElementById('gmaps-link');
    if (gmapsLink) {
        gmapsLink.addEventListener('input', function () {
            const val = this.value.trim();
            if (!val) return;

            if (val.includes('maps.app.goo.gl') || val.includes('goo.gl/maps')) {
                gmapsLink.classList.add('animate-pulse', 'border-primary-500');
                fetch(`/api/resolve_map_link?url=${encodeURIComponent(val)}`)
                    .then(res => res.json())
                    .then(data => {
                        gmapsLink.classList.remove('animate-pulse', 'border-primary-500');
                        if (data.lat && data.lng) {
                            updateMarker(data.lat, data.lng);
                        }
                    })
                    .catch(err => {
                        gmapsLink.classList.remove('animate-pulse', 'border-primary-500');
                        console.error('Error resolving link:', err);
                    });
                return;
            }

            let match = val.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
            if (!match) match = val.match(/[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)/);
            if (match) updateMarker(match[1], match[2]);
        });
    }

    // Manual Input Listeners
    const latIn = document.getElementById('lat-input');
    const lngIn = document.getElementById('lng-input');
    if (latIn && lngIn) {
        const handler = () => {
            const lat = parseFloat(latIn.value);
            const lng = parseFloat(lngIn.value);
            if (!isNaN(lat) && !isNaN(lng)) updateMarker(lat, lng);
        };
        latIn.addEventListener('input', handler);
        lngIn.addEventListener('input', handler);
    }
}

/**
 * Initializes the static display map
 */
function initStaticMap(container) {
    const mapData = document.getElementById('map-data');
    if (!mapData) return;

    let lat = parseFloat(mapData.dataset.lat) || 30.0444;
    let lng = parseFloat(mapData.dataset.lng) || 31.2357;
    const city = mapData.dataset.city;
    const title = mapData.dataset.title;
    
    if (!mapData.dataset.lat) {
        const cityCoords = {
            'القاهرة': [30.0444, 31.2357], 'Cairo': [30.0444, 31.2357],
            'الإسكندرية': [31.2001, 29.9187], 'Alexandria': [31.2001, 29.9187],
            'الجيزة': [30.0131, 31.2089], 'Giza': [30.0131, 31.2089],
            'المنصورة': [31.0409, 31.3785], 'Mansoura': [31.0409, 31.3785]
        };
        if (cityCoords[city]) {
            lat = cityCoords[city][0];
            lng = cityCoords[city][1];
        }
    }

    const map = L.map(container.id, { scrollWheelZoom: false }).setView([lat, lng], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);
    L.marker([lat, lng]).addTo(map).bindPopup(title).openPopup();
}
