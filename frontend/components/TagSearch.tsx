import { useEffect, useState, useRef, useCallback } from 'react';

export type TagInfo = {
  tag: string;
  count: number;
};

type Props = {
  spaceId: string;
  apiBase: string;
  token: string;
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  disabled?: boolean;
};

export default function TagSearch({
  spaceId,
  apiBase,
  token,
  selectedTags,
  onTagsChange,
  disabled = false,
}: Props) {
  const [allTags, setAllTags] = useState<TagInfo[]>([]);
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch all tags on mount
  useEffect(() => {
    async function fetchTags() {
      try {
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
          setAllTags(data.tags || []);
        }
      } catch (e) {
        console.error('Failed to fetch tags:', e);
      }
    }

    if (spaceId && token) {
      fetchTags();
    }
  }, [spaceId, token, apiBase]);

  // Debounce query for search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.toLowerCase().trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Filter tags based on query and exclude already selected
  const filteredTags = allTags.filter((tag) => {
    const matchesQuery = !debouncedQuery || tag.tag.toLowerCase().includes(debouncedQuery);
    const notSelected = !selectedTags.includes(tag.tag);
    return matchesQuery && notSelected;
  }).slice(0, 10); // Limit to 10 suggestions

  // Reset highlight when filtered list changes
  useEffect(() => {
    setHighlightIndex(0);
  }, [debouncedQuery]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        !inputRef.current?.contains(e.target as Node) &&
        !dropdownRef.current?.contains(e.target as Node)
      ) {
        setShowDropdown(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectTag = useCallback(
    (tag: string) => {
      if (!selectedTags.includes(tag)) {
        onTagsChange([...selectedTags, tag]);
      }
      setQuery('');
      setShowDropdown(false);
      inputRef.current?.focus();
    },
    [selectedTags, onTagsChange]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown && (e.key === 'ArrowDown' || e.key === 'Enter')) {
      setShowDropdown(true);
      e.preventDefault();
      return;
    }

    if (!showDropdown) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIndex((i) => Math.min(i + 1, filteredTags.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredTags[highlightIndex]) {
        selectTag(filteredTags[highlightIndex].tag);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setShowDropdown(false);
      setQuery('');
    }
  };

  return (
    <div style={{ position: 'relative', flex: 1, minWidth: '250px' }}>
      <div style={{ position: 'relative' }}>
        <span
          style={{
            position: 'absolute',
            left: '10px',
            top: '50%',
            transform: 'translateY(-50%)',
            fontSize: '16px',
            color: '#666',
          }}
        >
          🔍
        </span>
        <input
          ref={inputRef}
          type="text"
          placeholder="Search tags..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowDropdown(true)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          style={{
            width: '100%',
            padding: '8px 8px 8px 36px',
            borderRadius: '4px',
            border: '1px solid #ccc',
            fontSize: '14px',
          }}
        />
      </div>

      {showDropdown && filteredTags.length > 0 && (
        <div
          ref={dropdownRef}
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            left: 0,
            right: 0,
            backgroundColor: 'white',
            border: '1px solid #ccc',
            borderRadius: '4px',
            maxHeight: '300px',
            overflowY: 'auto',
            zIndex: 1000,
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
          }}
        >
          {filteredTags.map((tag, index) => (
            <div
              key={tag.tag}
              onClick={() => selectTag(tag.tag)}
              onMouseEnter={() => setHighlightIndex(index)}
              style={{
                padding: '10px 12px',
                cursor: 'pointer',
                backgroundColor: index === highlightIndex ? '#f0f0f0' : 'white',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: index < filteredTags.length - 1 ? '1px solid #f0f0f0' : 'none',
              }}
            >
              <span style={{ fontSize: '14px' }}>#{tag.tag}</span>
              <span
                style={{
                  fontSize: '12px',
                  color: '#666',
                  backgroundColor: '#e8f5e9',
                  padding: '2px 8px',
                  borderRadius: '12px',
                }}
              >
                {tag.count}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
