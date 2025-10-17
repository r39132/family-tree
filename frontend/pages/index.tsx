import { useEffect, useMemo, useState } from 'react';
import { Icons } from '../components/Icons';
import { api } from '../lib/api';
import MemberEditor from '../components/MemberEditor';
import TopNav from '../components/TopNav';
import { useRouter } from 'next/router';
import Modal from '../components/Modal';
import SearchableSelect from '../components/SearchableSelect';
import LoadingOverlay from '../components/LoadingOverlay';
import { isEligibleForMarriage } from '../lib/dateUtils';
import ProfilePicture from '../components/ProfilePicture';

export default function Home(){
  const [tree,setTree]=useState<any>({roots:[],members:[]});
  const [selected,setSelected]=useState<any|null>(null);
  const [moveChild,setMoveChild]=useState<string>('');
  const [moveParent,setMoveParent]=useState<string|undefined>(undefined);
  const [unsaved, setUnsaved] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [recoverId, setRecoverId] = useState<string>('');
  const [config, setConfig] = useState<any>({ enable_map: false });
  const [treeView, setTreeView] = useState<'standard' | 'minimal' | 'horizontal' | 'cards'>('standard');
  const [loading, setLoading] = useState(true);
  const [operationLoading, setOperationLoading] = useState(false);

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
    setLoading(true);
    try{
      // Load config
      const configData = await api('/config');
      setConfig(configData);

      // Load versions and tree data
      const vs = await api('/tree/versions');
      setVersions(vs);
      const data = await api('/tree');
      setTree(data);

      const u = await api('/tree/unsaved');
      setUnsaved(!!u.unsaved);
    }catch{
      router.push('/login');
    } finally {
      setLoading(false);
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

  await api(`/tree/members/${m.id}`, {method:'PATCH', body:JSON.stringify(m)});
  setSelected(null);
  router.push('/');
    }
  }

  async function move(){
    setOperationLoading(true);
    try {
      await api('/tree/move',{method:'POST', body:JSON.stringify({child_id: moveChild, new_parent_id: moveParent || null})});
      setMoveChild(''); setMoveParent(undefined);
      setUnsaved(true);
      await load();
    } finally {
      setOperationLoading(false);
    }
  }

  async function remove(id:string){
    if(confirm('Are you sure you want to delete this member?')){
      setOperationLoading(true);
      try {
        await api(`/tree/members/${id}`, {method:'DELETE'});
        setSelected(null);
        setUnsaved(true);
        await load();
      } finally {
        setOperationLoading(false);
      }
    }
  }

  async function saveTree(){
    setOperationLoading(true);
    try {
      const v = await api('/tree/save', { method:'POST' });
      setUnsaved(false);
      alert(`Tree saved! Version ${v.version}.`);
      await load();
    } finally {
      setOperationLoading(false);
    }
  }

  async function recoverTree(){
    setOperationLoading(true);
    try {
      await api('/tree/recover',{method:'POST',body:JSON.stringify({version_id:recoverId})});
      setRecoverId('');
      setUnsaved(false);
      alert('Tree recovered from selected version.');
      await load();
    } finally {
      setOperationLoading(false);
    }
  }

  function Node({n}:{n:any}){
    const m = n.member;
    const s = n.spouse;
  const { View, Edit, Delete, Map } = Icons;
    const nameEl = (x:any)=>{
      const deceased = !!x?.is_deceased;
      const style = deceased ? {color:'crimson'} : {};
      const asterisk = deceased ? '*' : '';
      let nameText;
      if (treeView === 'minimal') {
        nameText = `${x?.first_name || ''} ${(x?.last_name || '').charAt(0) || ''}${x?.last_name ? '.' : ''}`;
      } else if (treeView === 'horizontal') {
        nameText = `${x?.first_name || ''} ${x?.last_name || ''}`;
      } else {
        nameText = `${x?.first_name} ${x?.last_name}`;
      }

      if (treeView === 'horizontal' || treeView === 'cards') {
        return (
          <b
            style={{...style, cursor: 'pointer', textDecoration: 'underline'}}
            onClick={()=>router.push(`/view/${x.id}`)}
            title={`View ${x.first_name}`}
          >
            {nameText}{asterisk}
          </b>
        );
      }

      return <b style={style}>{nameText}{asterisk}</b>;
    };
    const dobText = (x:any)=> {
      if (treeView === 'minimal' || treeView === 'horizontal') return '';
      if (treeView === 'cards') return x?.dob ? x.dob : '';
      return x?.dob ? `(${x.dob})` : '';
    };

        const nodeClass =
      treeView === 'standard' ? 'node-compact' :
      treeView === 'minimal' ? 'node-minimal' :
      treeView === 'horizontal' ? 'node-horizontal' :
      treeView === 'cards' ? 'node-card' : '';
    const buttonClass =
      treeView === 'minimal' ? 'btn-tiny' :
      treeView === 'standard' ? 'btn-sm' :
      treeView === 'horizontal' ? 'btn-sm' :
      treeView === 'cards' ? 'btn-sm' : '';

    return (
      <li className={nodeClass}>
        {treeView === 'cards' ? (
          <>
            <div className="card-header">
              <div style={{ marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ProfilePicture
                  firstName={m.first_name}
                  lastName={m.last_name}
                  profilePictureUrl={m.profile_picture_url}
                  size={40}
                />
                <div style={{ flex: 1 }}>
                  <div>{nameEl(m)} <span className="small">{dobText(m)}</span></div>
                </div>
              </div>
              {s && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ProfilePicture
                    firstName={s.first_name}
                    lastName={s.last_name}
                    profilePictureUrl={s.profile_picture_url}
                    size={40}
                  />
                  <div style={{ flex: 1 }}>
                    <div>
                      <span style={{opacity:0.6}}>&amp;</span> {nameEl(s)} <span className="small">{dobText(s)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {treeView === 'standard' && (
                <ProfilePicture
                  firstName={m.first_name}
                  lastName={m.last_name}
                  profilePictureUrl={m.profile_picture_url}
                  size={32}
                />
              )}
              <div style={{ flex: 1 }}>
                {nameEl(m)}{' '}<span className="small">{dobText(m)}</span>
                {s && (
                  <>
                    {' '}<span style={{opacity:0.6}}>&amp;</span>{' '}
                    {treeView === 'standard' && (
                      <ProfilePicture
                        firstName={s.first_name}
                        lastName={s.last_name}
                        profilePictureUrl={s.profile_picture_url}
                        size={32}
                      />
                    )}
                    {' '}{nameEl(s)}{' '}<span className="small">{dobText(s)}</span>
                  </>
                )}
              </div>
            </div>
            {treeView !== 'horizontal' && (
              <div className="nav" style={{gap: treeView === 'minimal' ? 4 : 8}}>
                <button className={`btn secondary ${buttonClass}`} title={`View ${m.first_name}`} onClick={()=>router.push(`/view/${m.id}`)}><View /></button>
                <button className={`btn secondary ${buttonClass}`} title={`Edit ${m.first_name}`} onClick={()=>router.push(`/edit/${m.id}`)}><Edit /></button>
                {config.enable_map && m.residence_location && (
                  <button className={`btn secondary ${buttonClass}`} title={`View ${m.first_name} on map`} onClick={()=>router.push(`/map?member=${m.id}`)}><Map /></button>
                )}
                <button className={`btn ${buttonClass}`} title={`Delete ${m.first_name}`} onClick={()=>remove(m.id)}><Delete /></button>
                {s && (<span className="vsep" />)}
                {s && (
                  <>
                    <button className={`btn secondary ${buttonClass}`} title={`View ${s.first_name}`} onClick={()=>router.push(`/view/${s.id}`)}><View /></button>
                    <button className={`btn secondary ${buttonClass}`} title={`Edit ${s.first_name}`} onClick={()=>router.push(`/edit/${s.id}`)}><Edit /></button>
                    {config.enable_map && s.residence_location && (
                      <button className={`btn secondary ${buttonClass}`} title={`View ${s.first_name} on map`} onClick={()=>router.push(`/map?member=${s.id}`)}><Map /></button>
                    )}
                    <button className={`btn ${buttonClass}`} title={`Delete ${s.first_name}`} onClick={()=>remove(s.id)}><Delete /></button>
                  </>
                )}
              </div>
            )}
          </>
        )}
        {n.children?.length>0 && (
          <ul className={`tree ${
            treeView === 'standard' ? 'tree-compact' :
            treeView === 'minimal' ? 'tree-minimal' :
            treeView === 'horizontal' ? 'tree-horizontal' :
            treeView === 'cards' ? 'tree-cards' : ''
          }`}>
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
            View:
            <select
              value={treeView}
              onChange={e => setTreeView(e.target.value as 'standard' | 'minimal' | 'horizontal' | 'cards')}
              style={{ fontSize: '14px', padding: '6px 8px' }}
            >
              <option value="standard">Standard</option>
              <option value="minimal">Minimal</option>
              <option value="horizontal">Horizontal</option>
              <option value="cards">Cards</option>
            </select>
          </label>
        </div>
      </div>
        {unsaved && (
          <p style={{color:'crimson', marginTop:0}}>You have unsaved changes. Please click Save to create a new version.</p>
        )}
        <div className="bottombar" style={{marginTop:8}}>
          <div className="bottombar-left">
            <button
              className="btn"
              disabled={!unsaved || operationLoading}
              title={!unsaved ? 'No unsaved changes' : operationLoading ? 'Saving...' : 'Save current tree as a new version'}
              onClick={saveTree}
            >
              {operationLoading ? 'Saving...' : 'Save Tree'}
            </button>
          </div>
          <div className="bottombar-right" style={{display:'flex', gap:8, alignItems:'center'}}>
            <select value={recoverId} onChange={e=>setRecoverId(e.target.value)}>
              <option value="">Select version…</option>
              {versions.map((v:any)=> (<option key={v.id} value={v.id}>{fmtVersionLabel(v.created_at, undefined, v.version)}</option>))}
            </select>
            <button
              className="btn"
              disabled={!recoverId || operationLoading}
              onClick={recoverTree}
              title={operationLoading ? 'Recovering...' : 'Recover tree from selected version'}
            >
              {operationLoading ? 'Recovering...' : 'Recover'}
            </button>
          </div>
        </div>
        {tree.roots?.length ? (
          <div className={`tree-container ${treeView === 'horizontal' ? 'tree-container-horizontal' : ''}`}>
            <ul className={`tree ${
              treeView === 'standard' ? 'tree-compact' :
              treeView === 'minimal' ? 'tree-minimal' :
              treeView === 'horizontal' ? 'tree-horizontal' :
              treeView === 'cards' ? 'tree-cards' : ''
            }`}>
              {tree.roots.map((r:any)=>(<Node key={r.member.id} n={r}/>))}
            </ul>
          </div>
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
            <button className="btn" onClick={move} disabled={!moveChild || operationLoading}>
              {operationLoading ? 'Moving...' : 'Move'}
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Add Spouse/Partner</h2>
        <AddSpouse
          members={tree.members||[]}
          onLinked={async()=>{
            setOperationLoading(true);
            try {
              await load();
              setUnsaved(true);
            } finally {
              setOperationLoading(false);
            }
          }}
          loading={operationLoading}
        />
      </div>

  {/* Edit is handled on a dedicated page */}
      <Modal open={showInvalid} title="Please fix the following" onClose={()=>setShowInvalid(false)}>
        <ul>
          {invalidMsgs.map((m,i)=>(<li key={i}>{m}</li>))}
        </ul>
      </Modal>

      {/* Loading Overlays */}
      <LoadingOverlay
        isLoading={loading}
        message="Loading family tree..."
      />
      <LoadingOverlay
        isLoading={operationLoading}
        message="Processing..."
        transparent={true}
      />
    </div>
  );
}

function AddSpouse({members,onLinked,loading}:{members:any[]; onLinked: ()=>void; loading?: boolean}){
  const [memberId, setMemberId] = useState('');
  const [partnerId, setPartnerId] = useState('');
  const canLink = memberId && partnerId && memberId !== partnerId;
  const sortedMembers = useMemo(()=> (members||[]).slice().filter((m:any)=>
    isEligibleForMarriage(m.dob) // Filter to only show members 18 or older
  ).sort((a:any,b:any)=>{
    const fa = (a.first_name||'').toLowerCase();
    const fb = (b.first_name||'').toLowerCase();
    if(fa<fb) return -1; if(fa>fb) return 1;
    const la = (a.last_name||'').toLowerCase();
    const lb = (b.last_name||'').toLowerCase();
    if(la<lb) return -1; if(la>lb) return 1; return 0;
  }), [members]);
  async function link(){
    if(!canLink || loading) return;
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
          <button className="btn" onClick={link} disabled={!canLink || loading}>
            {loading ? 'Linking...' : 'Link'}
          </button>
        </div>
      </div>
    </>
  );
}
