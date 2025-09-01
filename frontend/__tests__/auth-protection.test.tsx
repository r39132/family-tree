/**
 * Integration tests for authentication protection
 *
 * This file tests that:
 * 1. Protected pages redirect unauthenticated users to login
 * 2. Authenticated users can access protected pages
 * 3. Public pages remain accessible without authentication
 */

// Mock localStorage for testing
const mockLocalStorage = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => store[key] = value,
    removeItem: (key: string) => delete store[key],
    clear: () => store = {},
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock Next.js router
const mockRouter = {
  pathname: '/',
  isReady: true,
  replace: jest.fn(),
  push: jest.fn(),
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

import { render, waitFor } from '@testing-library/react';
import { AuthGuard } from '../pages/_app';

describe('Authentication Protection', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
    mockRouter.replace.mockClear();
    mockRouter.push.mockClear();
    mockRouter.pathname = '/';
  });

  describe('Protected Routes', () => {
    const protectedRoutes = ['/', '/add', '/events', '/map', '/invite', '/edit/123', '/view/123'];

    protectedRoutes.forEach(route => {
      it(`should redirect unauthenticated users from ${route} to login`, async () => {
        mockRouter.pathname = route;

        render(
          <AuthGuard>
            <div>Protected Content</div>
          </AuthGuard>
        );

        await waitFor(() => {
          expect(mockRouter.replace).toHaveBeenCalledWith('/login');
        });
      });

      it(`should allow authenticated users to access ${route}`, async () => {
        mockLocalStorage.setItem('token', 'valid-jwt-token');
        mockRouter.pathname = route;

        const { getByText } = render(
          <AuthGuard>
            <div>Protected Content</div>
          </AuthGuard>
        );

        await waitFor(() => {
          expect(getByText('Protected Content')).toBeInTheDocument();
          expect(mockRouter.replace).not.toHaveBeenCalled();
        });
      });
    });
  });

  describe('Public Routes', () => {
    const publicRoutes = ['/login', '/register', '/forgot', '/reset', '/login.redirect', '/index.redirect'];

    publicRoutes.forEach(route => {
      it(`should allow unauthenticated users to access ${route}`, async () => {
        mockRouter.pathname = route;

        const { getByText } = render(
          <AuthGuard>
            <div>Public Content</div>
          </AuthGuard>
        );

        await waitFor(() => {
          expect(getByText('Public Content')).toBeInTheDocument();
          expect(mockRouter.replace).not.toHaveBeenCalled();
        });
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner while checking authentication', () => {
      mockRouter.isReady = false;

      const { getByText } = render(
        <AuthGuard>
          <div>Content</div>
        </AuthGuard>
      );

      expect(getByText('Loading...')).toBeInTheDocument();
    });
  });
});
