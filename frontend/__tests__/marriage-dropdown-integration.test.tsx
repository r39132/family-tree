/**
 * Integration tests for marriage dropdown age filtering
 * Tests that spouse/partner selection dropdowns properly filter out members under 18
 */

import { render, screen, waitFor } from '@testing-library/react';
import AddMemberPage from '../pages/add';
import EditMemberPage from '../pages/edit/[id]';

// Mock Next.js router
const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch as any;

// Import after mocking
import { useRouter } from 'next/router';

describe('Marriage Dropdown Age Filtering', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: mockReplace,
      query: {},
      asPath: '/',
      isReady: false,
    });

    mockFetch.mockClear();
    mockPush.mockClear();
    mockReplace.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Add Member Page - Spouse Dropdown', () => {
    it('filters out members under 18 from spouse dropdown', async () => {
      const today = new Date();
      const eighteenYearsAgo = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
      const sixteenYearsAgo = new Date(today.getFullYear() - 16, today.getMonth(), today.getDate());
      const twentyFiveYearsAgo = new Date(today.getFullYear() - 25, today.getMonth(), today.getDate());

      const formatDate = (d: Date) => 
        `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}/${d.getFullYear()}`;

      const mockMembers = [
        {
          id: 'member1',
          first_name: 'Adult',
          last_name: 'One',
          dob: formatDate(twentyFiveYearsAgo),
          spouse_id: null,
        },
        {
          id: 'member2',
          first_name: 'Exactly',
          last_name: 'Eighteen',
          dob: formatDate(eighteenYearsAgo),
          spouse_id: null,
        },
        {
          id: 'member3',
          first_name: 'Teen',
          last_name: 'Under18',
          dob: formatDate(sixteenYearsAgo),
          spouse_id: null,
        },
      ];

      // Mock config response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false }),
      } as any);

      // Mock tree data response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          roots: [],
          members: mockMembers,
        }),
      } as any);

      render(<AddMemberPage />);

      // Wait for loading to complete and dropdown to be populated
      await waitFor(() => {
        const spouseSelect = screen.getByLabelText(/spouse\/partner/i) as HTMLSelectElement;
        expect(spouseSelect.options.length).toBeGreaterThan(1); // More than just "(None)"
      }, { timeout: 3000 });

      // Get the spouse dropdown
      const spouseSelect = screen.getByLabelText(/spouse\/partner/i) as HTMLSelectElement;
      const options = Array.from(spouseSelect.options).map(opt => opt.textContent);

      // Should include adults and exactly 18 year olds
      expect(options).toContain('Adult One');
      expect(options).toContain('Exactly Eighteen');

      // Should NOT include members under 18
      expect(options).not.toContain('Teen Under18');
    });

    it('includes member who turns 18 today', async () => {
      const today = new Date();
      const formatDate = (d: Date) => 
        `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}/${d.getFullYear()}`;

      const eighteenYearsAgoToday = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());

      const mockMembers = [
        {
          id: 'member1',
          first_name: 'Birthday',
          last_name: 'Today',
          dob: formatDate(eighteenYearsAgoToday),
          spouse_id: null,
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false }),
      } as any);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          roots: [],
          members: mockMembers,
        }),
      } as any);

      render(<AddMemberPage />);

      await waitFor(() => {
        const spouseSelect = screen.getByLabelText(/spouse\/partner/i) as HTMLSelectElement;
        expect(spouseSelect.options.length).toBeGreaterThan(1);
      }, { timeout: 3000 });

      const spouseSelect = screen.getByLabelText(/spouse\/partner/i) as HTMLSelectElement;
      const options = Array.from(spouseSelect.options).map(opt => opt.textContent);

      expect(options).toContain('Birthday Today');
    });

    it('excludes member who turns 18 tomorrow', async () => {
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      const formatDate = (d: Date) => 
        `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}/${d.getFullYear()}`;

      const eighteenYearsAgoTomorrow = new Date(tomorrow.getFullYear() - 18, tomorrow.getMonth(), tomorrow.getDate());

      const mockMembers = [
        {
          id: 'member1',
          first_name: 'Birthday',
          last_name: 'Tomorrow',
          dob: formatDate(eighteenYearsAgoTomorrow),
          spouse_id: null,
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false }),
      } as any);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          roots: [],
          members: mockMembers,
        }),
      } as any);

      render(<AddMemberPage />);

      await waitFor(() => {
        const spouseSelect = screen.getByLabelText(/spouse\/partner/i);
        expect(spouseSelect).toBeInTheDocument();
      });

      const spouseSelect = screen.getByLabelText(/spouse\/partner/i) as HTMLSelectElement;
      const options = Array.from(spouseSelect.options).map(opt => opt.textContent);

      expect(options).not.toContain('Birthday Tomorrow');
    });
  });

  describe('Edit Member Page - Spouse Dropdown', () => {
    it('filters out members under 18 from spouse dropdown', async () => {
      (useRouter as jest.Mock).mockReturnValue({
        push: mockPush,
        replace: mockReplace,
        query: { id: 'edit-member-id' },
        asPath: '/edit/edit-member-id',
        isReady: true,
      });

      const today = new Date();
      const eighteenYearsAgo = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
      const sixteenYearsAgo = new Date(today.getFullYear() - 16, today.getMonth(), today.getDate());
      const twentyFiveYearsAgo = new Date(today.getFullYear() - 25, today.getMonth(), today.getDate());

      const formatDate = (d: Date) => 
        `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}/${d.getFullYear()}`;

      const mockMembers = [
        {
          id: 'edit-member-id',
          first_name: 'Current',
          last_name: 'Member',
          dob: formatDate(twentyFiveYearsAgo),
          spouse_id: null,
        },
        {
          id: 'member1',
          first_name: 'Adult',
          last_name: 'One',
          dob: formatDate(twentyFiveYearsAgo),
          spouse_id: null,
        },
        {
          id: 'member2',
          first_name: 'Exactly',
          last_name: 'Eighteen',
          dob: formatDate(eighteenYearsAgo),
          spouse_id: null,
        },
        {
          id: 'member3',
          first_name: 'Teen',
          last_name: 'Under18',
          dob: formatDate(sixteenYearsAgo),
          spouse_id: null,
        },
      ];

      // Mock config response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ enable_map: false }),
      } as any);

      // Mock tree data response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          roots: [],
          members: mockMembers,
        }),
      } as any);

      render(<EditMemberPage />);

      await waitFor(() => {
        const spouseSelect = screen.getByLabelText(/spouse/i);
        expect(spouseSelect).toBeInTheDocument();
      });

      // Get the spouse dropdown
      const spouseSelect = screen.getByLabelText(/spouse/i) as HTMLSelectElement;
      const options = Array.from(spouseSelect.options).map(opt => opt.textContent);

      // Should include adults and exactly 18 year olds
      expect(options).toContain('Adult One');
      expect(options).toContain('Exactly Eighteen');

      // Should NOT include members under 18
      expect(options).not.toContain('Teen Under18');

      // Should NOT include the current member
      expect(options).not.toContain('Current Member');
    });
  });
});
