import { useEffect } from 'react';

export type ToastType = 'success' | 'error' | 'info';

export interface ToastProps {
  type: ToastType;
  message: string;
  duration?: number;
  onDismiss: () => void;
}

export default function Toast({ type, message, duration = 3000, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, duration);
    return () => clearTimeout(timer);
  }, [duration, onDismiss]);

  const backgroundColor = type === 'success' 
    ? '#4caf50' 
    : type === 'error' 
    ? '#f44336' 
    : '#2196f3';

  const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';

  return (
    <div
      role="alert"
      aria-live="polite"
      style={{
        position: 'fixed',
        top: '80px',
        right: '20px',
        backgroundColor,
        color: 'white',
        padding: '12px 20px',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        zIndex: 2001,
        minWidth: '250px',
        maxWidth: '400px',
        cursor: 'pointer',
        animation: 'slideIn 0.3s ease-out'
      }}
      onClick={onDismiss}
    >
      <span style={{ fontSize: '20px', fontWeight: 'bold' }}>{icon}</span>
      <span style={{ flex: 1, fontSize: '14px' }}>{message}</span>
      <style jsx>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}
