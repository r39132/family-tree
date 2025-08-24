import { useState } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import { useRouter } from 'next/router';
import SimpleTopNav from '../components/SimpleTopNav';

export default function Login(){
  const [username,setUsername]=useState('');
  const [password,setPassword]=useState('');
  const [showPass,setShowPass]=useState(false);
  const [remember,setRemember]=useState(true);
  const [error,setError]=useState<string|null>(null);
  const router = useRouter();

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
    
    // Validate form before submission
    if (!isFormValid) {
      setError('Please fill in both username and password.');
      return;
    }

    try{
      const res = await api('/auth/login',{method:'POST', body:JSON.stringify({username,password})});
      localStorage.setItem('token', res.access_token);
      if(remember) localStorage.setItem('remember','1'); else localStorage.removeItem('remember');
  router.push('/');
    }catch(err:any){
      setError(getErrorMessage(err.message || 'An unexpected error occurred'));
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
          <label><input type="checkbox" className="checkbox" checked={remember} onChange={e=>setRemember(e.target.checked)}/>Remember me</label>
          <div className="bottombar">
            <div className="bottombar-left">
              <Link href="/forgot">Forgot password?</Link>
              <Link href="/register">Register</Link>
            </div>
            <div className="bottombar-right">
              <button 
                className={`btn ${!isFormValid ? 'disabled' : ''}`} 
                type="submit" 
                disabled={!isFormValid}
                title={!isFormValid ? 'Please fill in all fields' : 'Login to your account'}
              >
                Login
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
    </>
  );
}
