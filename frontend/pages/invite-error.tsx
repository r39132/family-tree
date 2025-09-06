import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import SimpleTopNav from '../components/SimpleTopNav';

interface ErrorDetails {
  type: 'redeemed' | 'invalid' | 'expired' | 'unknown';
  message: string;
}

export default function InviteError() {
  const router = useRouter();
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!router.isReady) return;

    const { type, message } = router.query;

    // Handle URL parameters or default error
    if (type && message) {
      setErrorDetails({
        type: type as ErrorDetails['type'],
        message: String(message)
      });
    } else {
      // Default error when no specific details provided
      setErrorDetails({
        type: 'invalid',
        message: 'The invite link is invalid or has expired.'
      });
    }

    setIsLoading(false);
  }, [router.isReady, router.query]);

  const getErrorIcon = (type: string) => {
    switch (type) {
      case 'redeemed':
        return (
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
            <path d="M12 8v4"/>
            <path d="M12 16h.01"/>
          </svg>
        );
      case 'expired':
        return (
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12,6 12,12 16,14"/>
          </svg>
        );
      default:
        return (
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        );
    }
  };

  const getErrorTitle = (type: string) => {
    switch (type) {
      case 'redeemed':
        return 'Invite Already Used';
      case 'expired':
        return 'Invite Expired';
      case 'invalid':
        return 'Invalid Invite';
      default:
        return 'Invite Error';
    }
  };

  const getErrorDescription = (type: string) => {
    switch (type) {
      case 'redeemed':
        return 'This invite has already been used to create an account. If you have already registered, please proceed to login.';
      case 'expired':
        return 'This invite link has expired. Please request a new invite from the person who invited you.';
      case 'invalid':
        return 'This invite link is invalid or malformed. Please check the link and try again.';
      default:
        return 'There was an issue with your invite link. Please contact support for assistance.';
    }
  };

  if (isLoading) {
    return (
      <>
        <div className="container">
          <SimpleTopNav />
          <div className="card">
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <p>Loading...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="container">
        <SimpleTopNav />
        <div className="card">
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              {errorDetails && getErrorIcon(errorDetails.type)}
            </div>

            <h1 style={{ marginBottom: '1rem', color: '#374151' }}>
              {errorDetails && getErrorTitle(errorDetails.type)}
            </h1>

            <p style={{
              marginBottom: '1.5rem',
              color: '#6b7280',
              lineHeight: '1.6',
              maxWidth: '400px',
              margin: '0 auto 1.5rem auto'
            }}>
              {errorDetails?.message || (errorDetails && getErrorDescription(errorDetails.type))}
            </p>

            <div style={{
              display: 'flex',
              gap: '1rem',
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              {errorDetails?.type === 'redeemed' ? (
                <Link href="/login">
                  <button className="btn">Go to Login</button>
                </Link>
              ) : (
                <Link href="/">
                  <button className="btn">Go to Home</button>
                </Link>
              )}

              <Link href="/register">
                <button
                  className="btn"
                  style={{
                    backgroundColor: 'transparent',
                    color: '#6b7280',
                    border: '1px solid #d1d5db'
                  }}
                >
                  Try Different Invite
                </button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
