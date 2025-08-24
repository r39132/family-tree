import React, { useEffect, useId, useMemo, useRef, useState } from 'react';

export type Option = { value: string; label: string };

type Props = {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  ariaLabel?: string;
  emptyOption?: Option | null; // Optional top option for clearing, e.g., "(Make root)"
  disabled?: boolean;
};

export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder,
  ariaLabel,
  emptyOption,
  disabled,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [highlight, setHighlight] = useState(0);
  const idBase = useId();

  const selectedLabel = useMemo(() => options.find(o => o.value === value)?.label ?? '', [options, value]);

  // Debounce query for large lists
  const [debouncedQuery, setDebouncedQuery] = useState('');
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query.trim().toLowerCase()), 150);
    return () => clearTimeout(t);
  }, [query]);

  const filtered = useMemo(() => {
    const base = emptyOption ? [emptyOption, ...options] : options;
    if (!debouncedQuery) return base;
    return base.filter(o => o.label.toLowerCase().includes(debouncedQuery));
  }, [options, emptyOption, debouncedQuery]);

  useEffect(() => {
    // Reset highlight when list changes
    setHighlight(0);
  }, [debouncedQuery, open]);

  // Close dropdown on outside click
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!open) return;
      const t = e.target as Node;
      if (inputRef.current?.contains(t) || listRef.current?.contains(t)) return;
      setOpen(false);
      setQuery('');
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [open]);

  function selectAtIndex(idx: number) {
    const opt = filtered[idx];
    if (!opt) return;
    onChange(opt.value);
    setOpen(false);
    setQuery('');
    // return focus to input for continued keyboard flow
    inputRef.current?.focus();
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open && (e.key === 'ArrowDown' || e.key === 'Enter')) {
      setOpen(true);
      setTimeout(() => inputRef.current?.select(), 0);
      e.preventDefault();
      return;
    }
    if (!open) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight(h => Math.min(h + 1, Math.max(0, filtered.length - 1)));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight(h => Math.max(h - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      selectAtIndex(highlight);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setOpen(false);
      setQuery('');
    }
  }

  const activeId = `${idBase}-opt-${highlight}`;

  return (
    <div className="searchable-select" style={{ position: 'relative' }}>
      <input
        ref={inputRef}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={`${idBase}-listbox`}
        aria-activedescendant={open ? activeId : undefined}
        aria-autocomplete="list"
        aria-label={ariaLabel}
        placeholder={placeholder}
        className="input"
        value={open ? query : selectedLabel}
        onFocus={() => {
          setOpen(true);
          setQuery(selectedLabel);
          // Select all text for quick replace
          setTimeout(() => inputRef.current?.select(), 0);
        }}
        onChange={(e) => {
          setQuery(e.target.value);
          if (!open) setOpen(true);
        }}
        onKeyDown={onKeyDown}
        disabled={disabled}
      />
      {open && (
        <ul
          id={`${idBase}-listbox`}
          ref={listRef}
          role="listbox"
          className="menu"
          style={{
            position: 'absolute',
            zIndex: 20,
            left: 0,
            right: 0,
            top: 'calc(100% + 4px)',
            background: 'var(--card-bg, #fff)',
            border: '1px solid var(--border, #ddd)',
            borderRadius: 6,
            maxHeight: 260,
            overflowY: 'auto',
            padding: 4,
            margin: 0,
            listStyle: 'none',
          }}
        >
          {filtered.length === 0 && (
            <li style={{ padding: '6px 8px', opacity: 0.6 }}>No results</li>
          )}
          {filtered.map((opt, idx) => (
            <li
              id={`${idBase}-opt-${idx}`}
              key={opt.value + idx}
              role="option"
              aria-selected={idx === highlight}
              className={idx === highlight ? 'active' : undefined}
              onMouseEnter={() => setHighlight(idx)}
              onMouseDown={(e) => {
                // prevent input blur before onClick
                e.preventDefault();
              }}
              onClick={() => selectAtIndex(idx)}
              style={{
                padding: '6px 8px',
                background: idx === highlight ? 'var(--hover, #f2f2f2)' : 'transparent',
                cursor: 'pointer',
                borderRadius: 4,
              }}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
