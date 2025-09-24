/**
 * Comprehensive frontend tests for tree display and version management
 * Tests identified UI bugs and state management issues
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import HomePage from '../pages/index';
import { useRouter } from 'next/router';

// Mock Next.js router
const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}));

// Mock fetch with proper typing
const mockFetch = jest.fn();
global.fetch = mockFetch as any;

describe('Tree Display System Tests', () => {
  const mockPush = jest.fn();
  const mockReplace = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: mockReplace,
      query: {},
      asPath: '/',
    });

    (fetch as jest.Mock).mockClear();
    mockPush.mockClear();
    mockReplace.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('BUG: Tree displays flat when hierarchical data exists', async () => {
    // Setup: Mock API response with clear hierarchical data
    const hierarchicalData = [
      {
        id: 'parent1',
        name: 'John Doe',
        parent_id: null, // Root member
        relationships: [
          { child_id: 'child1', relationship_type: 'parent' }
        ]
      },
      {
        id: 'child1',
        name: 'Jane Doe',
        parent_id: 'parent1', // Clear parent relationship
        relationships: []
      }
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => hierarchicalData,
    } as any);

    // Mock tree versions call
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ versions: [], active_version: null }),
    } as any);

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    });

    // BUG TEST: Check if tree structure is actually hierarchical
    const johnElement = screen.getByText('John Doe').closest('.node');
    const janeElement = screen.getByText('Jane Doe').closest('.node');

    // In a proper tree, Jane should be nested under John
    // But due to bug, they might be at same level
    const johnLevel = getElementDepth(johnElement);
    const janeLevel = getElementDepth(janeElement);

    console.log(`John depth: ${johnLevel}, Jane depth: ${janeLevel}`);

    // BUG: Jane should be deeper than John, but they're at same level
    expect(janeLevel).toBeGreaterThan(johnLevel);
  });

  test('BUG: Tree view mode changes dont persist properly', async () => {
    // Mock members data
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ([
        { id: '1', name: 'John', parent_id: null }
      ]),
    });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('John')).toBeInTheDocument();
    });

    // Find and click tree view dropdown
    const dropdown = screen.getByDisplayValue('Standard');
    fireEvent.change(dropdown, { target: { value: 'minimal' } });

    // BUG: View should change but DOM might not update properly
    await waitFor(() => {
      const updatedDropdown = screen.getByDisplayValue('Minimal');
      expect(updatedDropdown).toBeInTheDocument();
    });

    // Check if tree actually re-rendered with new view
    // In Minimal mode, nodes should have different styling
    const node = screen.getByText('John').closest('.node');
    expect(node).toHaveClass('minimal-view'); // This might fail due to bug
  });

  test('BUG: Version recovery UI state corruption', async () => {
    // Mock versions data
    const mockVersions = [
      {
        id: 'v1',
        created_at: '2025-01-01T10:00:00Z',
        version: 1
      },
      {
        id: 'v2',
        created_at: '2025-01-01T11:00:00Z',
        version: 2
      }
    ];

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]), // Empty members initially
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ versions: mockVersions, active_version: 'v2' }),
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('Versions')).toBeInTheDocument();
    });

    // Click to show versions
    fireEvent.click(screen.getByText('Versions'));

    await waitFor(() => {
      expect(screen.getByText('Version 1')).toBeInTheDocument();
      expect(screen.getByText('Version 2')).toBeInTheDocument();
    });

    // Mock recovery API call
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Recovered successfully' }),
    });

    // Mock updated members after recovery
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ([
        { id: '1', name: 'Recovered Member', parent_id: null }
      ]),
    });

    // Try to recover version 1
    const recoverButtons = screen.getAllByText('Recover');
    fireEvent.click(recoverButtons[0]);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/tree/recover',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ version_id: 'v1' }),
        })
      );
    });

    // BUG: UI might show success but tree doesn't update
    // or shows inconsistent state between versions and tree
    await waitFor(() => {
      expect(screen.getByText('Recovered Member')).toBeInTheDocument();
    });
  });

  test('BUG: Multiple rapid view changes cause state corruption', async () => {
    // Mock data
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ([
        { id: '1', name: 'Test', parent_id: null }
      ]),
    });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('Test')).toBeInTheDocument();
    });

    const dropdown = screen.getByDisplayValue('Standard');

    // Rapidly change views multiple times
    const views = ['minimal', 'horizontal', 'cards', 'standard'];

    for (let i = 0; i < 10; i++) {
      const view = views[i % views.length];
      fireEvent.change(dropdown, { target: { value: view } });

      // Small delay to simulate real user interaction
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    // BUG: After rapid changes, view might be stuck or corrupted
    // Final state should be 'standard' but might be something else
    const finalDropdown = screen.getByDisplayValue('Standard');
    expect(finalDropdown).toBeInTheDocument();

    // Tree should still be functional
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  test('BUG: Version save button state inconsistency', async () => {
    // Mock initial data
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([
          { id: '1', name: 'John', parent_id: null }
        ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ versions: [], active_version: null }),
      });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('John')).toBeInTheDocument();
    });

    // Initially, should show "No unsaved changes"
    expect(screen.getByText(/No unsaved changes/)).toBeInTheDocument();

    // Mock unsaved changes detection
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ unsaved: true }),
    });

    // Simulate an action that creates unsaved changes (like adding member)
    // For this test, we'll manually trigger the check
    const saveButton = screen.getByText('Save Current Version');

    // BUG: Button state might not update even when unsaved changes exist
    expect(saveButton).not.toBeDisabled();
  });

  test('Error handling: API failures should not crash tree display', async () => {
    // Mock API failure
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(<HomePage />);

    // Should show error message instead of crashing
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });

    // Tree container should still be rendered
    const treeContainer = screen.getByTestId('tree-container') ||
                         screen.getByText(/family tree/i).closest('div');
    expect(treeContainer).toBeInTheDocument();
  });
});

describe('Tree Node Rendering Tests', () => {
  test('Node click handling in different view modes', async () => {
    const mockMembers = [
      { id: '1', name: 'John Doe', parent_id: null },
      { id: '2', name: 'Jane Doe', parent_id: '1' }
    ];

    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockMembers,
    });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Test click in horizontal mode (should navigate)
    const dropdown = screen.getByDisplayValue('Standard');
    fireEvent.change(dropdown, { target: { value: 'horizontal' } });

    await waitFor(() => {
      expect(screen.getByDisplayValue('Horizontal')).toBeInTheDocument();
    });

    // Click on member name in horizontal mode
    const johnLink = screen.getByText('John Doe');
    fireEvent.click(johnLink);

    // Should navigate to view page
    expect(mockPush).toHaveBeenCalledWith('/view/1');
  });
});

// Helper function to calculate DOM element nesting depth
function getElementDepth(element: HTMLElement | null): number {
  if (!element) return 0;

  let depth = 0;
  let current = element.parentElement;

  while (current && current.classList.contains('tree-container')) {
    if (current.classList.contains('node') ||
        current.classList.contains('child-nodes')) {
      depth++;
    }
    current = current.parentElement;
  }

  return depth;
}
