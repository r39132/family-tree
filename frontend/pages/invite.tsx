import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import TopNav from '../components/TopNav';

type InviteItem = {
  code: string;
  active: boolean;
  used_by?: string;
  used_email?: string;
  used_at?: any;
};

export default function Invite(){
  const [error, setError] = useState<string|undefined>();
  const [count, setCount] = useState<number>(1);
  const [view, setView] = useState<'all'|'redeemed'|'unredeemed'>('all');
  const [invites, setInvites] = useState<InviteItem[]>([]);
  const [justCreated, setJustCreated] = useState<string[]>([]);

  async function loadInvites(v: 'all'|'redeemed'|'unredeemed' = view){
    try{
      const res = await api(`/auth/invites?view=${v}`);
      setInvites(res.invites || []);
    }catch(e:any){
      const msg = e?.message || '';
      if (msg.startsWith('404:')) {
        // Endpoint not available yet on backend; show empty list without error
        setInvites([]);
        setError(undefined);
        return;
      }
      setError(msg || 'Failed to load invites');
    }
  }

  useEffect(()=>{ loadInvites('all'); },[]);

  async function generate(){
    try{
      const res = await api(`/auth/invite?count=${count}`, { method:'POST' });
      const codes: string[] = res.invite_codes || [];
      setJustCreated(codes);
      await loadInvites('all');
      setView('all');
    }catch(e:any){
      const msg = e?.message || '';
      if (msg.startsWith('404:')){
        setError('Invites API not available. Please update and restart the backend.');
        return;
      }
      setError(msg || 'Failed to generate invites');
    }
  }

  const filtered = useMemo(()=>{
    return invites;
  }, [invites]);

  return (
    <div className="container">
      <TopNav />
      <div className="card">
        <h1>Invites</h1>
        {error && <p style={{color:'crimson'}}>{error}</p>}

        <div className="grid2">
          <div>
            <label>Tokens to Generate</label>
            <select value={count} onChange={e=>setCount(parseInt(e.target.value,10))}>
              {Array.from({length:10},(_,i)=>i+1).map(n=> <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div style={{display:'flex',alignItems:'flex-end',justifyContent:'flex-end'}}>
            <button className="btn" onClick={generate}>Generate Invite Token(s)</button>
          </div>
        </div>

        {justCreated.length>0 && (
          <div style={{marginTop:12}}>
            <b>New token(s):</b>
            <ul>
              {justCreated.map(c=> (
                <li key={c}><code>{c}</code> — <Link href={`/register?invite=${encodeURIComponent(c)}`}>Open registration</Link></li>
              ))}
            </ul>
          </div>
        )}

        <hr />

        <div className="bottombar">
          <div className="bottombar-left"></div>
          <div className="bottombar-right">
            <label style={{marginRight:8}}>View</label>
            <select value={view} onChange={async e=>{ const v=e.target.value as any; setView(v); await loadInvites(v); }}>
              <option value="all">All</option>
              <option value="redeemed">Redeemed</option>
              <option value="unredeemed">Unredeemed</option>
            </select>
          </div>
        </div>

        <div style={{overflowX:'auto', marginTop:12}}>
          <table style={{width:'100%', borderCollapse:'collapse'}}>
            <thead>
              <tr>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Token</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Redeemer Email</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Redeemer Username</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Redeemed At</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(row=>{
                const redeemed = !row.active;
                const dateStr = row.used_at ? String(row.used_at) : '';
                return (
                  <tr key={row.code}>
                    <td style={{padding:'8px'}}><code>{row.code}</code></td>
                    <td style={{padding:'8px'}}>{row.used_email || ''}</td>
                    <td style={{padding:'8px'}}>{row.used_by || ''}</td>
                    <td style={{padding:'8px'}}>{dateStr}</td>
                    <td style={{padding:'8px'}}>{redeemed ? 'Redeemed' : 'Unredeemed'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
