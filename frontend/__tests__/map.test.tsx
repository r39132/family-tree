import { render, screen, waitFor, act } from '@testing-library/react';

// Mock next/router
const mockPush = jest.fn();
const mockRouter = {
  push: mockPush,
  query: {},
  pathname: '/map',
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

// Mock api - need to define the mock implementation directly in the factory
jest.mock('../lib/api', () => ({
  api: jest.fn(() => {
    return Promise.resolve({
      enable_map: true,
      google_maps_api_key: 'test-key'
    });
  }),
}));

// Mock Google Maps API
const mockMap = {
  setCenter: jest.fn(),
  setZoom: jest.fn(),
  fitBounds: jest.fn(),
};

const mockMarker = {
  addListener: jest.fn(),
};

const mockInfoWindow = {
  open: jest.fn(),
  close: jest.fn(),
};

const mockBounds = {
  extend: jest.fn(),
};

// Set up global Google Maps mock
beforeAll(() => {
  (global as any).google = {
    maps: {
      Map: jest.fn(() => mockMap),
      Marker: jest.fn(() => mockMarker),
      InfoWindow: jest.fn(() => mockInfoWindow),
      LatLngBounds: jest.fn(() => mockBounds),
      LatLng: jest.fn(),
      MapTypeId: { ROADMAP: 'roadmap' },
      SymbolPath: { CIRCLE: 0 },
      Geocoder: jest.fn(() => ({
        geocode: jest.fn((request, callback) => {
          callback([{
            geometry: {
              location: {
                lat: () => 37.7749,
                lng: () => -122.4194,
              }
            }
          }], 'OK');
        })
      })),
    },
  };
});

// Import the component after mocks are set up
import MapPage from '../pages/map';
import { api } from '../lib/api';

describe('MapPage', () => {
  const mockApi = api as jest.MockedFunction<typeof api>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockRouter.query = {};
  });

  it('renders and loads content successfully', async () => {
    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({
          enable_map: true,
          google_maps_api_key: 'test-key'
        });
      }
      if (url === '/tree') {
        return Promise.resolve({
          members: [{
            id: '1',
            first_name: 'John',
            last_name: 'Doe',
            birth_location: 'New York, NY',
            residence_location: 'San Francisco, CA'
          }]
        });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<MapPage />);
    });

    // After loading completes, should show the layer switcher and content
    await waitFor(() => {
      expect(screen.getByLabelText('Select location layer to display')).toBeInTheDocument();
      expect(screen.getByText('Showing 1 family member with known residence locations.')).toBeInTheDocument();
    });
  });

  it('renders layer switcher after loading', async () => {
    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({
          enable_map: true,
          google_maps_api_key: 'test-key'
        });
      }
      if (url === '/tree') {
        return Promise.resolve({
          members: [{
            id: '1',
            first_name: 'John',
            last_name: 'Doe',
            birth_location: 'New York, NY',
            residence_location: 'San Francisco, CA'
          }]
        });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<MapPage />);
    });

    await waitFor(() => {
      expect(screen.queryByText('Loading family map...')).not.toBeInTheDocument();
    });

    expect(screen.getByLabelText('Select location layer to display')).toBeInTheDocument();
  });

  it('shows appropriate no-data message for empty tree', async () => {
    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({
          enable_map: true,
          google_maps_api_key: 'test-key'
        });
      }
      if (url === '/tree') {
        return Promise.resolve({ members: [] });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<MapPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('No family members have residence locations set.')).toBeInTheDocument();
    });
  });

  it('shows disabled message when maps are disabled', async () => {
    mockApi.mockImplementation((url) => {
      if (url === '/config') {
        return Promise.resolve({
          enable_map: false,
          google_maps_api_key: 'test-key'
        });
      }
      return Promise.resolve({});
    });

    await act(async () => {
      render(<MapPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('Map Feature Not Available')).toBeInTheDocument();
      expect(screen.getByText('The map feature is currently disabled. Please contact your administrator to enable it.')).toBeInTheDocument();
    });
  });
});
