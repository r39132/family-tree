import { useEffect, useState } from 'react';
import AdminCacheManager from '../lib/adminCache';

type AdminCacheStatsDisplayProps = {
  show: boolean;
  onClose: () => void;
};

export default function AdminCacheStatsDisplay({ show, onClose }: AdminCacheStatsDisplayProps) {
  const [config, setConfig] = useState({ ttl: 5 * 60 * 1000, enabled: true });
  const [stats, setStats] = useState<any>({});
  const [ttlMinutes, setTtlMinutes] = useState(5);

  useEffect(() => {
    if (show) {
      const cacheManager = AdminCacheManager.getInstance();
      setConfig(cacheManager.getConfig());
      setStats(cacheManager.getCacheStats());
      setTtlMinutes(Math.round(cacheManager.getConfig().ttl / (60 * 1000)));
    }
  }, [show]);

  function updateConfig() {
    const cacheManager = AdminCacheManager.getInstance();
    const newConfig = {
      ttl: ttlMinutes * 60 * 1000,
      enabled: config.enabled
    };
    cacheManager.setConfig(newConfig);
    setConfig(newConfig);
    setStats(cacheManager.getCacheStats());
  }

  function clearCache() {
    const cacheManager = AdminCacheManager.getInstance();
    cacheManager.invalidateCache('manual_clear');
    setStats(cacheManager.getCacheStats());
  }

  function formatAge(age?: number): string {
    if (!age) return 'N/A';
    const seconds = Math.floor(age / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  }

  if (!show) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Admin Cache Settings</h3>
          <button
            className="btn secondary"
            onClick={onClose}
            style={{ padding: '4px 8px', fontSize: '12px' }}
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div style={{ marginBottom: '16px' }}>
            <h4>Cache Status</h4>
            <div className="cache-stats">
              <div><strong>Enabled:</strong> {stats.enabled ? '✅ Yes' : '❌ No'}</div>
              <div><strong>Cached:</strong> {stats.cached ? '✅ Yes' : '❌ No'}</div>
              {stats.cached && (
                <>
                  <div><strong>Age:</strong> {formatAge(stats.age)}</div>
                  <div><strong>Users:</strong> {stats.userCount}</div>
                  <div><strong>Version:</strong> <code>{stats.version?.substring(0, 8)}...</code></div>
                </>
              )}
              <div><strong>TTL:</strong> {Math.round(stats.ttl / (60 * 1000))} minutes</div>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <h4>Configuration</h4>
            <div style={{ marginBottom: '12px' }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={config.enabled}
                  onChange={e => setConfig({ ...config, enabled: e.target.checked })}
                />
                Enable admin data caching
              </label>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label>
                Cache TTL (minutes):
                <input
                  type="number"
                  value={ttlMinutes}
                  onChange={e => setTtlMinutes(parseInt(e.target.value) || 1)}
                  min="1"
                  max="60"
                  className="input"
                  style={{ width: '80px', marginLeft: '8px' }}
                />
              </label>
            </div>
          </div>

          <div className="cache-actions">
            <button className="btn" onClick={updateConfig}>
              Apply Settings
            </button>
            <button className="btn secondary" onClick={clearCache} style={{ marginLeft: '8px' }}>
              Clear Cache
            </button>
          </div>

          <div style={{ marginTop: '16px', fontSize: '12px', color: '#666' }}>
            <p><strong>Cache invalidation triggers:</strong></p>
            <ul style={{ margin: '4px 0', paddingLeft: '16px' }}>
              <li>TTL expiration</li>
              <li>Admin actions (evict/unevict/promote/demote)</li>
              <li>User data changes (login counts, eviction status, admin roles)</li>
              <li>Manual cache clear</li>
            </ul>
            <p><em>Cache automatically refreshes after any admin action to ensure data consistency.</em></p>
          </div>
        </div>
      </div>
    </div>
  );
}
