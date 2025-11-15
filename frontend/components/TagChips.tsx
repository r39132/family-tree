type Props = {
  tags: string[];
  onRemove: (tag: string) => void;
  onClearAll?: () => void;
  disabled?: boolean;
};

export default function TagChips({ tags, onRemove, onClearAll, disabled = false }: Props) {
  if (tags.length === 0) return null;

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        alignItems: 'center',
        padding: '10px 0',
      }}
    >
      <span style={{ fontSize: '14px', color: '#666', fontWeight: '500' }}>Active filters:</span>
      {tags.map((tag) => (
        <div
          key={tag}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            backgroundColor: '#e3f2fd',
            color: '#1976d2',
            borderRadius: '16px',
            fontSize: '14px',
            fontWeight: '500',
          }}
        >
          <span>#{tag}</span>
          <button
            onClick={() => onRemove(tag)}
            disabled={disabled}
            style={{
              background: 'none',
              border: 'none',
              color: '#1976d2',
              cursor: disabled ? 'not-allowed' : 'pointer',
              fontSize: '16px',
              padding: '0',
              display: 'flex',
              alignItems: 'center',
              opacity: disabled ? 0.5 : 1,
            }}
            aria-label={`Remove ${tag} filter`}
          >
            ×
          </button>
        </div>
      ))}
      {onClearAll && tags.length > 1 && (
        <button
          onClick={onClearAll}
          disabled={disabled}
          style={{
            padding: '6px 12px',
            backgroundColor: 'white',
            color: '#666',
            border: '1px solid #ddd',
            borderRadius: '16px',
            fontSize: '14px',
            cursor: disabled ? 'not-allowed' : 'pointer',
            fontWeight: '500',
            opacity: disabled ? 0.5 : 1,
          }}
        >
          Clear all
        </button>
      )}
    </div>
  );
}
