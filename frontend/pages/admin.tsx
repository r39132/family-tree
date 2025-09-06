import { useEffect, useState } from 'react';
import TopNav from '../components/TopNav';
import { API_BASE } from '../lib/api';
import AdminCacheManager from '../lib/adminCache';
import AdminCacheStatsDisplay from '../components/AdminCacheStatsDisplay';

interface UserItem {
  id: string;
  email?: string;
  first_login_at?: number;  // Now epoch seconds
  last_login_at?: number;   // Now epoch seconds
  login_count?: number;
  evicted_at?: number | null;  // Now epoch seconds
  is_admin?: boolean;
}

export default function AdminPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCacheStats, setShowCacheStats] = useState(false);

  // Helper function to format epoch seconds to local datetime
  const formatDateTime = (epochSeconds?: number) => {
    if (!epochSeconds) return '';
    const date = new Date(epochSeconds * 1000);
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  async function load() {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      if (!token) {
        window.location.href = '/login';
        return;
      }

      // Check cache first
      const cacheManager = AdminCacheManager.getInstance();
      const cachedUsers = cacheManager.getCachedUsers();
      if (cachedUsers) {
        setUsers(cachedUsers);
        setLoading(false);
        return;
      }

      // Verify current user is admin
      const meRes = await fetch(`${API_BASE}/auth/me`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (!meRes.ok) {
        if (meRes.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
        } else {
          window.location.href = '/';
        }
        return;
      }
      const me = await meRes.json();
      if (!Array.isArray(me.roles) || !me.roles.includes('admin')) {
        window.location.href = '/';
        return;
      }

      const res = await fetch(`${API_BASE}/admin/users`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.status === 403) {
        // not admin
        window.location.href = '/';
        return;
      }
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();

      // Cache the users data
      cacheManager.setCachedUsers(data.users || []);
      setUsers(data.users || []);
    } catch (e: any) {
      setError(e?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function act(path: string) {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      if (!token) return;
      const res = await fetch(`${API_BASE}${path}`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
      if (res.status === 403) {
        alert('You are not authorized');
        return;
      }
      if (!res.ok) throw new Error(`${res.status}`);

      // Invalidate cache after any admin action
      const cacheManager = AdminCacheManager.getInstance();
      cacheManager.invalidateAfterAdminAction();

      // Reload data
      await load();
    } catch (e: any) {
      alert(e?.message || 'Action failed');
    }
  }

  return (
    <div>
      <TopNav />
      <div className="container" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1>Admin</h1>
          <button
            onClick={() => setShowCacheStats(true)}
            style={{
              padding: '8px 16px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Cache Settings
          </button>
        </div>
        <h2>Users</h2>
        {loading && <div>Loading users…</div>}
        {error && <div style={{ color: 'red' }}>{error}</div>}
        {!loading && !error && (
          <div style={{ overflowX: 'auto', marginTop: '16px' }}>
            <table className="table" style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '14px',
              tableLayout: 'fixed'
            }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ textAlign: 'left', padding: '12px 8px', width: '12%' }}>ID</th>
                  <th style={{ textAlign: 'left', padding: '12px 8px', width: '20%' }}>Email</th>
                  <th style={{ textAlign: 'left', padding: '12px 8px', width: '12%' }}>First login</th>
                  <th style={{ textAlign: 'left', padding: '12px 8px', width: '12%' }}>Last login</th>
                  <th style={{ textAlign: 'left', padding: '12px 8px', width: '8%' }}>Login count</th>
                  <th style={{ textAlign: 'left', padding: '12px 8px', width: '6%' }}>Admin</th>
                  <th style={{ textAlign: 'left', padding: '12px 8px', width: '12%' }}>Evicted at</th>
                  <th style={{ textAlign: 'left', padding: '12px 8px', width: '18%' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '8px', fontWeight: '500', overflow: 'hidden', textOverflow: 'ellipsis' }}>{u.id}</td>
                    <td style={{ padding: '8px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{u.email || ''}</td>
                    <td style={{ padding: '8px', fontSize: '11px' }}>{formatDateTime(u.first_login_at)}</td>
                    <td style={{ padding: '8px', fontSize: '11px' }}>{formatDateTime(u.last_login_at)}</td>
                    <td style={{ padding: '8px', textAlign: 'center' }}>{u.login_count ?? 0}</td>
                    <td style={{ padding: '8px', textAlign: 'center' }}>{u.is_admin ? '✅' : ''}</td>
                    <td style={{ padding: '8px', fontSize: '11px' }}>{formatDateTime(u.evicted_at || undefined)}</td>
                    <td style={{ padding: '8px', whiteSpace: 'nowrap' }}>
                      {!u.evicted_at ? (
                        <button
                          className="btn"
                          style={{
                            marginRight: '4px',
                            padding: '4px 8px',
                            fontSize: '11px',
                            backgroundColor: '#dc3545',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                          onClick={() => act(`/admin/users/${u.id}/evict`)}
                        >
                          Evict
                        </button>
                      ) : (
                        <button
                          className="btn"
                          style={{
                            marginRight: '4px',
                            padding: '4px 8px',
                            fontSize: '11px',
                            backgroundColor: '#17a2b8',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                          onClick={() => act(`/admin/users/${u.id}/unevict`)}
                        >
                          Unevict
                        </button>
                      )}
                      {!u.is_admin ? (
                        <button
                          className="btn"
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                          onClick={() => act(`/admin/users/${u.id}/promote`)}
                        >
                          Promote
                        </button>
                      ) : (
                        <button
                          className="btn"
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            backgroundColor: '#ffc107',
                            color: 'black',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                          onClick={() => act(`/admin/users/${u.id}/demote`)}
                        >
                          Demote
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Cache Settings Modal */}
      {showCacheStats && (
        <AdminCacheStatsDisplay
          show={showCacheStats}
          onClose={() => setShowCacheStats(false)}
        />
      )}
    </div>
  );
}
