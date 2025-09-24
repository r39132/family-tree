import React from 'react';

interface LoadingOverlayProps {
  isLoading: boolean;
  message?: string;
  transparent?: boolean;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isLoading,
  message = "Loading...",
  transparent = false
}) => {
  if (!isLoading) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center ${
        transparent ? 'bg-black bg-opacity-30' : 'bg-white bg-opacity-90'
      }`}
      style={{ backdropFilter: 'blur(2px)' }}
    >
      <div className="flex flex-col items-center space-y-4 p-6 rounded-lg bg-white shadow-lg border">
        {/* Spinner */}
        <div className="relative">
          <div className="w-12 h-12 border-4 border-blue-200 rounded-full animate-spin"></div>
          <div className="absolute top-0 left-0 w-12 h-12 border-4 border-transparent border-t-blue-600 rounded-full animate-spin"></div>
        </div>

        {/* Message */}
        <div className="text-center">
          <p className="text-lg font-medium text-gray-800">{message}</p>
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;
