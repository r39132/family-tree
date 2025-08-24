import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import { useRouter } from 'next/router';
import SimpleTopNav from '../components/SimpleTopNav';

export default function Register(){
  const [invite_code,setInvite]=useState('');
  const [username,setUsername]=useState('');
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [confirm,setConfirm]=useState('');
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error,setError]=useState<string|null>(null);
  const router = useRouter();

  // Prefill invite from query once ready
  useEffect(()=>{
    if(!router.isReady) return;
    const q = router.query as { invite?: string };
    if (q.invite && !invite_code) {
      setInvite(String(q.invite));
    }
  }, [router.isReady, router.query, invite_code]);

  function isValidEmail(v:string){
    // Simple email regex similar to MemberEditor
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  }

  async function submit(e:any){
    e.preventDefault();
    // Basic client validation
    if(!invite_code.trim()||!username.trim()||!email.trim()||!password.trim()||!confirm.trim()){
      setError('All fields are required.');
      return;
    }
    if(!isValidEmail(email)){
      setError('Please enter a valid email address.');
      return;
    }
    if(password!==confirm){
      setError('Passwords do not match.');
      return;
    }
    try{
      await api('/auth/register',{method:'POST', body:JSON.stringify({invite_code,username,email,password})});
      router.push('/login');
    }catch(err:any){
      setError(err.message);
    }
  }

  return (
    <>
      <div className="container">
        <SimpleTopNav />
        <div className="card">
          <h1>Register</h1>
          {error && <p style={{color:'crimson'}}>{error}</p>}
          <form onSubmit={submit}>
          <input className="input" placeholder="Invite Code" value={invite_code} onChange={e=>setInvite(e.target.value)}/>
          <input className="input" placeholder="Username" value={username} onChange={e=>setUsername(e.target.value)}/>
          <input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)}/>
          <div className="input-wrap">
            <input
              id="reg-password"
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
              aria-pressed={showPass}
              aria-controls="reg-password"
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
          <div className="input-wrap">
            <input
              id="reg-confirm"
              className="input"
              type={showConfirm ? 'text' : 'password'}
              placeholder="Confirm Password"
              value={confirm}
              onChange={e=>setConfirm(e.target.value)}
            />
            <button
              type="button"
              className="toggle-pass"
              aria-label={showConfirm ? 'Hide password' : 'Show password'}
              aria-pressed={showConfirm}
              aria-controls="reg-confirm"
              title={showConfirm ? 'Hide password' : 'Show password'}
              onClick={()=>setShowConfirm(v=>!v)}
            >
              {showConfirm ? (
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
          <div className="bottombar">
            <div className="bottombar-left">
              <Link href="/login">Back to login</Link>
            </div>
            <div className="bottombar-right">
              <button className="btn" type="submit">Create account</button>
            </div>
          </div>
        </form>
      </div>
    </div>
    </>
  );
}
