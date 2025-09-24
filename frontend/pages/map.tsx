import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import TopNav from '../components/TopNav';
import { api } from '../lib/api';
import LoadingOverlay from '../components/LoadingOverlay';

type Member = {
  id: string;
  first_name: string;
  last_name: string;
  residence_location?: string;
};

type MapPin = {
  id: string;
  firstName: string;
  fullName: string;
  address: string;
  lat: number;
  lng: number;
};

declare global {
  interface Window {
    google: any;
    initMap: () => void;
  }
}

export default function MapPage() {
  const router = useRouter();
  const { member: focusMemberId } = router.query as { member?: string };
  const [members, setMembers] = useState<Member[]>([]);
  const [mapPins, setMapPins] = useState<MapPin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [mapReady, setMapReady] = useState(false);
  const [mapConfig, setMapConfig] = useState({ enable_map: false, google_maps_api_key: '' });

  useEffect(() => {
    checkMapConfig();
  }, []);

  async function checkMapConfig() {
    try {
      const config = await api('/config');
      setMapConfig(config);

      if (!config.enable_map) {
        setError('Map feature is not enabled');
        setLoading(false);
        return;
      }

      if (!config.google_maps_api_key) {
        setError('Google Maps API key is not configured');
        setLoading(false);
        return;
      }

      await loadMembers();
    } catch (e: any) {
      setError(e?.message || 'Failed to load configuration');
      setLoading(false);
    }
  }

  async function loadMembers() {
    try {
      const data = await api('/tree');
      const membersWithLocation = (data.members || []).filter((m: Member) =>
        m.residence_location && m.residence_location.trim()
      );

      setMembers(membersWithLocation);
      await geocodeAddresses(membersWithLocation);
    } catch (e: any) {
      if (e?.message?.includes('401')) {
        router.push('/login');
        return;
      }
      setError(e?.message || 'Failed to load members');
    } finally {
      setLoading(false);
    }
  }

  async function geocodeAddresses(members: Member[]) {
    if (!window.google) {
      setError('Google Maps is not loaded');
      return;
    }

    const geocoder = new window.google.maps.Geocoder();
    const pins: MapPin[] = [];

    for (const member of members) {
      try {
        const result = await new Promise<any>((resolve, reject) => {
          geocoder.geocode(
            { address: member.residence_location },
            (results: any[], status: string) => {
              if (status === 'OK' && results && results.length > 0) {
                resolve(results[0]);
              } else {
                reject(new Error(`Geocoding failed for ${member.first_name}: ${status}`));
              }
            }
          );
        });

        const location = result.geometry.location;
        pins.push({
          id: member.id,
          firstName: member.first_name,
          fullName: `${member.first_name} ${member.last_name}`,
          address: member.residence_location || '',
          lat: location.lat(),
          lng: location.lng()
        });
      } catch (e) {
        console.warn(`Could not geocode address for ${member.first_name}:`, e);
      }
    }

    setMapPins(pins);
  }

  useEffect(() => {
    if (!mapConfig.enable_map || !mapConfig.google_maps_api_key) return;

    // Load Google Maps API
    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${mapConfig.google_maps_api_key}&callback=initMap`;
      script.async = true;
      script.defer = true;

      window.initMap = () => {
        setMapReady(true);
      };

      document.head.appendChild(script);
    } else {
      setMapReady(true);
    }
  }, [mapConfig.enable_map, mapConfig.google_maps_api_key]);

  useEffect(() => {
    if (!mapReady) return;

    initializeMap();
  }, [mapReady, mapPins]);

  function initializeMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement || !window.google) return;

    // Default center (San Francisco)
    const defaultCenter = { lat: 37.7749, lng: -122.4194 };
    let mapCenter = defaultCenter;
    let mapZoom = 10;

    // If we have pins, calculate bounds and center
    if (mapPins.length > 0) {
      const bounds = new window.google.maps.LatLngBounds();
      mapPins.forEach(pin => {
        bounds.extend(new window.google.maps.LatLng(pin.lat, pin.lng));
      });
      mapCenter = bounds.getCenter().toJSON();
    }

    const map = new window.google.maps.Map(mapElement, {
      zoom: mapZoom,
      center: mapCenter,
      mapTypeId: window.google.maps.MapTypeId.ROADMAP,
    });

    // Fit map to show all pins or focus on specific member
    const focusPin = focusMemberId ? mapPins.find(pin => pin.id === focusMemberId) : null;

    if (focusPin) {
      // Focus on specific member
      map.setCenter({ lat: focusPin.lat, lng: focusPin.lng });
      map.setZoom(15);
    } else if (mapPins.length > 1) {
      // Fit all pins
      const bounds = new window.google.maps.LatLngBounds();
      mapPins.forEach(pin => {
        bounds.extend(new window.google.maps.LatLng(pin.lat, pin.lng));
      });
      map.fitBounds(bounds);
    }

    // Create markers for each pin
    mapPins.forEach(pin => {
      const isFocused = pin.id === focusMemberId;

      const marker = new window.google.maps.Marker({
        position: { lat: pin.lat, lng: pin.lng },
        map: map,
        title: pin.firstName,
        optimized: false,
        icon: isFocused ? {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: '#ff4444',
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2
        } : undefined
      });

      // Create info window for hover
      const infoWindow = new window.google.maps.InfoWindow({
        content: `
          <div style="padding: 8px;">
            <h4 style="margin: 0 0 4px 0;">${pin.fullName}</h4>
            <p style="margin: 0; color: #666;">${pin.address}</p>
          </div>
        `
      });

      // Show info window on hover
      marker.addListener('mouseover', () => {
        infoWindow.open(map, marker);
      });

      marker.addListener('mouseout', () => {
        infoWindow.close();
      });

      // Show info window on click (for mobile)
      marker.addListener('click', () => {
        infoWindow.open(map, marker);
      });

      // Auto-open info window for focused member
      if (isFocused) {
        infoWindow.open(map, marker);
      }
    });
  }

  if (!mapConfig.enable_map) {
    return (
      <div>
        <TopNav />
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h2>Map Feature Not Available</h2>
          <p>The map feature is currently disabled. Please contact your administrator to enable it.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <TopNav />
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h2>Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <TopNav />
      <div style={{ padding: '20px' }}>
        <h1>Family Locations</h1>
        {!loading && mapPins.length === 0 ? (
          <p>No family members have residence locations set.</p>
        ) : !loading ? (
          <>
            <p>Showing {mapPins.length} family member{mapPins.length !== 1 ? 's' : ''} with known locations.</p>
            <div
              id="map"
              style={{
                width: '100%',
                height: '600px',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </>
        ) : null}
      </div>

      {/* Loading Overlay */}
      <LoadingOverlay
        isLoading={loading}
        message="Loading map and geocoding addresses..."
      />
    </div>
  );
}
