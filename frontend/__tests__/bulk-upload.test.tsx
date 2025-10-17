import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BulkUploadPage from '../pages/bulk-upload';

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/bulk-upload',
    query: {},
    asPath: '/bulk-upload',
  }),
}));

// Mock the api function
jest.mock('../lib/api', () => ({
  api: jest.fn(),
}));

describe('BulkUploadPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the bulk upload page', () => {
    render(<BulkUploadPage />);
    
    expect(screen.getByText('Bulk Upload Members')).toBeInTheDocument();
    expect(screen.getByText('Select JSON File')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
  });

  it('shows format guide', () => {
    render(<BulkUploadPage />);
    
    expect(screen.getByText('JSON Format Guide')).toBeInTheDocument();
    expect(screen.getByText(/Your JSON file should follow this structure/i)).toBeInTheDocument();
  });

  it('disables upload button when no file is selected', () => {
    render(<BulkUploadPage />);
    
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    expect(uploadButton).toBeDisabled();
  });

  it('validates file extension', async () => {
    const { container } = render(<BulkUploadPage />);
    
    const file = new File(['{}'], 'test.txt', { type: 'text/plain' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (input) {
      fireEvent.change(input, { target: { files: [file] } });
      
      await waitFor(() => {
        expect(screen.getByText(/Please select a JSON file/i)).toBeInTheDocument();
      });
    }
  });

  it('displays selected file information', () => {
    const { container } = render(<BulkUploadPage />);
    
    const file = new File(['{"space_name": "Demo", "members": []}'], 'demo.json', { 
      type: 'application/json' 
    });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (input) {
      fireEvent.change(input, { target: { files: [file] } });
      
      expect(screen.getByText(/Selected: demo.json/i)).toBeInTheDocument();
    }
  });

  it('shows back to tree button', () => {
    render(<BulkUploadPage />);
    
    const backButton = screen.getByRole('button', { name: /Back to Tree/i });
    expect(backButton).toBeInTheDocument();
  });

  it('shows reset button after file selection', () => {
    const { container } = render(<BulkUploadPage />);
    
    const file = new File(['{"space_name": "Demo", "members": []}'], 'demo.json', { 
      type: 'application/json' 
    });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (input) {
      fireEvent.change(input, { target: { files: [file] } });
      
      expect(screen.getByRole('button', { name: /Reset/i })).toBeInTheDocument();
    }
  });
});
