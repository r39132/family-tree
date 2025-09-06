import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import TopNav from '../components/TopNav';

type InviteItem = {
  code: string;
  status?: 'available'|'invite-sent'|'redeemed';
  // legacy booleans from older backend responses
  active?: boolean;
  used_by?: string;
  used_email?: string;
  used_at?: any;
  redeemed_at?: any;  // New field for redemption date
  sent_email?: string;
  sent_at?: any;
  invited_at?: any;   // New field for invite sent date
};

export default function Invite(){
  const [error, setError] = useState<string|undefined>();
  const [count, setCount] = useState<number>(1);
  const [view, setView] = useState<'all'|'redeemed'|'available'|'invite-sent'>('all');
  const [invites, setInvites] = useState<InviteItem[]>([]);
  const [justCreated, setJustCreated] = useState<string[]>([]);

  // Helper function to format dates in user-friendly format
  // Dates are stored in GMT and should be displayed in user's local timezone
  const formatDate = (dateValue: any): string => {
    if (!dateValue) return '';

    try {
      let date: Date;

      // Handle Firestore timestamp format or ISO string
      if (typeof dateValue === 'object' && dateValue.seconds) {
        // Firestore timestamp format - already in UTC
        date = new Date(dateValue.seconds * 1000);
      } else if (typeof dateValue === 'string') {
        date = new Date(dateValue);
      } else {
        date = new Date(dateValue);
      }

      // Check if date is valid
      if (isNaN(date.getTime())) return String(dateValue);

      // Format in user's local timezone with explicit timezone display
      return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'  // Show timezone abbreviation
      });
    } catch (e) {
      console.error('Error formatting date:', e, dateValue);
      return String(dateValue);
    }
  };

  async function loadInvites(v: 'all'|'redeemed'|'available'|'invite-sent' = view){
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

  async function deleteInvite(code: string){
    if (!confirm(`Are you sure you want to delete invite ${code}? This cannot be undone.`)) {
      return;
    }

    try{
      await api(`/auth/invites/${encodeURIComponent(code)}`, { method: 'DELETE' });
      await loadInvites(view); // Refresh the current view
      setError(undefined);
    }catch(e:any){
      const msg = e?.message || '';
      setError(msg || 'Failed to delete invite');
    }
  }

  async function resendInvite(code: string, email: string){
    if (!email) {
      setError('No email address found for this invite');
      return;
    }

    try{
      await api(`/auth/invites/${encodeURIComponent(code)}/email`, {
        method: 'POST',
        body: JSON.stringify({ email })
      });
      await loadInvites(view); // Refresh to show updated sent_at time
      setError(undefined);
    }catch(e:any){
      const msg = e?.message || '';
      setError(msg || 'Failed to resend invite');
    }
  }

  const getStatus = (row: InviteItem): 'available'|'invite-sent'|'redeemed' => {
    if (row.status) return row.status;
    // Fallback for legacy shape: derive from fields; ignore active if redeemed fields are present
    if (row.used_by) return 'redeemed';
    if (row.sent_email) return 'invite-sent';
    // If legacy 'active' exists and is false, treat as redeemed
    if (row.active === false) return 'redeemed';
    return 'available';
  };

  const filtered = useMemo(()=>{
    let out = invites;
    if(view === 'redeemed') out = invites.filter(i=>getStatus(i) === 'redeemed');
    if(view === 'available') out = invites.filter(i=>getStatus(i) === 'available');
    if(view === 'invite-sent') out = invites.filter(i=>getStatus(i) === 'invite-sent');
    return out;
  }, [invites, view]);
  const countLabel = useMemo(()=>{
  if(view === 'redeemed') return 'redeemed';
  if(view === 'available') return 'available';
  if(view === 'invite-sent') return 'invite(s) sent';
    return 'total';
  }, [view]);

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
              <option value="available">Available</option>
              <option value="invite-sent">Invite Sent</option>
            </select>
          </div>
        </div>

        <div style={{marginTop:8}}>
          <span className="badge">{filtered.length}</span> {countLabel} token(s)
        </div>

        <div style={{overflowX:'auto', marginTop:12}}>
          <table style={{width:'100%', borderCollapse:'collapse'}}>
            <thead>
              <tr>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Token</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Email</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Username</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Invited At</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Redeemed At</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Status</th>
                <th style={{textAlign:'left', borderBottom:'1px solid #eaeaea', padding:'8px'}}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(row=>{
                const st = getStatus(row);

                // Format invited date (when invite was sent)
                let invitedDate = '';
                if (row.invited_at) {
                  invitedDate = formatDate(row.invited_at);
                } else if (row.sent_at) {
                  // Fallback to legacy sent_at field
                  invitedDate = formatDate(row.sent_at);
                }

                // Format redeemed date (when invite was used)
                let redeemedDate = '';
                if (row.redeemed_at) {
                  redeemedDate = formatDate(row.redeemed_at);
                } else if (row.used_at) {
                  // Fallback to legacy used_at field
                  redeemedDate = formatDate(row.used_at);
                }

                const status = st === 'redeemed' ? 'Redeemed' : (st === 'invite-sent' ? 'Invite Sent' : 'Available');
                return (
                  <tr key={row.code}>
                    <td style={{padding:'8px'}}><code>{row.code}</code></td>
                    <td style={{padding:'8px'}}>{row.used_email || row.sent_email || ''}</td>
                    <td style={{padding:'8px'}}>{row.used_by || ''}</td>
                    <td style={{padding:'8px'}}>{invitedDate}</td>
                    <td style={{padding:'8px'}}>{redeemedDate}</td>
                    <td style={{padding:'8px'}}>{status}</td>
                    <td style={{padding:'8px'}}>
                      {st === 'available' && (
                        <>
                          <Link href={`/invite/email-link?code=${encodeURIComponent(row.code)}`}>Email Registration Link</Link>
                          <span style={{margin: '0 8px'}}>|</span>
                          <button
                            onClick={() => deleteInvite(row.code)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#dc2626',
                              cursor: 'pointer',
                              textDecoration: 'underline',
                              fontSize: 'inherit'
                            }}
                          >
                            Delete
                          </button>
                        </>
                      )}
                      {st === 'invite-sent' && (
                        <>
                          <button
                            onClick={() => resendInvite(row.code, row.sent_email || '')}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#2563eb',
                              cursor: 'pointer',
                              textDecoration: 'underline',
                              fontSize: 'inherit'
                            }}
                          >
                            Resend
                          </button>
                          <span style={{margin: '0 8px'}}>|</span>
                          <button
                            onClick={() => deleteInvite(row.code)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#dc2626',
                              cursor: 'pointer',
                              textDecoration: 'underline',
                              fontSize: 'inherit'
                            }}
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </td>
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
