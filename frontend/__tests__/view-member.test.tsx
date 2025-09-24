import { render, screen, act, waitFor } from '@testing-library/react';

// Mock next/router
const mockPush = jest.fn();
const mockRouter = {
  push: mockPush,
  query: { id: '1' },
  pathname: '/view/[id]',
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

// Mock api
jest.mock('../lib/api', () => ({
  api: jest.fn(),
}));

const mockMember = {
  id: '1',
  first_name: 'John',
  last_name: 'Doe',
  email: 'john@example.com',
  birth_date: '1990-01-01',
  birth_location: 'New York, NY',
  residence_location: 'San Francisco, CA',
  hobbies: [],
  children: [],
  relationships: [],
  invited_by: null,
  invite_date: null
};

// Import the component after mocks are set up
import ViewMember from '../pages/view/[id]';
import { api } from '../lib/api';

describe('ViewMember', () => {
  const mockApi = api as jest.MockedFunction<typeof api>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockRouter.query = { id: '1' };
  });

  it('renders map buttons for both birth and residence locations when available', async () => {
    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({ enable_map: true });
      }
      if (url === '/tree') {
        return Promise.resolve({ members: [mockMember] });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<ViewMember />);
    });

    await waitFor(() => {
      expect(screen.getByText('First Name')).toBeInTheDocument();
    });

    // Should show both map buttons
    expect(screen.getByLabelText('View birthplace on map')).toBeInTheDocument();
    expect(screen.getByLabelText('View residence on map')).toBeInTheDocument();
  });

  it('only shows residence map button when birth location is missing', async () => {
    const memberWithoutBirthLocation = {
      ...mockMember,
      birth_location: ''
    };

    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({ enable_map: true });
      }
      if (url === '/tree') {
        return Promise.resolve({ members: [memberWithoutBirthLocation] });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<ViewMember />);
    });

    await waitFor(() => {
      expect(screen.getByText('First Name')).toBeInTheDocument();
    });

    // Should only show residence map button
    expect(screen.queryByLabelText('View birthplace on map')).not.toBeInTheDocument();
    expect(screen.getByLabelText('View residence on map')).toBeInTheDocument();
  });

  it('only shows birth map button when residence location is missing', async () => {
    const memberWithoutResidenceLocation = {
      ...mockMember,
      residence_location: ''
    };

    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({ enable_map: true });
      }
      if (url === '/tree') {
        return Promise.resolve({ members: [memberWithoutResidenceLocation] });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<ViewMember />);
    });

    await waitFor(() => {
      expect(screen.getByText('First Name')).toBeInTheDocument();
    });

    // Should only show birth map button
    expect(screen.getByLabelText('View birthplace on map')).toBeInTheDocument();
    expect(screen.queryByLabelText('View residence on map')).not.toBeInTheDocument();
  });

  it('shows no map buttons when maps are disabled', async () => {
    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({ enable_map: false });
      }
      if (url === '/tree') {
        return Promise.resolve({ members: [mockMember] });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<ViewMember />);
    });

    await waitFor(() => {
      expect(screen.getByText('First Name')).toBeInTheDocument();
    });

    // Should show no map buttons when maps are disabled
    expect(screen.queryByLabelText('View birthplace on map')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('View residence on map')).not.toBeInTheDocument();
  });

  it('shows no map buttons when both locations are missing', async () => {
    const memberWithoutLocations = {
      ...mockMember,
      birth_location: '',
      residence_location: ''
    };

    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({ enable_map: true });
      }
      if (url === '/tree') {
        return Promise.resolve({ members: [memberWithoutLocations] });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<ViewMember />);
    });

    await waitFor(() => {
      expect(screen.getByText('First Name')).toBeInTheDocument();
    });

    // Should show no map buttons when no locations available
    expect(screen.queryByLabelText('View birthplace on map')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('View residence on map')).not.toBeInTheDocument();
  });
});
