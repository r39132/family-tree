import { useState } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';

export default function Forgot(){
  const [username,setUsername]=useState('');
  const [email,setEmail]=useState('');
  const [ok,setOk]=useState(false);
  const [error,setError]=useState<string|null>(null);

  async function submit(e:any){
    e.preventDefault();
    try{
      await api('/auth/forgot',{method:'POST', body:JSON.stringify({username,email})});
      setOk(true);
    }catch(err:any){
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h1>Password recovery</h1>
  {ok ? <p>Check your email for a reset link (in development with USE_EMAIL_IN_DEV=true, check the backend logs).</p> : (
          <form onSubmit={submit}>
            {error && <p style={{color:'crimson'}}>{error}</p>}
            <input className="input" placeholder="Username" value={username} onChange={e=>setUsername(e.target.value)}/>
            <input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)}/>
            <div className="bottombar">
              <div className="bottombar-left">
                <Link href="/login">Back to login</Link>
              </div>
              <div className="bottombar-right">
                <button className="btn" type="submit">Send reset</button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
