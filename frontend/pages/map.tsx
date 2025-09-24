import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import TopNav from '../components/TopNav';
import { api } from '../lib/api';
import LoadingOverlay from '../components/LoadingOverlay';

type Member = {
  id: string;
  first_name: string;
  last_name: string;
  birth_location?: string;
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

type LayerType = 'residence' | 'birth';

declare global {
  interface Window {
    google: any;
    initMap: () => void;
  }
}

export default function MapPage() {
  const router = useRouter();
  const {
    member: focusMemberId,
    layer: layerParam = 'residence',
    addr: addressParam
  } = router.query as {
    member?: string;
    layer?: LayerType;
    addr?: string;
  };

  const [members, setMembers] = useState<Member[]>([]);
  const [mapPins, setMapPins] = useState<MapPin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [mapReady, setMapReady] = useState(false);
  const [mapConfig, setMapConfig] = useState({ enable_map: false, google_maps_api_key: '' });
  const [currentLayer, setCurrentLayer] = useState<LayerType>(layerParam);
  const [geocodingCache, setGeocodingCache] = useState<Map<string, { lat: number; lng: number }>>(new Map());
  const [toastMessage, setToastMessage] = useState<string>('');

  useEffect(() => {
    checkMapConfig();
  }, []);

  // Update layer when URL param changes
  useEffect(() => {
    setCurrentLayer(layerParam);
  }, [layerParam]);

  // Handle layer switching
  function handleLayerChange(newLayer: LayerType) {
    setCurrentLayer(newLayer);

    // Update URL with new layer
    const newQuery: any = { ...router.query, layer: newLayer };
    if (!focusMemberId && !addressParam) {
      // Remove member and addr params when switching layers without specific focus
      delete newQuery.member;
      delete newQuery.addr;
    }

    router.push({
      pathname: '/map',
      query: newQuery,
    }, undefined, { shallow: true });
  }

  function showToast(message: string) {
    setToastMessage(message);
    setTimeout(() => setToastMessage(''), 5000);
  }

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
      const allMembers = data.members || [];
      setMembers(allMembers);
      await geocodeAddressesForLayer(allMembers, currentLayer);
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

  async function geocodeAddressesForLayer(members: Member[], layer: LayerType) {
    if (!window.google) {
      setError('Google Maps is not loaded');
      return;
    }

    const locationField = layer === 'birth' ? 'birth_location' : 'residence_location';
    const membersWithLocation = members.filter((m: Member) =>
      m[locationField] && m[locationField]!.trim()
    );

    const geocoder = new window.google.maps.Geocoder();
    const pins: MapPin[] = [];

    for (const member of membersWithLocation) {
      const address = member[locationField]!;
      const cacheKey = `${layer}-${member.id}`;

      try {
        let location;

        // Check cache first
        if (geocodingCache.has(cacheKey)) {
          const cached = geocodingCache.get(cacheKey)!;
          location = { lat: () => cached.lat, lng: () => cached.lng };
        } else {
          // Geocode the address
          const result = await new Promise<any>((resolve, reject) => {
            geocoder.geocode(
              { address: address },
              (results: any[], status: string) => {
                if (status === 'OK' && results && results.length > 0) {
                  resolve(results[0]);
                } else {
                  reject(new Error(`Geocoding failed for ${member.first_name}: ${status}`));
                }
              }
            );
          });

          location = result.geometry.location;

          // Cache the result
          const newCache = new Map(geocodingCache);
          newCache.set(cacheKey, { lat: location.lat(), lng: location.lng() });
          setGeocodingCache(newCache);
        }

        pins.push({
          id: member.id,
          firstName: member.first_name,
          fullName: `${member.first_name} ${member.last_name}`,
          address: address,
          lat: location.lat(),
          lng: location.lng()
        });
      } catch (e) {
        console.warn(`Could not geocode ${layer} address for ${member.first_name}:`, e);
      }
    }

    setMapPins(pins);
  }

  // Handle address geocoding from URL parameter
  async function geocodeAddressParam(address: string) {
    if (!window.google || !address) return null;

    const cacheKey = `addr-${address}`;

    try {
      let location;

      // Check cache first
      if (geocodingCache.has(cacheKey)) {
        const cached = geocodingCache.get(cacheKey)!;
        location = { lat: () => cached.lat, lng: () => cached.lng };
      } else {
        const geocoder = new window.google.maps.Geocoder();
        const result = await new Promise<any>((resolve, reject) => {
          geocoder.geocode(
            { address: decodeURIComponent(address) },
            (results: any[], status: string) => {
              if (status === 'OK' && results && results.length > 0) {
                resolve(results[0]);
              } else {
                reject(new Error(`Could not find location: ${status}`));
              }
            }
          );
        });

        location = result.geometry.location;

        // Cache the result
        const newCache = new Map(geocodingCache);
        newCache.set(cacheKey, { lat: location.lat(), lng: location.lng() });
        setGeocodingCache(newCache);
      }

      return {
        lat: location.lat(),
        lng: location.lng(),
        address: decodeURIComponent(address)
      };
    } catch (e) {
      showToast("We couldn't find that location.");
      return null;
    }
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
  }, [mapReady, mapPins, focusMemberId, addressParam]);

  // Reload data when layer changes
  useEffect(() => {
    if (members.length > 0 && mapReady) {
      geocodeAddressesForLayer(members, currentLayer);
    }
  }, [currentLayer, mapReady]);

  async function initializeMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement || !window.google) return;

    // Default center (San Francisco)
    const defaultCenter = { lat: 37.7749, lng: -122.4194 };
    let mapCenter = defaultCenter;
    let mapZoom = 10;

    const map = new window.google.maps.Map(mapElement, {
      zoom: mapZoom,
      center: mapCenter,
      mapTypeId: window.google.maps.MapTypeId.ROADMAP,
    });

    // Handle address parameter (from Add Member page)
    if (addressParam) {
      const addressLocation = await geocodeAddressParam(addressParam);
      if (addressLocation) {
        map.setCenter({ lat: addressLocation.lat, lng: addressLocation.lng });
        map.setZoom(15);

        // Create temporary marker for the address
        const tempMarker = new window.google.maps.Marker({
          position: { lat: addressLocation.lat, lng: addressLocation.lng },
          map: map,
          title: 'Location Preview',
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 10,
            fillColor: '#4285f4',
            fillOpacity: 0.8,
            strokeColor: '#ffffff',
            strokeWeight: 3
          }
        });

        const tempInfoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="padding: 8px;">
              <h4 style="margin: 0 0 4px 0;">Location Preview</h4>
              <p style="margin: 0; color: #666;">${addressLocation.address}</p>
            </div>
          `
        });

        tempInfoWindow.open(map, tempMarker);
      }
      return;
    }

    // Handle member focus or show all pins
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
    } else if (mapPins.length === 1) {
      // Center on single pin
      map.setCenter({ lat: mapPins[0].lat, lng: mapPins[0].lng });
      map.setZoom(12);
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

      // Create info window
      const infoWindow = new window.google.maps.InfoWindow({
        content: `
          <div style="padding: 8px;">
            <h4 style="margin: 0 0 4px 0;">${pin.fullName}</h4>
            <p style="margin: 0; color: #666;">
              ${currentLayer === 'birth' ? 'Born in' : 'Lives in'}: ${pin.address}
            </p>
            <a href="/view/${pin.id}" style="color: #1976d2; text-decoration: underline; font-size: 12px;">
              View Profile
            </a>
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1>Family Locations</h1>

          {/* Layer Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label htmlFor="layer-select" style={{ fontSize: '14px', fontWeight: 'bold' }}>
              Show:
            </label>
            <select
              id="layer-select"
              value={currentLayer}
              onChange={(e) => handleLayerChange(e.target.value as LayerType)}
              style={{
                padding: '8px 12px',
                borderRadius: '4px',
                border: '1px solid #ccc',
                fontSize: '14px',
                background: 'white'
              }}
              aria-label="Select location layer to display"
            >
              <option value="residence">Location of Residence</option>
              <option value="birth">Location of Birth</option>
            </select>
          </div>
        </div>

        {/* Content based on loading state */}
        {!loading && mapPins.length === 0 && !addressParam ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <p>
              {currentLayer === 'birth'
                ? "No family members have birth locations set."
                : "No family members have residence locations set."
              }
            </p>
            <p style={{ fontSize: '14px' }}>
              Add location information to member profiles to see them on the map.
            </p>
          </div>
        ) : !loading ? (
          <>
            {mapPins.length > 0 && (
              <p style={{ marginBottom: '16px', color: '#666' }}>
                Showing {mapPins.length} family member{mapPins.length !== 1 ? 's' : ''} with known{' '}
                {currentLayer === 'birth' ? 'birth' : 'residence'} locations.
              </p>
            )}
            {addressParam && (
              <p style={{ marginBottom: '16px', color: '#666' }}>
                Previewing location for: <strong>{decodeURIComponent(addressParam)}</strong>
              </p>
            )}
            {focusMemberId && mapPins.length > 0 && (
              <p style={{ marginBottom: '16px', color: '#1976d2' }}>
                <strong>Focused on:</strong>{' '}
                {mapPins.find(p => p.id === focusMemberId)?.fullName || 'Selected member'}
              </p>
            )}
            {focusMemberId && mapPins.length === 0 && !addressParam && (
              <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#fff3cd', borderRadius: '4px', marginBottom: '16px' }}>
                <p style={{ margin: 0, color: '#856404' }}>
                  This member doesn't have a {currentLayer === 'birth' ? 'birth' : 'residence'} location yet.
                </p>
              </div>
            )}
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

      {/* Toast notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          backgroundColor: '#f44336',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          zIndex: 1000
        }}>
          {toastMessage}
        </div>
      )}

      {/* Loading Overlay */}
      <LoadingOverlay
        isLoading={loading}
        message="Loading map and geocoding addresses..."
      />
    </div>
  );
}
