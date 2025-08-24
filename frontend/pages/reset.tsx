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
            <input className="input" type="password" placeholder="New password" value={p1} onChange={e=>setP1(e.target.value)}/>
            <input className="input" type="password" placeholder="Confirm password" value={p2} onChange={e=>setP2(e.target.value)}/>
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
