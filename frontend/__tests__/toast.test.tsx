import { render, screen, waitFor } from '@testing-library/react';
import { act } from '@testing-library/react';
import '@testing-library/jest-dom';
import Toast from '../components/Toast';

describe('Toast Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders success toast with correct message', () => {
    const onDismiss = jest.fn();
    render(<Toast type="success" message="Test success" onDismiss={onDismiss} />);
    
    expect(screen.getByText('Test success')).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('renders error toast with correct message', () => {
    const onDismiss = jest.fn();
    render(<Toast type="error" message="Test error" onDismiss={onDismiss} />);
    
    expect(screen.getByText('Test error')).toBeInTheDocument();
    expect(screen.getByText('✗')).toBeInTheDocument();
  });

  it('renders info toast with correct message', () => {
    const onDismiss = jest.fn();
    render(<Toast type="info" message="Test info" onDismiss={onDismiss} />);
    
    expect(screen.getByText('Test info')).toBeInTheDocument();
    expect(screen.getByText('ℹ')).toBeInTheDocument();
  });

  it('calls onDismiss when clicked', () => {
    const onDismiss = jest.fn();
    const { container } = render(<Toast type="success" message="Test" onDismiss={onDismiss} />);
    
    const toastElement = container.querySelector('[role="alert"]') as HTMLElement;
    expect(toastElement).toBeInTheDocument();
    
    if (toastElement) {
      toastElement.click();
      expect(onDismiss).toHaveBeenCalledTimes(1);
    }
  });

  it('auto-dismisses after specified duration', () => {
    const onDismiss = jest.fn();
    render(<Toast type="success" message="Test" duration={3000} onDismiss={onDismiss} />);
    
    expect(onDismiss).not.toHaveBeenCalled();
    
    act(() => {
      jest.advanceTimersByTime(3000);
    });
    
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it('uses default duration of 3000ms when not specified', () => {
    const onDismiss = jest.fn();
    render(<Toast type="success" message="Test" onDismiss={onDismiss} />);
    
    act(() => {
      jest.advanceTimersByTime(2999);
    });
    expect(onDismiss).not.toHaveBeenCalled();
    
    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it('has proper ARIA attributes for accessibility', () => {
    const onDismiss = jest.fn();
    const { container } = render(<Toast type="success" message="Test" onDismiss={onDismiss} />);
    
    const toastElement = container.querySelector('[role="alert"]');
    expect(toastElement).toBeInTheDocument();
    expect(toastElement).toHaveAttribute('aria-live', 'polite');
  });

  it('cleans up timer on unmount', () => {
    const onDismiss = jest.fn();
    const { unmount } = render(<Toast type="success" message="Test" duration={5000} onDismiss={onDismiss} />);
    
    unmount();
    
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    
    // onDismiss should not be called after unmount
    expect(onDismiss).not.toHaveBeenCalled();
  });
});
