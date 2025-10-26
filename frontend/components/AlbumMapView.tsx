import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import Leaflet components to avoid SSR issues
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);

const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);

const Marker = dynamic(
  () => import('react-leaflet').then((mod) => mod.Marker),
  { ssr: false }
);

const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
);

type AlbumMapViewProps = {
  photos: any[];
  onPhotoClick: (photo: any, index: number) => void;
};

export default function AlbumMapView({ photos, onPhotoClick }: AlbumMapViewProps) {
  const [mounted, setMounted] = useState(false);
  const [leaflet, setLeaflet] = useState<any>(null);

  useEffect(() => {
    setMounted(true);
    // Load Leaflet CSS
    // @ts-ignore - CSS import for side effects
    import('leaflet/dist/leaflet.css');
    // Load Leaflet library for icon configuration
    import('leaflet').then((L) => {
      setLeaflet(L);
      // Fix default marker icon issue with Leaflet in Next.js
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      });
    });
  }, []);

  if (!mounted || !leaflet) {
    return (
      <div style={{
        width: '100%',
        height: '600px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#666'
      }}>
        Loading map...
      </div>
    );
  }

  const photosWithLocation = photos.filter(p => p.gps_latitude && p.gps_longitude);

  if (photosWithLocation.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '40px',
        color: '#666',
        fontSize: '18px'
      }}>
        No photos with location data
      </div>
    );
  }

  // Calculate center and bounds
  const latitudes = photosWithLocation.map(p => p.gps_latitude!);
  const longitudes = photosWithLocation.map(p => p.gps_longitude!);
  const centerLat = latitudes.reduce((a, b) => a + b, 0) / latitudes.length;
  const centerLng = longitudes.reduce((a, b) => a + b, 0) / longitudes.length;

  return (
    <div style={{ width: '100%', height: '600px', borderRadius: '8px', overflow: 'hidden' }}>
      <MapContainer
        center={[centerLat, centerLng]}
        zoom={10}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {photosWithLocation.map((photo, index) => (
          <Marker
            key={photo.id}
            position={[photo.gps_latitude!, photo.gps_longitude!]}
          >
            <Popup>
              <div
                onClick={() => onPhotoClick(photo, photos.indexOf(photo))}
                style={{ cursor: 'pointer', maxWidth: '200px' }}
              >
                <img
                  src={photo.thumbnail_cdn_url}
                  alt={photo.filename}
                  style={{
                    width: '100%',
                    height: '150px',
                    objectFit: 'cover',
                    borderRadius: '4px',
                    marginBottom: '8px'
                  }}
                />
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>
                  {photo.filename}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  By {photo.uploader_id} • ❤️ {photo.like_count}
                </div>
                {photo.tags.length > 0 && (
                  <div style={{ fontSize: '11px', color: '#2e7d32', marginTop: '4px' }}>
                    {photo.tags.slice(0, 2).map((tag: string) => `#${tag}`).join(' ')}
                  </div>
                )}
                <div style={{
                  marginTop: '8px',
                  fontSize: '12px',
                  color: '#1976d2',
                  textAlign: 'center'
                }}>
                  Click to view full size
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
