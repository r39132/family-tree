import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import { useRouter } from 'next/router';
import SimpleTopNav from '../components/SimpleTopNav';

export default function Reset(){
  const router = useRouter();
  const [username,setUsername]=useState('');
  const [token,setToken]=useState('');
  const [p1,setP1]=useState('');
  const [p2,setP2]=useState('');
  const [showP1, setShowP1] = useState(false);
  const [showP2, setShowP2] = useState(false);
  const [ok,setOk]=useState(false);
  const [error,setError]=useState<string|null>(null);

  useEffect(()=>{
    if(router.isReady){
      const t = (router.query.token as string) || '';
      const u = (router.query.username as string) || '';
      setToken(t); setUsername(u);
    }
  },[router.isReady, router.query]);

  async function submit(e:any){
    e.preventDefault();
    try{
      await api('/auth/reset',{method:'POST', body:JSON.stringify({username, new_password:p1, confirm_password:p2, token})});
      setOk(true);
      setTimeout(()=> router.push('/login'), 1200);
    }catch(err:any){
      setError(err.message);
    }
  }

  return (
    <>
      <div className="container">
        <SimpleTopNav />
        <div className="card">
          <h1>Reset password</h1>
          {ok ? <p>Password updated. Redirecting to login…</p> : (
          <form onSubmit={submit}>
            {error && <p style={{color:'crimson'}}>{error}</p>}
            <input className="input" placeholder="Username" value={username} onChange={e=>setUsername(e.target.value)}/>
            <div className="input-wrap">
              <input
                id="new-password"
                className="input"
                type={showP1 ? 'text' : 'password'}
                placeholder="New password"
                value={p1}
                onChange={e=>setP1(e.target.value)}
              />
              <button
                type="button"
                className="toggle-pass"
                aria-label={showP1 ? 'Hide password' : 'Show password'}
                aria-pressed={showP1}
                aria-controls="new-password"
                title={showP1 ? 'Hide password' : 'Show password'}
                onClick={()=>setShowP1(v=>!v)}
              >
                {showP1 ? (
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
                id="confirm-password"
                className="input"
                type={showP2 ? 'text' : 'password'}
                placeholder="Confirm password"
                value={p2}
                onChange={e=>setP2(e.target.value)}
              />
              <button
                type="button"
                className="toggle-pass"
                aria-label={showP2 ? 'Hide password' : 'Show password'}
                aria-pressed={showP2}
                aria-controls="confirm-password"
                title={showP2 ? 'Hide password' : 'Show password'}
                onClick={()=>setShowP2(v=>!v)}
              >
                {showP2 ? (
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
                <button className="btn" type="submit">Set password</button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
    </>
  );
}
