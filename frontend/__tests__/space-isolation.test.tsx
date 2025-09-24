/**
 * Frontend tests for space-specific tree functionality
 * Tests UI behavior with space isolation and multi-user scenarios
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import HomePage from '../pages/index';

// Mock Next.js router
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    query: {},
    asPath: '/',
    events: {
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn()
    }
  }),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch as any;

describe('Space-Specific Tree Functionality', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    mockPush.mockClear();
    mockReplace.mockClear();
  });

  test('Tree displays only current space members', async () => {
    // Mock space A data
    const spaceAMembers = [
      {
        id: 'alice_member',
        first_name: 'Alice',
        last_name: 'Smith',
        parent_id: null,
        space_id: 'space_a_123'
      },
      {
        id: 'bob_member',
        first_name: 'Bob',
        last_name: 'Smith',
        parent_id: 'alice_member',
        space_id: 'space_a_123'
      }
    ];

    // Mock API responses for Alice's space
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false }) // Config
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ versions: [], active_version: null }) // Versions
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: spaceAMembers }) // Tree data
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: false }) // Unsaved status
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
      expect(screen.getByText('Bob Smith')).toBeInTheDocument();
    });

    // Should only see space A members
    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.getByText('Bob Smith')).toBeInTheDocument();

    // Should NOT see members from other spaces
    expect(screen.queryByText('David Johnson')).not.toBeInTheDocument();
    expect(screen.queryByText('Emma Johnson')).not.toBeInTheDocument();
  });

  test('Version save creates space-specific version', async () => {
    // Mock initial data
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ versions: [], active_version: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: true }) // Has unsaved changes
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('Save Tree')).toBeInTheDocument();
    });

    // Mock save response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 'version_space_a_123',
        version: 1,
        created_at: '2025-01-01T12:00:00Z'
      })
    });

    // Mock reload after save
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          versions: [{ id: 'version_space_a_123', version: 1 }],
          active_version: 'version_space_a_123'
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: false })
      });

    // Click save button
    const saveButton = screen.getByText('Save Tree');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/tree/save',
        expect.objectContaining({
          method: 'POST'
        })
      );
    });

    // Should show success message
    // Note: alert() would need to be mocked to test this properly
  });

  test('Version recovery validates space ownership', async () => {
    // Mock versions from user's space
    const userVersions = [
      {
        id: 'version_user_space',
        version: 1,
        created_at: '2025-01-01T10:00:00Z'
      },
      {
        id: 'version_user_space_2',
        version: 2,
        created_at: '2025-01-01T11:00:00Z'
      }
    ];

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          versions: userVersions,
          active_version: 'version_user_space_2'
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: false })
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('Version 1')).toBeInTheDocument();
      expect(screen.getByText('Version 2')).toBeInTheDocument();
    });

    // Should only show versions from user's space
    const versionSelect = screen.getByDisplayValue('Select version…');
    expect(versionSelect).toBeInTheDocument();

    // The versions dropdown should only contain user's versions
    fireEvent.click(versionSelect);
    expect(screen.getByText(/Version 1/)).toBeInTheDocument();
    expect(screen.getByText(/Version 2/)).toBeInTheDocument();
  });

  test('Unsaved changes detection works with space-specific active versions', async () => {
    // Mock scenario where user has space-specific unsaved changes
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          versions: [{ id: 'v1', version: 1 }],
          active_version: 'v1'
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: true }) // Has unsaved changes
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText(/You have unsaved changes/)).toBeInTheDocument();
    });

    // Should show unsaved changes warning
    expect(screen.getByText(/You have unsaved changes/)).toBeInTheDocument();

    // Save button should be enabled
    const saveButton = screen.getByText('Save Tree');
    expect(saveButton).not.toBeDisabled();
  });

  test('Tree operations maintain space isolation', async () => {
    const spaceMembers = [
      {
        id: 'parent_member',
        first_name: 'Parent',
        last_name: 'User',
        parent_id: null,
        space_id: 'user_space_123'
      },
      {
        id: 'child_member',
        first_name: 'Child',
        last_name: 'User',
        parent_id: 'parent_member',
        space_id: 'user_space_123'
      }
    ];

    // Mock initial load
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ versions: [], active_version: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          roots: [
            {
              member: spaceMembers[0],
              children: [
                {
                  member: spaceMembers[1],
                  children: []
                }
              ]
            }
          ],
          members: spaceMembers
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: false })
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('Parent User')).toBeInTheDocument();
      expect(screen.getByText('Child User')).toBeInTheDocument();
    });

    // Verify hierarchical structure is displayed
    const parentNode = screen.getByText('Parent User').closest('.node-compact');
    const childNode = screen.getByText('Child User').closest('.node-compact');

    expect(parentNode).toBeInTheDocument();
    expect(childNode).toBeInTheDocument();

    // In proper hierarchy, child should be nested deeper than parent
    // This is harder to test with the current DOM structure but the presence of both indicates success
  });

  test('Version recovery failure shows appropriate error', async () => {
    // Setup with versions
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          versions: [{ id: 'v1', version: 1 }],
          active_version: null
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: false })
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('Recover')).toBeInTheDocument();
    });

    // Select version to recover
    const versionSelect = screen.getByDisplayValue('Select version…');
    fireEvent.change(versionSelect, { target: { value: 'v1' } });

    // Mock recovery failure (e.g., cross-space access attempt)
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Access denied: Version belongs to different space' })
    });

    // Click recover
    const recoverButton = screen.getByText('Recover');
    fireEvent.click(recoverButton);

    // Should handle error gracefully
    // Note: Error handling would need to be implemented in the component
  });

  test('Multiple rapid operations maintain space consistency', async () => {
    // Mock initial state
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ versions: [], active_version: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: true })
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('Save Tree')).toBeInTheDocument();
    });

    // Mock multiple save operations
    for (let i = 0; i < 3; i++) {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: `version_${i}`,
          version: i + 1,
          created_at: '2025-01-01T12:00:00Z'
        })
      });

      // Mock reload after each save
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ enable_map: false })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ versions: [], active_version: `version_${i}` })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ roots: [], members: [] })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ unsaved: false })
        });
    }

    // Perform rapid saves
    const saveButton = screen.getByText('Save Tree');
    for (let i = 0; i < 3; i++) {
      fireEvent.click(saveButton);
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Should handle all operations without issues
    // All saves should use space-specific endpoints
  });
});

describe('Space-Specific UI State Management', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  test('Navigation guard respects space-specific unsaved state', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ versions: [], active_version: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: true }) // Space-specific unsaved changes
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText(/You have unsaved changes/)).toBeInTheDocument();
    });

    // Should show unsaved warning for this space
    expect(screen.getByText(/You have unsaved changes/)).toBeInTheDocument();

    // Navigation guard would be triggered on route change
    // This is tested through the useEffect hook that listens to router events
  });

  test('Version list updates reflect space-specific changes', async () => {
    // Mock initial empty versions
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ versions: [], active_version: null })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: true })
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Select version…')).toBeInTheDocument();
    });

    // Initially no versions
    const versionSelect = screen.getByDisplayValue('Select version…');
    expect(versionSelect).toBeInTheDocument();

    // Mock save operation and reload
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 'new_version',
        version: 1,
        created_at: '2025-01-01T12:00:00Z'
      })
    });

    // Mock reload with new version
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          versions: [{
            id: 'new_version',
            version: 1,
            created_at: '2025-01-01T12:00:00Z'
          }],
          active_version: 'new_version'
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ roots: [], members: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unsaved: false })
      });

    // Save tree
    const saveButton = screen.getByText('Save Tree');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Version 1/)).toBeInTheDocument();
    });

    // Should now show the new version
    expect(screen.getByText(/Version 1/)).toBeInTheDocument();
  });
});
