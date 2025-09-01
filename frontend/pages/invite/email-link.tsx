import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import TopNav from '../../components/TopNav';
import { publicApi } from '../../lib/api';

export default function EmailInviteLink(){
  const router = useRouter();
  const { code } = router.query as { code?: string };
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string|undefined>();
  const [ok, setOk] = useState(false);

  useEffect(()=>{
    if(!router.isReady) return;
    if(!code){ setError('Missing invite code'); }
  },[router.isReady, code]);

  async function submit(e:any){
    e.preventDefault();
    setError(undefined);
    if(!email.trim()) { setError('Email is required'); return; }
    try{
      await publicApi(`/auth/public/invites/${encodeURIComponent(String(code))}/email`, { method:'POST', body: JSON.stringify({ email }) });
      setOk(true);
      setTimeout(()=>{ router.push('/invite'); }, 800);
    }catch(e:any){ setError(e?.message || 'Failed to send email'); }
  }

  return (
    <div className="container">
      <TopNav />
      <div className="card">
        <h1>Email Registration Link</h1>
        {code && <p>Invite token: <code>{code}</code></p>}
        {ok ? (
          <p>Invitation email queued. Redirecting…</p>
        ) : (
          <form onSubmit={submit}>
            {error && <p style={{color:'crimson'}}>{error}</p>}
            <label>Email<input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} /></label>
            <div className="bottombar">
              <div className="bottombar-left"></div>
              <div className="bottombar-right">
                <button className="btn secondary" type="button" onClick={()=>router.push('/invite')}>Cancel</button>
                <button className="btn" type="submit">Send</button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
