import { useEffect, useMemo, useState } from 'react';
import { Icons } from '../components/Icons';
import { api } from '../lib/api';
import MemberEditor from '../components/MemberEditor';
import TopNav from '../components/TopNav';
import { useRouter } from 'next/router';
import Modal from '../components/Modal';

export default function Home(){
  const [tree,setTree]=useState<any>({roots:[],members:[]});
  const [selected,setSelected]=useState<any|null>(null);
  const [moveChild,setMoveChild]=useState<string>('');
  const [moveParent,setMoveParent]=useState<string|undefined>(undefined);
  const router = useRouter();
  const [showInvalid, setShowInvalid] = useState(false);
  const [invalidMsgs, setInvalidMsgs] = useState<string[]>([]);

  // logout handled in TopNav

  async function load(){
    try{
      const data = await api('/tree');
      setTree(data);
    }catch{
      router.push('/login');
    }
  }

  useEffect(()=>{ load(); },[]);

  async function saveMember(m:any){
    // Editing only on this page
    if(m.id){
  // Minimal safeguard — client validation runs in MemberEditor
  const errs: string[] = [];
  if(!m.first_name?.trim()) errs.push('First name is required.');
  if(!m.last_name?.trim()) errs.push('Last name is required.');
  if(!m.dob?.trim()) errs.push('Date of Birth is required.');
  if(errs.length){ setInvalidMsgs(errs); setShowInvalid(true); return; }
  await api(`/tree/members/${m.id}`, {method:'PATCH', body:JSON.stringify(m)});
  setSelected(null);
  router.push('/');
    }
  }

  async function move(){
    await api('/tree/move',{method:'POST', body:JSON.stringify({child_id: moveChild, new_parent_id: moveParent || null})});
    setMoveChild(''); setMoveParent(undefined);
    await load();
  }

  async function remove(id:string){
    if(confirm('Are you sure you want to delete this member?')){
      await api(`/tree/members/${id}`, {method:'DELETE'});
      setSelected(null);
      await load();
    }
  }

  function Node({n}:{n:any}){
    const m = n.member;
    const s = n.spouse;
  const { View, Edit, Delete } = Icons;
    const nameEl = (x:any)=>{
      const deceased = !!x?.is_deceased;
      const style = deceased ? {color:'crimson'} : {};
      const asterisk = deceased ? '*' : '';
      return <b style={style}>{x?.first_name} {x?.last_name}{asterisk}</b>;
    };
    const dobText = (x:any)=> x?.dob ? x.dob : '';
    return (
      <li className="node">
        {nameEl(m)}{' '}<span className="small">({dobText(m)})</span>
        {s && (
          <>
            {' '}<span style={{opacity:0.6}}>&amp;</span>{' '}
            {nameEl(s)}{' '}<span className="small">({dobText(s)})</span>
          </>
        )}
        <div className="nav" style={{gap:8}}>
          <button className="btn secondary" title={`View ${m.first_name}`} onClick={()=>router.push(`/view/${m.id}`)}><View /></button>
          <button className="btn secondary" title={`Edit ${m.first_name}`} onClick={()=>router.push(`/edit/${m.id}`)}><Edit /></button>
          <button className="btn" title={`Delete ${m.first_name}`} onClick={()=>remove(m.id)}><Delete /></button>
          {s && (<span className="vsep" />)}
          {s && (
            <>
              <button className="btn secondary" title={`View ${s.first_name}`} onClick={()=>router.push(`/view/${s.id}`)}><View /></button>
              <button className="btn secondary" title={`Edit ${s.first_name}`} onClick={()=>router.push(`/edit/${s.id}`)}><Edit /></button>
              <button className="btn" title={`Delete ${s.first_name}`} onClick={()=>remove(s.id)}><Delete /></button>
            </>
          )}
        </div>
        {n.children?.length>0 && (
          <ul className="tree">
            {n.children
              .slice()
              .sort((a:any,b:any)=>{
                // Sort by child dob_ts ascending (birth order); fallback to name
                const at=a.member?.dob_ts || a.member?.dob || '';
                const bt=b.member?.dob_ts || b.member?.dob || '';
                if(at && bt){ return (new Date(at) as any) - (new Date(bt) as any); }
                const af=(a.member?.first_name||'').toLowerCase();
                const bf=(b.member?.first_name||'').toLowerCase();
                if(af<bf) return -1; if(af>bf) return 1;
                const al=(a.member?.last_name||'').toLowerCase();
                const bl=(b.member?.last_name||'').toLowerCase();
                if(al<bl) return -1; if(al>bl) return 1; return 0;
              })
              .map((c:any)=>(<Node key={c.member.id} n={c}/>))}
          </ul>
        )}
      </li>
    );
  }

  return (
    <div className="container">
      <TopNav />

    <div className="card">
  <h2>Tree ({tree.members?.length ?? 0})</h2>
        {tree.roots?.length ? (
          <ul className="tree">
            {tree.roots.map((r:any)=>(<Node key={r.member.id} n={r}/>))}
          </ul>
  ) : <p>No members yet. Click "Add member" to add the first member.</p>}
      </div>

  {/* Add member moved to /add */}

      <div className="card">
        <h2>Move Member</h2>
        <div className="grid2">
          <select value={moveChild} onChange={e=>setMoveChild(e.target.value)}>
            <option value="">Select child</option>
            {tree.members?.slice().sort((a:any,b:any)=>{
              const fa = (a.first_name||'').toLowerCase();
              const fb = (b.first_name||'').toLowerCase();
              if(fa<fb) return -1; if(fa>fb) return 1;
              const la = (a.last_name||'').toLowerCase();
              const lb = (b.last_name||'').toLowerCase();
              if(la<lb) return -1; if(la>lb) return 1; return 0;
            }).map((m:any)=>(<option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>))}
          </select>
          <select value={moveParent||''} onChange={e=>setMoveParent(e.target.value || undefined)}>
            <option value="">(Make root)</option>
            {tree.members?.slice().sort((a:any,b:any)=>{
              const fa = (a.first_name||'').toLowerCase();
              const fb = (b.first_name||'').toLowerCase();
              if(fa<fb) return -1; if(fa>fb) return 1;
              const la = (a.last_name||'').toLowerCase();
              const lb = (b.last_name||'').toLowerCase();
              if(la<lb) return -1; if(la>lb) return 1; return 0;
            }).map((m:any)=>(<option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>))}
          </select>
        </div>
        <div className="bottombar">
          <div className="bottombar-left"></div>
          <div className="bottombar-right">
            <button className="btn" onClick={move} disabled={!moveChild}>Move</button>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Add Spouse/Partner</h2>
        <AddSpouse members={tree.members||[]} onLinked={load} />
      </div>

  {/* Edit is handled on a dedicated page */}
      <Modal open={showInvalid} title="Please fix the following" onClose={()=>setShowInvalid(false)}>
        <ul>
          {invalidMsgs.map((m,i)=>(<li key={i}>{m}</li>))}
        </ul>
      </Modal>
    </div>
  );
}

