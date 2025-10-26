import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/router';
import TopNav from '../components/TopNav';
import { api } from '../lib/api';
import LoadingOverlay from '../components/LoadingOverlay';

type AlbumPhoto = {
  id: string;
  space_id: string;
  uploader_id: string;
  filename: string;
  cdn_url: string;
  thumbnail_cdn_url: string;
  upload_date: string;
  file_size: number;
  width: number;
  height: number;
  tags: string[];
  like_count: number;
  gps_latitude?: number;
  gps_longitude?: number;
};

type AlbumStats = {
  total_photos: number;
  total_likes: number;
  total_uploaders: number;
  recent_uploads: number;
};

type UserInfo = {
  username: string;
  current_space?: string;
};

type ViewMode = 'thumbnail' | 'standard' | 'map';

export default function AlbumPage() {
  const router = useRouter();
  const [photos, setPhotos] = useState<AlbumPhoto[]>([]);
  const [filteredPhotos, setFilteredPhotos] = useState<AlbumPhoto[]>([]);
  const [stats, setStats] = useState<AlbumStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  const [deleting, setDeleting] = useState(false);
  const [deleteProgress, setDeleteProgress] = useState({ current: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);

  // View mode
  const [viewMode, setViewMode] = useState<ViewMode>('thumbnail');

  // Selection mode
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedPhotos, setSelectedPhotos] = useState<Set<string>>(new Set());

  // Filters and sorting
  const [filterUploader, setFilterUploader] = useState('');
  const [filterTags, setFilterTags] = useState('');
  const [sortBy, setSortBy] = useState('upload_date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Lightbox
  const [selectedPhoto, setSelectedPhoto] = useState<AlbumPhoto | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState(0);
  const [newTags, setNewTags] = useState('');
  const [likedPhotos, setLikedPhotos] = useState<Set<string>>(new Set());

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadUserInfo();
  }, []);

  useEffect(() => {
    if (userInfo?.current_space) {
      // Load view preference from localStorage
      const savedView = localStorage.getItem(`album_view_${userInfo.current_space}`);
      if (savedView && ['thumbnail', 'standard', 'map'].includes(savedView)) {
        setViewMode(savedView as ViewMode);
      }
      loadPhotos();
      loadStats();
    }
  }, [userInfo, sortBy, sortOrder]);

  useEffect(() => {
    applyFilters();
  }, [photos, filterUploader, filterTags]);

  async function loadUserInfo() {
    try {
      const data = await api('/user/profile');
      setUserInfo(data);
    } catch (e: any) {
      if (e.message.includes('401')) {
        router.push('/login');
      }
    }
  }

  async function loadPhotos() {
    if (!userInfo?.current_space) return;

    try {
      setLoading(true);
      const params = new URLSearchParams({
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: '100'
      });

      const data = await api(`/spaces/${userInfo.current_space}/album/photos?${params}`);
      setPhotos(data);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load photos');
    } finally {
      setLoading(false);
    }
  }

  async function loadStats() {
    if (!userInfo?.current_space) return;

    try {
      const data = await api(`/spaces/${userInfo.current_space}/album/stats`);
      setStats(data);
    } catch (e: any) {
      console.error('Failed to load stats:', e);
    }
  }

  function applyFilters() {
    let filtered = [...photos];

    if (filterUploader) {
      filtered = filtered.filter(p => p.uploader_id === filterUploader);
    }

    if (filterTags) {
      const tagList = filterTags.split(',').map(t => t.trim().toLowerCase());
      filtered = filtered.filter(p =>
        p.tags.some(t => tagList.includes(t.toLowerCase()))
      );
    }

    setFilteredPhotos(filtered);
  }

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    if (!event.target.files || !userInfo?.current_space) return;

    const files = Array.from(event.target.files);
    const totalFiles = files.length;

    setUploading(true);
    setUploadProgress({ current: 0, total: totalFiles });

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080'}/spaces/${userInfo.current_space}/album/photos`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
          }
        );

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        successCount++;
      } catch (e: any) {
        console.error('Upload error:', e);
        failCount++;
      }

      // Update progress after each file
      setUploadProgress({ current: i + 1, total: totalFiles });
    }

    // Show completion briefly
    await new Promise(resolve => setTimeout(resolve, 500));

    setUploading(false);
    setUploadProgress({ current: 0, total: 0 });

    if (failCount > 0) {
      setError(`Uploaded ${successCount} photos. Failed: ${failCount}`);
    }

    loadPhotos();
    loadStats();

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  async function toggleLike(photoId: string) {
    if (!userInfo?.current_space) return;

    const isLiked = likedPhotos.has(photoId);

    try {
      if (isLiked) {
        await api(`/spaces/${userInfo.current_space}/album/photos/${photoId}/like`, {
          method: 'DELETE'
        });
        setLikedPhotos(prev => {
          const next = new Set(prev);
          next.delete(photoId);
          return next;
        });
      } else {
        await api(`/spaces/${userInfo.current_space}/album/photos/${photoId}/like`, {
          method: 'POST'
        });
        setLikedPhotos(prev => new Set(prev).add(photoId));
      }

      loadPhotos();
    } catch (e: any) {
      console.error('Like toggle error:', e);
    }
  }

  async function updateTags(photoId: string, tags: string[]) {
    if (!userInfo?.current_space) return;

    try {
      await api(`/spaces/${userInfo.current_space}/album/photos/${photoId}/tags`, {
        method: 'PUT',
        body: JSON.stringify({ tags })
      });

      loadPhotos();

      if (selectedPhoto?.id === photoId) {
        setSelectedPhoto({ ...selectedPhoto, tags });
      }
    } catch (e: any) {
      console.error('Tag update error:', e);
    }
  }

  function openLightbox(photo: AlbumPhoto, index: number) {
    setSelectedPhoto(photo);
    setLightboxIndex(index);
    setNewTags(photo.tags.join(', '));
  }

  function closeLightbox() {
    setSelectedPhoto(null);
  }

  function navigatePhoto(direction: 'prev' | 'next') {
    let newIndex = lightboxIndex;

    if (direction === 'prev') {
      newIndex = lightboxIndex > 0 ? lightboxIndex - 1 : filteredPhotos.length - 1;
    } else {
      newIndex = lightboxIndex < filteredPhotos.length - 1 ? lightboxIndex + 1 : 0;
    }

    setLightboxIndex(newIndex);
    setSelectedPhoto(filteredPhotos[newIndex]);
    setNewTags(filteredPhotos[newIndex].tags.join(', '));
  }

  function handleAddTags() {
    if (!selectedPhoto) return;

    const tags = newTags.split(',').map(t => t.trim()).filter(t => t);
    updateTags(selectedPhoto.id, tags);
  }

  async function deletePhoto(photoId: string) {
    if (!userInfo?.current_space) return;
    if (!confirm('Are you sure you want to delete this photo?')) return;

    try {
      setDeleting(true);
      setDeleteProgress({ current: 1, total: 1 });

      await api(`/spaces/${userInfo.current_space}/album/photos/${photoId}`, {
        method: 'DELETE'
      });

      closeLightbox();
      loadPhotos();
      loadStats();
    } catch (e: any) {
      console.error('Delete error:', e);
      setError(e.message || 'Failed to delete photo');
    } finally {
      setDeleting(false);
      setDeleteProgress({ current: 0, total: 0 });
    }
  }

  async function bulkDeletePhotos() {
    if (!userInfo?.current_space) return;
    if (selectedPhotos.size === 0) return;

    const count = selectedPhotos.size;
    if (!confirm(`Are you sure you want to delete ${count} photo${count > 1 ? 's' : ''}?`)) return;

    try {
      setDeleting(true);
      setDeleteProgress({ current: 0, total: count });

      const response = await api(
        `/spaces/${userInfo.current_space}/album/photos/bulk-delete`,
        {
          method: 'POST',
          body: JSON.stringify({ photo_ids: Array.from(selectedPhotos) })
        }
      );

      setDeleteProgress({ current: response.successful, total: count });

      if (response.successful > 0) {
        setSelectedPhotos(new Set());
        setSelectionMode(false);

        // Wait a bit to show completion before reloading
        await new Promise(resolve => setTimeout(resolve, 500));

        loadPhotos();
        loadStats();
      }

      if (response.failed > 0) {
        const errorMsg = response.errors.map((e: any) => e.error).join(', ');
        setError(`Deleted ${response.successful} photos. Failed: ${response.failed}. Errors: ${errorMsg}`);
      }
    } catch (e: any) {
      console.error('Bulk delete error:', e);
      setError(e.message || 'Failed to delete photos');
    } finally {
      setDeleting(false);
      setDeleteProgress({ current: 0, total: 0 });
    }
  }

  function togglePhotoSelection(photoId: string) {
    setSelectedPhotos(prev => {
      const next = new Set(prev);
      if (next.has(photoId)) {
        next.delete(photoId);
      } else {
        next.add(photoId);
      }
      return next;
    });
  }

  function selectAll() {
    setSelectedPhotos(new Set(filteredPhotos.map(p => p.id)));
  }

  function clearSelection() {
    setSelectedPhotos(new Set());
  }

  function cancelSelectionMode() {
    setSelectionMode(false);
    setSelectedPhotos(new Set());
  }

  function clearFilters() {
    setFilterUploader('');
    setFilterTags('');
  }

  function changeViewMode(mode: ViewMode) {
    setViewMode(mode);
    if (userInfo?.current_space) {
      localStorage.setItem(`album_view_${userInfo.current_space}`, mode);
    }
  }

  if (loading && photos.length === 0) {
    return (
      <>
        <TopNav />
        <LoadingOverlay isLoading={true} message="Loading album..." />
      </>
    );
  }

  return (
    <>
      <TopNav />

      {/* Upload Progress Overlay */}
      {uploading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            minWidth: '400px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
          }}>
            <h3 style={{ margin: '0 0 20px 0', textAlign: 'center' }}>
              Uploading Photos...
            </h3>
            <div style={{
              width: '100%',
              height: '30px',
              backgroundColor: '#e0e0e0',
              borderRadius: '15px',
              overflow: 'hidden',
              marginBottom: '15px'
            }}>
              <div style={{
                width: uploadProgress.total > 0
                  ? `${(uploadProgress.current / uploadProgress.total) * 100}%`
                  : '0%',
                height: '100%',
                backgroundColor: '#2e7d32',
                transition: 'width 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '14px',
                fontWeight: 'bold'
              }}>
                {uploadProgress.total > 0 &&
                  `${Math.round((uploadProgress.current / uploadProgress.total) * 100)}%`
                }
              </div>
            </div>
            <p style={{
              textAlign: 'center',
              margin: 0,
              color: '#666',
              fontSize: '14px'
            }}>
              {uploadProgress.current} of {uploadProgress.total} photos uploaded
            </p>
          </div>
        </div>
      )}

      {/* Deletion Progress Overlay */}
      {deleting && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            minWidth: '400px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
          }}>
            <h3 style={{ margin: '0 0 20px 0', textAlign: 'center' }}>
              Deleting Photos...
            </h3>
            <div style={{
              width: '100%',
              height: '30px',
              backgroundColor: '#e0e0e0',
              borderRadius: '15px',
              overflow: 'hidden',
              marginBottom: '15px'
            }}>
              <div style={{
                width: deleteProgress.total > 0
                  ? `${(deleteProgress.current / deleteProgress.total) * 100}%`
                  : '0%',
                height: '100%',
                backgroundColor: '#2e7d32',
                transition: 'width 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '14px',
                fontWeight: 'bold'
              }}>
                {deleteProgress.total > 0 &&
                  `${Math.round((deleteProgress.current / deleteProgress.total) * 100)}%`
                }
              </div>
            </div>
            <p style={{
              textAlign: 'center',
              margin: 0,
              color: '#666',
              fontSize: '14px'
            }}>
              {deleteProgress.current} of {deleteProgress.total} photos deleted
            </p>
          </div>
        </div>
      )}

      <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto', opacity: (deleting || uploading) ? 0.5 : 1, pointerEvents: (deleting || uploading) ? 'none' : 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', gap: '10px', flexWrap: 'wrap' }}>
          <h1 style={{ margin: 0 }}>📷 Family Album</h1>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {!selectionMode ? (
              <>
                <button
                  onClick={() => setSelectionMode(true)}
                  disabled={deleting || uploading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#666',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: (deleting || uploading) ? 'not-allowed' : 'pointer',
                    fontSize: '16px',
                    opacity: (deleting || uploading) ? 0.5 : 1
                  }}
                >
                  Select Photos
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading || deleting}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#2e7d32',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: (uploading || deleting) ? 'not-allowed' : 'pointer',
                    fontSize: '16px',
                    opacity: (uploading || deleting) ? 0.5 : 1
                  }}
                >
                  {uploading ? 'Uploading...' : '+ Upload Photos'}
                </button>
              </>
            ) : (
              <>
                <span style={{ fontSize: '14px', color: '#666' }}>
                  {selectedPhotos.size} selected
                </span>
                <button
                  onClick={selectAll}
                  disabled={deleting}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#1976d2',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: deleting ? 'not-allowed' : 'pointer',
                    fontSize: '16px',
                    opacity: deleting ? 0.5 : 1
                  }}
                >
                  Select All
                </button>
                <button
                  onClick={clearSelection}
                  disabled={selectedPhotos.size === 0 || deleting}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#666',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: (selectedPhotos.size === 0 || deleting) ? 'not-allowed' : 'pointer',
                    fontSize: '16px',
                    opacity: (selectedPhotos.size === 0 || deleting) ? 0.5 : 1
                  }}
                >
                  Clear
                </button>
                <button
                  onClick={bulkDeletePhotos}
                  disabled={selectedPhotos.size === 0 || deleting}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#c62828',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: (selectedPhotos.size === 0 || deleting) ? 'not-allowed' : 'pointer',
                    fontSize: '16px',
                    opacity: (selectedPhotos.size === 0 || deleting) ? 0.5 : 1
                  }}
                >
                  {deleting ? 'Deleting...' : `🗑️ Delete (${selectedPhotos.size})`}
                </button>
                <button
                  onClick={cancelSelectionMode}
                  disabled={deleting}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#fff',
                    color: '#333',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    cursor: deleting ? 'not-allowed' : 'pointer',
                    fontSize: '16px',
                    opacity: deleting ? 0.5 : 1
                  }}
                >
                  Cancel
                </button>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            multiple
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </div>

        {stats && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '15px',
            marginBottom: '20px',
            padding: '15px',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px'
          }}>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{stats.total_photos}</div>
              <div style={{ fontSize: '14px', color: '#666' }}>Total Photos</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{stats.total_likes}</div>
              <div style={{ fontSize: '14px', color: '#666' }}>Total Likes</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{stats.recent_uploads}</div>
              <div style={{ fontSize: '14px', color: '#666' }}>Recent (7 days)</div>
            </div>
          </div>
        )}

        {error && (
          <div style={{
            padding: '10px',
            backgroundColor: '#ffebee',
            color: '#c62828',
            borderRadius: '4px',
            marginBottom: '20px'
          }}>
            {error}
          </div>
        )}

        {/* Filters and Sorting */}
        <div style={{
          display: 'flex',
          gap: '10px',
          marginBottom: '20px',
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          {/* View Mode Toggle */}
          <div style={{ display: 'flex', gap: '5px', marginRight: '10px' }}>
            <button
              onClick={() => changeViewMode('thumbnail')}
              style={{
                padding: '8px 12px',
                backgroundColor: viewMode === 'thumbnail' ? '#2e7d32' : '#f5f5f5',
                color: viewMode === 'thumbnail' ? 'white' : '#333',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: viewMode === 'thumbnail' ? 'bold' : 'normal'
              }}
              title="Thumbnail View"
            >
              🔲 Thumbnail
            </button>
            <button
              onClick={() => changeViewMode('standard')}
              style={{
                padding: '8px 12px',
                backgroundColor: viewMode === 'standard' ? '#2e7d32' : '#f5f5f5',
                color: viewMode === 'standard' ? 'white' : '#333',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: viewMode === 'standard' ? 'bold' : 'normal'
              }}
              title="Standard View"
            >
              🖼️ Standard
            </button>
            <button
              onClick={() => changeViewMode('map')}
              style={{
                padding: '8px 12px',
                backgroundColor: viewMode === 'map' ? '#2e7d32' : '#f5f5f5',
                color: viewMode === 'map' ? 'white' : '#333',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: viewMode === 'map' ? 'bold' : 'normal'
              }}
              title="Map View"
            >
              🗺️ Map
            </button>
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
          >
            <option value="upload_date">Upload Date</option>
            <option value="likes">Likes</option>
            <option value="filename">Filename</option>
            <option value="uploader">Uploader</option>
          </select>

          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>

          <input
            type="text"
            placeholder="Filter by tags (comma-separated)"
            value={filterTags}
            onChange={(e) => setFilterTags(e.target.value)}
            style={{
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ccc',
              minWidth: '200px'
            }}
          />

          {(filterUploader || filterTags) && (
            <button
              onClick={clearFilters}
              style={{
                padding: '8px 12px',
                backgroundColor: '#666',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Clear Filters
            </button>
          )}
        </div>

        {/* Photo Grid */}
        {filteredPhotos.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#666',
            fontSize: '18px'
          }}>
            {photos.length === 0 ? 'No photos yet. Upload some to get started!' : 'No photos match your filters.'}
          </div>
        ) : viewMode === 'map' ? (
          // Map View
          (() => {
            const photosWithLocation = filteredPhotos.filter(p => p.gps_latitude && p.gps_longitude);
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
            return (
              <div style={{
                width: '100%',
                height: '600px',
                backgroundColor: '#f5f5f5',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#666',
                fontSize: '18px'
              }}>
                Map view will be implemented with {photosWithLocation.length} geo-tagged photo{photosWithLocation.length !== 1 ? 's' : ''}
                <br />
                (Requires mapping library integration)
              </div>
            );
          })()
        ) : viewMode === 'standard' ? (
          // Standard View - Larger images
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
            gap: '30px'
          }}>
            {filteredPhotos.map((photo, index) => (
              <div
                key={photo.id}
                onClick={() => selectionMode ? togglePhotoSelection(photo.id) : openLightbox(photo, index)}
                style={{
                  cursor: 'pointer',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  backgroundColor: '#fff',
                  position: 'relative',
                  border: selectionMode && selectedPhotos.has(photo.id) ? '4px solid #1976d2' : 'none'
                }}
                onMouseEnter={(e) => {
                  if (!selectionMode) {
                    e.currentTarget.style.transform = 'scale(1.02)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!selectionMode) {
                    e.currentTarget.style.transform = 'scale(1)';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                  }
                }}
              >
                {selectionMode && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '10px',
                      right: '10px',
                      width: '30px',
                      height: '30px',
                      borderRadius: '50%',
                      backgroundColor: selectedPhotos.has(photo.id) ? '#1976d2' : 'rgba(255,255,255,0.9)',
                      border: selectedPhotos.has(photo.id) ? 'none' : '2px solid #ccc',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '18px',
                      color: 'white',
                      zIndex: 10
                    }}
                  >
                    {selectedPhotos.has(photo.id) && '✓'}
                  </div>
                )}
                <img
                  src={photo.cdn_url}
                  alt={photo.filename}
                  style={{
                    width: '100%',
                    height: '400px',
                    objectFit: 'cover'
                  }}
                />
                <div style={{ padding: '15px' }}>
                  <div style={{
                    fontSize: '16px',
                    fontWeight: 'bold',
                    marginBottom: '8px',
                    color: '#333'
                  }}>
                    {photo.filename}
                  </div>
                  <div style={{
                    fontSize: '14px',
                    color: '#666',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px'
                  }}>
                    <span>By {photo.uploader_id}</span>
                    <span>❤️ {photo.like_count}</span>
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#999',
                    marginBottom: '8px'
                  }}>
                    {new Date(photo.upload_date).toLocaleDateString()} • {photo.width} × {photo.height}
                  </div>
                  {photo.tags.length > 0 && (
                    <div style={{
                      marginTop: '8px',
                      fontSize: '12px',
                      color: '#2e7d32'
                    }}>
                      {photo.tags.map(tag => `#${tag}`).join(' ')}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Thumbnail View (default)
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
            gap: '20px'
          }}>
            {filteredPhotos.map((photo, index) => (
              <div
                key={photo.id}
                onClick={() => selectionMode ? togglePhotoSelection(photo.id) : openLightbox(photo, index)}
                style={{
                  cursor: 'pointer',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  backgroundColor: '#fff',
                  position: 'relative',
                  border: selectionMode && selectedPhotos.has(photo.id) ? '4px solid #1976d2' : 'none'
                }}
                onMouseEnter={(e) => {
                  if (!selectionMode) {
                    e.currentTarget.style.transform = 'scale(1.02)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!selectionMode) {
                    e.currentTarget.style.transform = 'scale(1)';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                  }
                }}
              >
                {selectionMode && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '10px',
                      right: '10px',
                      width: '30px',
                      height: '30px',
                      borderRadius: '50%',
                      backgroundColor: selectedPhotos.has(photo.id) ? '#1976d2' : 'rgba(255,255,255,0.9)',
                      border: selectedPhotos.has(photo.id) ? 'none' : '2px solid #ccc',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '18px',
                      color: 'white',
                      zIndex: 10
                    }}
                  >
                    {selectedPhotos.has(photo.id) && '✓'}
                  </div>
                )}
                <img
                  src={photo.thumbnail_cdn_url}
                  alt={photo.filename}
                  style={{
                    width: '100%',
                    height: '250px',
                    objectFit: 'cover'
                  }}
                />
                <div style={{ padding: '12px' }}>
                  <div style={{
                    fontSize: '14px',
                    color: '#666',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span>By {photo.uploader_id}</span>
                    <span>❤️ {photo.like_count}</span>
                  </div>
                  {photo.tags.length > 0 && (
                    <div style={{
                      marginTop: '8px',
                      fontSize: '12px',
                      color: '#2e7d32'
                    }}>
                      {photo.tags.slice(0, 3).map(tag => `#${tag}`).join(' ')}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Lightbox */}
        {selectedPhoto && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.9)',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '20px'
            }}
            onClick={closeLightbox}
          >
            <div
              style={{
                maxWidth: '90%',
                maxHeight: '90%',
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: '#fff',
                borderRadius: '8px',
                overflow: 'hidden'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '15px',
                borderBottom: '1px solid #eee'
              }}>
                <h3 style={{ margin: 0 }}>{selectedPhoto.filename}</h3>
                <button
                  onClick={closeLightbox}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '24px',
                    cursor: 'pointer',
                    color: '#666'
                  }}
                >
                  ✕
                </button>
              </div>

              <div style={{
                position: 'relative',
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#000'
              }}>
                <button
                  onClick={() => navigatePhoto('prev')}
                  style={{
                    position: 'absolute',
                    left: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    padding: '10px 15px',
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    border: 'none',
                    borderRadius: '50%',
                    cursor: 'pointer',
                    fontSize: '20px'
                  }}
                >
                  ‹
                </button>

                <img
                  src={selectedPhoto.cdn_url}
                  alt={selectedPhoto.filename}
                  style={{
                    maxWidth: '100%',
                    maxHeight: '70vh',
                    objectFit: 'contain'
                  }}
                />

                <button
                  onClick={() => navigatePhoto('next')}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    padding: '10px 15px',
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    border: 'none',
                    borderRadius: '50%',
                    cursor: 'pointer',
                    fontSize: '20px'
                  }}
                >
                  ›
                </button>
              </div>

              <div style={{ padding: '15px', borderTop: '1px solid #eee' }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px'
                }}>
                  <span style={{ fontSize: '14px', color: '#666' }}>
                    Uploaded by {selectedPhoto.uploader_id} on {new Date(selectedPhoto.upload_date).toLocaleDateString()}
                  </span>
                  <button
                    onClick={() => toggleLike(selectedPhoto.id)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: likedPhotos.has(selectedPhoto.id) ? '#e57373' : '#fff',
                      color: likedPhotos.has(selectedPhoto.id) ? '#fff' : '#333',
                      border: '1px solid #ddd',
                      borderRadius: '20px',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    ❤️ {selectedPhoto.like_count}
                  </button>
                </div>

                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <input
                    type="text"
                    value={newTags}
                    onChange={(e) => setNewTags(e.target.value)}
                    placeholder="Add tags (comma-separated)"
                    style={{
                      flex: 1,
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid #ddd'
                    }}
                  />
                  <button
                    onClick={handleAddTags}
                    disabled={deleting}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#2e7d32',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: deleting ? 'not-allowed' : 'pointer',
                      opacity: deleting ? 0.5 : 1
                    }}
                  >
                    Update Tags
                  </button>
                  {selectedPhoto.uploader_id === userInfo?.username && (
                    <button
                      onClick={() => deletePhoto(selectedPhoto.id)}
                      disabled={deleting}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#c62828',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: deleting ? 'not-allowed' : 'pointer',
                        opacity: deleting ? 0.5 : 1
                      }}
                    >
                      {deleting ? 'Deleting...' : 'Delete'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
