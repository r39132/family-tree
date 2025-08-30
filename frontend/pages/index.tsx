import { useEffect, useMemo, useState } from 'react';
import { Icons } from '../components/Icons';
import { api } from '../lib/api';
import MemberEditor from '../components/MemberEditor';
import TopNav from '../components/TopNav';
import { useRouter } from 'next/router';
import Modal from '../components/Modal';
import SearchableSelect from '../components/SearchableSelect';
import TreeCacheManager from '../lib/treeCache';
import CacheStatsDisplay from '../components/CacheStatsDisplay';

export default function Home(){
  const [tree,setTree]=useState<any>({roots:[],members:[]});
  const [selected,setSelected]=useState<any|null>(null);
  const [moveChild,setMoveChild]=useState<string>('');
  const [moveParent,setMoveParent]=useState<string|undefined>(undefined);
  const [unsaved, setUnsaved] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [recoverId, setRecoverId] = useState<string>('');
  const [showCacheStats, setShowCacheStats] = useState(false);
  const [config, setConfig] = useState<any>({ enable_map: false });

  function fmtVersionLabel(iso?: string, _count?: number, version?: number){
    if(!iso) return '';
    const d = new Date(iso);
    const locale = typeof window !== 'undefined' ? navigator.language : 'en-US';
    const date = d.toLocaleDateString(locale, { month: 'short', day: 'numeric', year: 'numeric' });
    const time = d.toLocaleTimeString(locale, { hour: 'numeric', minute: '2-digit' });
    const base = `${date} at ${time}`;
    return version !== undefined ? `${base} (v${version})` : base;
  }
  const router = useRouter();
  const [showInvalid, setShowInvalid] = useState(false);
  const [invalidMsgs, setInvalidMsgs] = useState<string[]>([]);

  // logout handled in TopNav

  async function load(){
    try{
      const cacheManager = TreeCacheManager.getInstance();

      // Load config
      const configData = await api('/config');
      setConfig(configData);

      // Try to get cached tree data first
      const cachedTree = cacheManager.getCachedTree();
      if (cachedTree) {
        setTree(cachedTree);
        // Still load versions and unsaved state (these are small and change frequently)
        const vs = await api('/tree/versions');
        setVersions(vs);
        const u = await api('/tree/unsaved');
        setUnsaved(!!u.unsaved);
        return;
      }

      // Cache miss - load fresh data
      const vs = await api('/tree/versions');
      setVersions(vs);
      const data = await api('/tree');

      // Cache the tree data
      cacheManager.setCachedTree(data);
      setTree(data);

      const u = await api('/tree/unsaved');
      setUnsaved(!!u.unsaved);
    }catch{
      router.push('/login');
    }
  }

  useEffect(()=>{ load(); },[]);
  // Navigation guard
  useEffect(()=>{
    const beforeUnload = (e: BeforeUnloadEvent)=>{
      if(!unsaved) return;
      e.preventDefault();
      e.returnValue = '';
    };
    const onRouteChangeStart = (url: string)=>{
      if(!unsaved) return;
      if(!confirm('You have unsaved changes. Leave without saving?')){
        // Cancel route change by pushing back to current path
        router.events.emit('routeChangeError');
        // eslint-disable-next-line @typescript-eslint/no-throw-literal
        throw 'routeChange aborted';
      }
    };
    window.addEventListener('beforeunload', beforeUnload);
    router.events.on('routeChangeStart', onRouteChangeStart);
    return ()=>{
      window.removeEventListener('beforeunload', beforeUnload);
      router.events.off('routeChangeStart', onRouteChangeStart);
    };
  },[unsaved]);

  async function saveMember(m:any){
    // Editing only on this page
    if(m.id){
  // Minimal safeguard — client validation runs in MemberEditor
  const errs: string[] = [];
  if(!m.first_name?.trim()) errs.push('First name is required.');
  if(!m.last_name?.trim()) errs.push('Last name is required.');
  if(!m.dob?.trim()) errs.push('Date of Birth is required.');
  if(errs.length){ setInvalidMsgs(errs); setShowInvalid(true); return; }

  const cacheManager = TreeCacheManager.getInstance();

  // Check if this update affects tree display
  if (cacheManager.shouldInvalidateForMemberUpdate(m)) {
    cacheManager.invalidateCache('data_changed');
  }

  await api(`/tree/members/${m.id}`, {method:'PATCH', body:JSON.stringify(m)});
  setSelected(null);
  router.push('/');
    }
  }

  async function move(){
  const cacheManager = TreeCacheManager.getInstance();
  cacheManager.invalidateCache('structure_changed');

  await api('/tree/move',{method:'POST', body:JSON.stringify({child_id: moveChild, new_parent_id: moveParent || null})});
    setMoveChild(''); setMoveParent(undefined);
  setUnsaved(true);
  await load();
  }

  async function remove(id:string){
    if(confirm('Are you sure you want to delete this member?')){
      const cacheManager = TreeCacheManager.getInstance();
      cacheManager.invalidateCache('structure_changed');

      await api(`/tree/members/${id}`, {method:'DELETE'});
      setSelected(null);
      setUnsaved(true);
      await load();
    }
  }

  async function saveTree(){
    const cacheManager = TreeCacheManager.getInstance();
    cacheManager.invalidateCache('structure_changed');

    const v = await api('/tree/save', { method:'POST' });
    setUnsaved(false);
    const vs = await api('/tree/versions');
    setVersions(vs);
  }

  async function recoverTree(){
    if(!recoverId) return;

    const cacheManager = TreeCacheManager.getInstance();
    cacheManager.invalidateCache('structure_changed');

    await api('/tree/recover', { method:'POST', body: JSON.stringify({ version_id: recoverId }) });
    setUnsaved(false);
    await load();
  }

  function Node({n}:{n:any}){
    const m = n.member;
    const s = n.spouse;
  const { View, Edit, Delete, Map } = Icons;
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
          {config.enable_map && m.residence_location && (
            <button className="btn secondary" title={`View ${m.first_name} on map`} onClick={()=>router.push(`/map?member=${m.id}`)}><Map /></button>
          )}
          <button className="btn" title={`Delete ${m.first_name}`} onClick={()=>remove(m.id)}><Delete /></button>
          {s && (<span className="vsep" />)}
          {s && (
            <>
              <button className="btn secondary" title={`View ${s.first_name}`} onClick={()=>router.push(`/view/${s.id}`)}><View /></button>
              <button className="btn secondary" title={`Edit ${s.first_name}`} onClick={()=>router.push(`/edit/${s.id}`)}><Edit /></button>
              {config.enable_map && s.residence_location && (
                <button className="btn secondary" title={`View ${s.first_name} on map`} onClick={()=>router.push(`/map?member=${s.id}`)}><Map /></button>
              )}
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ margin: 0 }}>Tree ({tree.members?.length ?? 0})</h2>
        <button
          className="btn secondary"
          onClick={() => setShowCacheStats(true)}
          style={{ fontSize: '12px', padding: '4px 8px' }}
          title="View cache settings and statistics"
        >
          📊 Cache
        </button>
      </div>
        {unsaved && (
          <p style={{color:'crimson', marginTop:0}}>You have unsaved changes. Please click Save to create a new version.</p>
        )}
        <div className="bottombar" style={{marginTop:8}}>
          <div className="bottombar-left">
            <button className="btn" disabled={!unsaved} title={!unsaved ? 'No unsaved changes' : 'Save current tree as a new version'} onClick={saveTree}>Save Tree</button>
          </div>
          <div className="bottombar-right" style={{display:'flex', gap:8, alignItems:'center'}}>
            <select value={recoverId} onChange={e=>setRecoverId(e.target.value)}>
              <option value="">Select version…</option>
              {versions.map((v:any)=> (<option key={v.id} value={v.id}>{fmtVersionLabel(v.created_at, undefined, v.version)}</option>))}
            </select>
            <button className="btn" disabled={!recoverId} onClick={recoverTree}>Recover</button>
          </div>
        </div>
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
          <SearchableSelect
            options={(tree.members||[]).slice().sort((a:any,b:any)=>{
              const fa = (a.first_name||'').toLowerCase();
              const fb = (b.first_name||'').toLowerCase();
              if (fa<fb) return -1; if (fa>fb) return 1;
              const la = (a.last_name||'').toLowerCase();
              const lb = (b.last_name||'').toLowerCase();
              if (la<lb) return -1; if (la>lb) return 1; return 0;
            }).map((m:any)=>({ value: m.id, label: `${m.first_name} ${m.last_name}` }))}
            value={moveChild}
            onChange={setMoveChild}
            placeholder="Select child"
            ariaLabel="Select child"
          />
          <SearchableSelect
            options={(tree.members||[]).slice().sort((a:any,b:any)=>{
              const fa = (a.first_name||'').toLowerCase();
              const fb = (b.first_name||'').toLowerCase();
              if (fa<fb) return -1; if (fa>fb) return 1;
              const la = (a.last_name||'').toLowerCase();
              const lb = (b.last_name||'').toLowerCase();
              if (la<lb) return -1; if (la>lb) return 1; return 0;
            }).map((m:any)=>({ value: m.id, label: `${m.first_name} ${m.last_name}` }))}
            value={moveParent || ''}
            onChange={(v)=>setMoveParent(v || undefined)}
            placeholder="Select parent (or make root)"
            ariaLabel="Select new parent"
            emptyOption={{ value: '', label: '(Make root)' }}
          />
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
        <AddSpouse members={tree.members||[]} onLinked={async()=>{ await load(); setUnsaved(true); }} />
      </div>

  {/* Edit is handled on a dedicated page */}
      <Modal open={showInvalid} title="Please fix the following" onClose={()=>setShowInvalid(false)}>
        <ul>
          {invalidMsgs.map((m,i)=>(<li key={i}>{m}</li>))}
        </ul>
      </Modal>

      <CacheStatsDisplay
        show={showCacheStats}
        onClose={() => setShowCacheStats(false)}
      />
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
