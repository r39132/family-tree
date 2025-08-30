/**
 * Tree Cache Manager
 * Handles caching of tree data with smart invalidation
 */

type CacheConfig = {
  ttl: number; // Time to live in milliseconds
  enabled: boolean;
};

type TreeCacheData = {
  tree: any;
  timestamp: number;
  version: string; // Hash of tree-relevant data for invalidation
};

type CacheInvalidationReason =
  | 'ttl_expired'
  | 'data_changed'
  | 'manual_clear'
  | 'structure_changed';

class TreeCacheManager {
  private static instance: TreeCacheManager;
  private cache: TreeCacheData | null = null;
  private config: CacheConfig = {
    ttl: 5 * 60 * 1000, // 5 minutes default
    enabled: true
  };

  private constructor() {
    // Load config from localStorage if available
    this.loadConfig();
  }

  static getInstance(): TreeCacheManager {
    if (!TreeCacheManager.instance) {
      TreeCacheManager.instance = new TreeCacheManager();
    }
    return TreeCacheManager.instance;
  }

  private loadConfig(): void {
    if (typeof window === 'undefined') return;

    const saved = localStorage.getItem('tree-cache-config');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        this.config = { ...this.config, ...parsed };
      } catch (e) {
        console.warn('Failed to parse tree cache config:', e);
      }
    }
  }

  setConfig(config: Partial<CacheConfig>): void {
    this.config = { ...this.config, ...config };
    if (typeof window !== 'undefined') {
      localStorage.setItem('tree-cache-config', JSON.stringify(this.config));
    }
  }

  getConfig(): CacheConfig {
    return { ...this.config };
  }

  /**
   * Generate a version hash from tree-relevant data
   * Only includes fields that are displayed in the tree view
   */
  private generateTreeVersion(tree: any): string {
    if (!tree || !tree.members) return '';

    // Extract only tree-relevant fields for version calculation
    const relevantData = tree.members.map((member: any) => ({
      id: member.id,
      first_name: member.first_name,
      last_name: member.last_name,
      dob: member.dob,
      is_deceased: member.is_deceased,
      spouse_id: member.spouse_id
    }));

    // Include relations and tree structure
    const structureData = {
      members: relevantData,
      relations: tree.relations || [],
      roots: tree.roots?.map((r: any) => r.member?.id) || []
    };

    // Simple hash function (in production, consider using a proper hash library)
    return btoa(JSON.stringify(structureData)).replace(/[^a-zA-Z0-9]/g, '');
  }

  /**
   * Check if current tree data should invalidate cache
   */
  private shouldInvalidate(newTree: any): { should: boolean; reason?: CacheInvalidationReason } {
    if (!this.cache) {
      return { should: false };
    }

    // Check TTL
    const now = Date.now();
    if (now - this.cache.timestamp > this.config.ttl) {
      return { should: true, reason: 'ttl_expired' };
    }

    // Check if tree-relevant data changed
    const newVersion = this.generateTreeVersion(newTree);
    if (newVersion !== this.cache.version) {
      return { should: true, reason: 'data_changed' };
    }

    return { should: false };
  }

  /**
   * Get cached tree data if valid
   */
  getCachedTree(): any | null {
    if (!this.config.enabled || !this.cache) {
      return null;
    }

    const { should, reason } = this.shouldInvalidate(this.cache.tree);
    if (should) {
      console.log(`Tree cache invalidated: ${reason}`);
      this.cache = null;
      return null;
    }

    console.log('Using cached tree data');
    return this.cache.tree;
  }

  /**
   * Cache tree data
   */
  setCachedTree(tree: any): void {
    if (!this.config.enabled) {
      return;
    }

    const version = this.generateTreeVersion(tree);
    this.cache = {
      tree,
      timestamp: Date.now(),
      version
    };

    console.log('Tree data cached with version:', version);
  }

  /**
   * Manually invalidate cache
   */
  invalidateCache(reason: CacheInvalidationReason = 'manual_clear'): void {
    if (this.cache) {
      console.log(`Tree cache manually invalidated: ${reason}`);
    }
    this.cache = null;
  }

  /**
   * Check if a member update should invalidate tree cache
   */
  shouldInvalidateForMemberUpdate(memberUpdate: any): boolean {
    // Fields that affect tree display
    const treeRelevantFields = [
      'first_name',
      'last_name',
      'dob',
      'is_deceased',
      'spouse_id'
    ];

    // Check if any tree-relevant field is being updated
    return treeRelevantFields.some(field =>
      memberUpdate.hasOwnProperty(field) && memberUpdate[field] !== undefined
    );
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
  } {
    return {
      cached: !!this.cache,
      age: this.cache ? Date.now() - this.cache.timestamp : undefined,
      ttl: this.config.ttl,
      enabled: this.config.enabled,
      version: this.cache?.version
    };
  }
}

export default TreeCacheManager;
