/**
 * Tag Search Components Tests
 * 
 * Tests for TagSearch, TagChips, and PopularTags components
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TagSearch from '../components/TagSearch';
import TagChips from '../components/TagChips';
import PopularTags from '../components/PopularTags';

// Mock fetch
global.fetch = jest.fn();

describe('TagSearch Component', () => {
  const mockProps = {
    spaceId: 'test-space',
    apiBase: 'http://localhost:8080',
    token: 'test-token',
    selectedTags: [],
    onTagsChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        tags: [
          { tag: 'family', count: 10 },
          { tag: 'vacation', count: 5 },
          { tag: 'birthday', count: 3 },
        ],
        total_tags: 3,
      }),
    });
  });

  it('renders search input', () => {
    render(<TagSearch {...mockProps} />);
    const input = screen.getByPlaceholderText('Search tags...');
    expect(input).toBeInTheDocument();
  });

  it('fetches tags on mount', async () => {
    render(<TagSearch {...mockProps} />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8080/spaces/test-space/album/tags?sort_by=count',
        {
          headers: {
            Authorization: 'Bearer test-token',
          },
        }
      );
    });
  });

  it('shows dropdown when input is focused', async () => {
    render(<TagSearch {...mockProps} />);
    
    const input = screen.getByPlaceholderText('Search tags...');
    fireEvent.focus(input);
    
    await waitFor(() => {
      expect(screen.getByText('#family')).toBeInTheDocument();
    });
  });

  it('filters tags based on search query', async () => {
    render(<TagSearch {...mockProps} />);
    
    const input = screen.getByPlaceholderText('Search tags...');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'fam' } });
    
    await waitFor(() => {
      expect(screen.getByText('#family')).toBeInTheDocument();
      expect(screen.queryByText('#vacation')).not.toBeInTheDocument();
    });
  });

  it('calls onTagsChange when tag is selected', async () => {
    render(<TagSearch {...mockProps} />);
    
    const input = screen.getByPlaceholderText('Search tags...');
    fireEvent.focus(input);
    
    await waitFor(() => {
      const familyTag = screen.getByText('#family');
      fireEvent.click(familyTag);
    });
    
    expect(mockProps.onTagsChange).toHaveBeenCalledWith(['family']);
  });

  it('excludes already selected tags from dropdown', async () => {
    const props = { ...mockProps, selectedTags: ['family'] };
    render(<TagSearch {...props} />);
    
    const input = screen.getByPlaceholderText('Search tags...');
    fireEvent.focus(input);
    
    await waitFor(() => {
      expect(screen.queryByText('#family')).not.toBeInTheDocument();
      expect(screen.getByText('#vacation')).toBeInTheDocument();
    });
  });
});

describe('TagChips Component', () => {
  const mockProps = {
    tags: ['family', 'vacation', 'birthday'],
    onRemove: jest.fn(),
    onClearAll: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders all tag chips', () => {
    render(<TagChips {...mockProps} />);
    
    expect(screen.getByText('#family')).toBeInTheDocument();
    expect(screen.getByText('#vacation')).toBeInTheDocument();
    expect(screen.getByText('#birthday')).toBeInTheDocument();
  });

  it('calls onRemove when remove button is clicked', () => {
    render(<TagChips {...mockProps} />);
    
    const removeButtons = screen.getAllByRole('button', { name: /Remove .* filter/ });
    fireEvent.click(removeButtons[0]);
    
    expect(mockProps.onRemove).toHaveBeenCalledWith('family');
  });

  it('shows clear all button when multiple tags exist', () => {
    render(<TagChips {...mockProps} />);
    
    expect(screen.getByText('Clear all')).toBeInTheDocument();
  });

  it('calls onClearAll when clear all button is clicked', () => {
    render(<TagChips {...mockProps} />);
    
    const clearAllButton = screen.getByText('Clear all');
    fireEvent.click(clearAllButton);
    
    expect(mockProps.onClearAll).toHaveBeenCalled();
  });

  it('does not render when tags array is empty', () => {
    const props = { ...mockProps, tags: [] };
    const { container } = render(<TagChips {...props} />);
    
    expect(container.firstChild).toBeNull();
  });

  it('disables buttons when disabled prop is true', () => {
    const props = { ...mockProps, disabled: true };
    render(<TagChips {...props} />);
    
    const removeButtons = screen.getAllByRole('button', { name: /Remove .* filter/ });
    expect(removeButtons[0]).toBeDisabled();
  });
});

describe('PopularTags Component', () => {
  const mockProps = {
    spaceId: 'test-space',
    apiBase: 'http://localhost:8080',
    token: 'test-token',
    onTagClick: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        tags: [
          { tag: 'family', count: 10 },
          { tag: 'vacation', count: 5 },
          { tag: 'birthday', count: 3 },
        ],
        total_tags: 3,
      }),
    });
  });

  it('fetches popular tags on mount', async () => {
    render(<PopularTags {...mockProps} />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8080/spaces/test-space/album/tags?sort_by=count',
        {
          headers: {
            Authorization: 'Bearer test-token',
          },
        }
      );
    });
  });

  it('renders popular tags', async () => {
    render(<PopularTags {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('#family')).toBeInTheDocument();
      expect(screen.getByText('(10)')).toBeInTheDocument();
    });
  });

  it('calls onTagClick when tag is clicked', async () => {
    render(<PopularTags {...mockProps} />);
    
    await waitFor(() => {
      const familyTag = screen.getByText('#family');
      fireEvent.click(familyTag.closest('button')!);
    });
    
    expect(mockProps.onTagClick).toHaveBeenCalledWith('family');
  });

  it('does not render when no tags are available', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        tags: [],
        total_tags: 0,
      }),
    });
    
    const { container } = render(<PopularTags {...mockProps} />);
    
    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it('shows only top 10 tags', async () => {
    const manyTags = Array.from({ length: 15 }, (_, i) => ({
      tag: `tag${i}`,
      count: 15 - i,
    }));
    
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        tags: manyTags,
        total_tags: 15,
      }),
    });
    
    render(<PopularTags {...mockProps} />);
    
    await waitFor(() => {
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBe(10);
    });
  });
});
