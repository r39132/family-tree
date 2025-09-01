import { AppProps } from 'next/app';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import '../styles.css';

// Public routes that don't require authentication
const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/forgot',
  '/reset',
  '/login.redirect',
  '/index.redirect'
];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      if (typeof window === 'undefined') return;

      const token = localStorage.getItem('token');
      const currentPath = router.pathname;

      // Check if current route is public
      const isPublicRoute = PUBLIC_ROUTES.includes(currentPath);

      if (!token && !isPublicRoute) {
        // No token and trying to access protected route - redirect to login
        router.replace('/login');
        return;
      }

      if (token && !isPublicRoute) {
        // For protected routes, validate the token by making a test API call
        try {
          const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";
          const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (!response.ok) {
            // Token is invalid, remove it and redirect to login
            localStorage.removeItem('token');
            router.replace('/login');
            return;
          }

          setIsAuthenticated(true);
        } catch (error) {
          // Network error or invalid token - redirect to login
          localStorage.removeItem('token');
          router.replace('/login');
          return;
        }
      }

      setIsLoading(false);
    };

    // Wait for router to be ready
    if (router.isReady) {
      checkAuth();
    }
  }, [router.isReady, router.pathname]);

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontFamily: 'system-ui, sans-serif'
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  return <>{children}</>;
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthGuard>
      <Component {...pageProps} />
    </AuthGuard>
  );
}
