/**
 * Admin Cache Manager
 * Handles caching of admin users data with smart invalidation
 */

type CacheConfig = {
  ttl: number; // Time to live in milliseconds
  enabled: boolean;
};

type AdminCacheData = {
  users: any[];
  timestamp: number;
  version: string; // Hash of admin-relevant data for invalidation
};

type CacheInvalidationReason =
  | 'ttl_expired'
  | 'data_changed'
  | 'manual_clear'
  | 'admin_action';

class AdminCacheManager {
  private static instance: AdminCacheManager;
  private cache: AdminCacheData | null = null;
  private config: CacheConfig = {
    ttl: 5 * 60 * 1000, // 5 minutes default
    enabled: true
  };

  private constructor() {
    // Load config from localStorage if available
    this.loadConfig();
  }

  static getInstance(): AdminCacheManager {
    if (!AdminCacheManager.instance) {
      AdminCacheManager.instance = new AdminCacheManager();
    }
    return AdminCacheManager.instance;
  }

  private loadConfig(): void {
    if (typeof window === 'undefined') return;

    const saved = localStorage.getItem('admin-cache-config');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        this.config = { ...this.config, ...parsed };
      } catch (e) {
        console.warn('Failed to parse admin cache config:', e);
      }
    }
  }

  setConfig(config: Partial<CacheConfig>): void {
    this.config = { ...this.config, ...config };
    if (typeof window !== 'undefined') {
      localStorage.setItem('admin-cache-config', JSON.stringify(this.config));
    }
  }

  getConfig(): CacheConfig {
    return { ...this.config };
  }

  /**
   * Generate a version hash from admin-relevant data
   * Includes fields that are displayed in the admin view
   */
  private generateAdminVersion(users: any[]): string {
    if (!users || !Array.isArray(users)) return '';

    // Extract only admin-relevant fields for version calculation
    const relevantData = users.map((user: any) => ({
      id: user.id,
      email: user.email,
      first_login_at: user.first_login_at,
      last_login_at: user.last_login_at,
      login_count: user.login_count,
      evicted_at: user.evicted_at,
      is_admin: user.is_admin
    }));

    // Simple hash function (in production, consider using a proper hash library)
    return btoa(JSON.stringify(relevantData)).replace(/[^a-zA-Z0-9]/g, '');
  }

  /**
   * Check if current admin data should invalidate cache
   */
  private shouldInvalidate(newUsers: any[]): { should: boolean; reason?: CacheInvalidationReason } {
    if (!this.cache) {
      return { should: false };
    }

    // Check TTL
    const now = Date.now();
    if (now - this.cache.timestamp > this.config.ttl) {
      return { should: true, reason: 'ttl_expired' };
    }

    // Check if admin-relevant data changed
    const newVersion = this.generateAdminVersion(newUsers);
    if (newVersion !== this.cache.version) {
      return { should: true, reason: 'data_changed' };
    }

    return { should: false };
  }

  /**
   * Get cached admin data if valid
   */
  getCachedUsers(): any[] | null {
    if (!this.config.enabled || !this.cache) {
      return null;
    }

    const { should, reason } = this.shouldInvalidate(this.cache.users);
    if (should) {
      console.log(`Admin cache invalidated: ${reason}`);
      this.cache = null;
      return null;
    }

    console.log('Using cached admin data');
    return this.cache.users;
  }

  /**
   * Cache admin users data
   */
  setCachedUsers(users: any[]): void {
    if (!this.config.enabled) {
      return;
    }

    const version = this.generateAdminVersion(users);
    this.cache = {
      users,
      timestamp: Date.now(),
      version
    };

    console.log('Admin data cached with version:', version);
  }

  /**
   * Manually invalidate cache
   */
  invalidateCache(reason: CacheInvalidationReason = 'manual_clear'): void {
    if (this.cache) {
      console.log(`Admin cache manually invalidated: ${reason}`);
    }
    this.cache = null;
  }

  /**
   * Invalidate cache after admin actions (evict/unevict/promote/demote)
   */
  invalidateAfterAdminAction(): void {
    this.invalidateCache('admin_action');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    cached: boolean;
    age?: number;
    ttl: number;
    enabled: boolean;
    version?: string;
    userCount?: number;
  } {
    return {
      cached: !!this.cache,
      age: this.cache ? Date.now() - this.cache.timestamp : undefined,
      ttl: this.config.ttl,
      enabled: this.config.enabled,
      version: this.cache?.version,
      userCount: this.cache?.users?.length
    };
  }
}

export default AdminCacheManager;