function AddSpouse({members,onLinked}:{members:any[]; onLinked: ()=>void}){
  const [memberId, setMemberId] = useState('');
  const [partnerId, setPartnerId] = useState('');
  const canLink = memberId && partnerId && memberId !== partnerId;
  const sortedMembers = useMemo(()=> (members||[]).slice().sort((a:any,b:any)=>{
    const fa = (a.first_name||'').toLowerCase();
    const fb = (b.first_name||'').toLowerCase();
    if(fa<fb) return -1; if(fa>fb) return 1;
    const la = (a.last_name||'').toLowerCase();
    const lb = (b.last_name||'').toLowerCase();
    if(la<lb) return -1; if(la>lb) return 1; return 0;
  }), [members]);
  async function link(){
    if(!canLink) return;
    await api(`/tree/members/${memberId}/spouse`, { method:'POST', body: JSON.stringify({ spouse_id: partnerId }) });
    setMemberId(''); setPartnerId('');
    onLinked();
  }
  return (
    <>
      <div className="grid2">
        <select value={memberId} onChange={e=>setMemberId(e.target.value)}>
          <option value="">Select member</option>
          {sortedMembers.map((m:any)=>(<option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>))}
        </select>
        <select value={partnerId} onChange={e=>setPartnerId(e.target.value)}>
          <option value="">Select spouse/partner</option>
          {sortedMembers.filter((m:any)=>m.id!==memberId).map((m:any)=>(<option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>))}
        </select>
      </div>
      <div className="bottombar">
        <div className="bottombar-left"></div>
        <div className="bottombar-right">
          <button className="btn" onClick={link} disabled={!canLink}>Link</button>
        </div>
      </div>
    </>
  );
}
