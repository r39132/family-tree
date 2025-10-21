import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import { useRouter } from 'next/router';
import SimpleTopNav from '../components/SimpleTopNav';
import LoadingOverlay from '../components/LoadingOverlay';

interface FamilySpace {
  id: string;
  name: string;
  description?: string;
}

export default function Login(){
  const [username,setUsername]=useState('');
  const [password,setPassword]=useState('');
  const [selectedSpace,setSelectedSpace]=useState('');
  const [availableSpaces,setAvailableSpaces]=useState<FamilySpace[]>([]);
  const [showPass,setShowPass]=useState(false);
  const [remember,setRemember]=useState(true);
  const [error,setError]=useState<string|null>(null);
  const [loading,setLoading]=useState(false);
  const router = useRouter();

  // Fetch available family spaces on component mount
  useEffect(() => {
    async function fetchSpaces() {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";
        const response = await fetch(`${API_BASE}/spaces`);
        if (response.ok) {
          const spaces = await response.json();
          setAvailableSpaces(spaces);
          // If there's only one available space, pre-select it to avoid showing an "automatic" placeholder
          if (Array.isArray(spaces) && spaces.length === 1) {
            setSelectedSpace(spaces[0].id);
          }
        }
      } catch (err) {
        console.error('Failed to fetch family spaces:', err);
        // Set default spaces if fetch fails
        setAvailableSpaces([
          { id: 'demo', name: 'Demo' },
          { id: 'karunakaran', name: 'Karunakaran' },
          { id: 'anand', name: 'Anand' },
          { id: 'kullatira', name: 'Kullatira' }
        ]);
      }
    }
    fetchSpaces();
  }, []);

  // Check if form is valid (all required fields filled)
  const isFormValid = username.trim() !== '' && password.trim() !== '';

  function getErrorMessage(errorText: string): string {
    // Convert generic error messages to user-friendly ones
    if (errorText.includes('Failed to fetch') || errorText.includes('fetch')) {
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    }
    if (errorText.includes('Invalid credentials') || errorText.includes('401')) {
      return 'Invalid username or password. Please check your credentials and try again.';
    }
    if (errorText.includes('400')) {
      return 'Please check your username and password format.';
    }
    if (errorText.includes('500')) {
      return 'Server error. Please try again later or contact support.';
    }
    // Return the original message if no specific pattern matches
    return errorText;
  }

  async function submit(e:any){
    e.preventDefault();

    // Clear any previous errors
    setError(null);
    setLoading(true);

    // Validate form before submission
    if (!isFormValid) {
      setError('Please fill in all required fields.');
      setLoading(false);
      return;
    }

    try{
      // Use direct fetch instead of api() to handle eviction errors specifically
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";
      const bodyPayload: Record<string, string> = {
        username,
        password,
      };

      if (selectedSpace.trim()) {
        bodyPayload.space_id = selectedSpace.trim();
      }

      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(bodyPayload)
      });

      if (!response.ok) {
        const errorText = await response.text();

        // Handle specific eviction error
        if (response.status === 403 && errorText.includes('evicted')) {
          setError('Your account has been evicted. Please contact an administrator.');
          setLoading(false);
          return;
        }

        // Handle other errors with user-friendly messages
        if (response.status === 401) {
          setError('Invalid username or password. Please check your credentials and try again.');
          setLoading(false);
          return;
        }

        // Handle space-related errors
        if (response.status === 400 && errorText.includes('space')) {
          setError('Selected family space is not available. Please choose another space.');
          setLoading(false);
          return;
        }

        // Generic error handling
        throw new Error(`${response.status}: ${errorText}`);
      }

      const res = await response.json();
      localStorage.setItem('token', res.access_token);
      if(remember) localStorage.setItem('remember','1'); else localStorage.removeItem('remember');
      router.push('/');
    }catch(err:any){
      setError(getErrorMessage(err.message || 'An unexpected error occurred'));
      setLoading(false);
    }
  }

  return (
    <>
      <div className="container">
        <SimpleTopNav />
        <div className="card">
          <h1>Login</h1>
          {error && <p style={{color:'crimson'}}>{error}</p>}
          <form onSubmit={submit}>
            <label htmlFor="username">Username</label>
            <input id="username" className="input" placeholder="Username" value={username} onChange={e=>setUsername(e.target.value)}/>
            <label htmlFor="password">Password</label>
            <div className="input-wrap">
              <input
                id="password"
                className="input"
                type={showPass ? 'text' : 'password'}
                placeholder="Password"
                value={password}
                onChange={e=>setPassword(e.target.value)}
              />
              <button
                type="button"
                className="toggle-pass"
                aria-label={showPass ? 'Hide password' : 'Show password'}
                title={showPass ? 'Hide password' : 'Show password'}
                onClick={()=>setShowPass(v=>!v)}
              >
                {showPass ? (
                  // Eye off icon
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-5 0-9.27-3.11-11-8 1.02-2.94 3.07-5.29 5.65-6.71" />
                    <path d="M1 1l22 22" />
                    <path d="M9.88 9.88A3 3 0 0 0 12 15a3 3 0 0 0 2.12-.88" />
                    <path d="M14.12 14.12L9.88 9.88" />
                    <path d="M10.73 5.08A10.94 10.94 0 0 1 12 4c5 0 9.27 3.11 11 8-.54 1.56-1.4 2.96-2.5 4.12" />
                  </svg>
                ) : (
                  // Eye icon
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
            {/* Only show Family Space dropdown if there are multiple spaces available */}
            {availableSpaces.length > 1 && (
              <>
                <label htmlFor="familySpace">Family Space (optional)</label>
                <select
                  id="familySpace"
                  className="input"
                  value={selectedSpace}
                  onChange={e=>setSelectedSpace(e.target.value)}
                  title="Select your family space"
                >
                  {/*
                    Empty value means: don't send a space_id to the backend and let the server
                    pick the user's last accessed/current space automatically.
                  */}
                  <option value="">Use last accessed space (automatic)</option>
                  {availableSpaces.map(space => (
                    <option key={space.id} value={space.id}>
                      {space.name}
                      {space.description && ` - ${space.description}`}
                    </option>
                  ))}
                </select>
              </>
            )}
            {/* Show read-only family space name when there's only one space */}
            {availableSpaces.length === 1 && (
              <>
                <label htmlFor="familySpace">Family Space</label>
                <div
                  className="input"
                  style={{
                    backgroundColor: '#f5f5f5',
                    color: '#666',
                    cursor: 'default'
                  }}
                  title={`You will log into: ${availableSpaces[0].name}`}
                >
                  {availableSpaces[0].name}
                  {availableSpaces[0].description && ` - ${availableSpaces[0].description}`}
                </div>
              </>
            )}
          <label><input type="checkbox" className="checkbox" checked={remember} onChange={e=>setRemember(e.target.checked)}/>Remember me</label>
          <div className="bottombar">
            <div className="bottombar-left">
              <Link href="/forgot">Forgot password?</Link>
              <Link href="/register">Register</Link>
            </div>
            <div className="bottombar-right">
              <button
                className={`btn ${!isFormValid || loading ? 'disabled' : ''}`}
                type="submit"
                disabled={!isFormValid || loading}
                title={!isFormValid ? 'Please fill in all fields' : loading ? 'Logging in...' : 'Login to your account'}
              >
                {loading ? 'Logging in...' : 'Login'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Loading Overlay */}
      <LoadingOverlay
        isLoading={loading}
        message="Logging in..."
        transparent={true}
      />
    </div>
    </>
  );
}
