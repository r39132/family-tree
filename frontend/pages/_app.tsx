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
    const checkAuth = () => {
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

      if (token) {
        setIsAuthenticated(true);
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
