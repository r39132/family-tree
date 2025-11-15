import { useEffect, useState } from 'react';

export type TagInfo = {
  tag: string;
  count: number;
};

type Props = {
  spaceId: string;
  apiBase: string;
  token: string;
  onTagClick: (tag: string) => void;
  disabled?: boolean;
};

export default function PopularTags({ spaceId, apiBase, token, onTagClick, disabled = false }: Props) {
  const [popularTags, setPopularTags] = useState<TagInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPopularTags() {
      try {
        setLoading(true);
        const response = await fetch(
          `${apiBase}/spaces/${spaceId}/album/tags?sort_by=count`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        if (response.ok) {
          const data = await response.json();
          // Get top 10 most used tags
          setPopularTags((data.tags || []).slice(0, 10));
        }
      } catch (e) {
        console.error('Failed to fetch popular tags:', e);
      } finally {
        setLoading(false);
      }
    }

    if (spaceId && token) {
      fetchPopularTags();
    }
  }, [spaceId, token, apiBase]);

  if (loading) {
    return null;
  }

  if (popularTags.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        padding: '15px',
        backgroundColor: '#f9f9f9',
        borderRadius: '8px',
        marginBottom: '20px',
      }}
    >
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#333' }}>
        Popular Tags
      </h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {popularTags.map((tag) => (
          <button
            key={tag.tag}
            onClick={() => onTagClick(tag.tag)}
            disabled={disabled}
            style={{
              padding: '6px 12px',
              backgroundColor: 'white',
              color: '#2e7d32',
              border: '1px solid #2e7d32',
              borderRadius: '16px',
              fontSize: '14px',
              cursor: disabled ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              opacity: disabled ? 0.5 : 1,
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              if (!disabled) {
                e.currentTarget.style.backgroundColor = '#2e7d32';
                e.currentTarget.style.color = 'white';
              }
            }}
            onMouseLeave={(e) => {
              if (!disabled) {
                e.currentTarget.style.backgroundColor = 'white';
                e.currentTarget.style.color = '#2e7d32';
              }
            }}
          >
            <span>#{tag.tag}</span>
            <span
              style={{
                fontSize: '12px',
                opacity: 0.8,
              }}
            >
              ({tag.count})
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
