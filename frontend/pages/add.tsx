import { useRouter } from 'next/router';
import MemberEditor from '../components/MemberEditor';
import TopNav from '../components/TopNav';
import { api } from '../lib/api';
import { useState, useEffect } from 'react';
import Modal from '../components/Modal';
import TreeCacheManager from '../lib/treeCache';

export default function AddMemberPage(){
  const router = useRouter();
  const [member] = useState<any>({ first_name:'', nick_name:'', last_name:'', dob:'', middle_name:'', birth_location:'', residence_location:'', email:'', phone:'', hobbies:[] });
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string,string>>({});
  const [showInvalid, setShowInvalid] = useState(false);
  const [invalidMsgs, setInvalidMsgs] = useState<string[]>([]);
  const [config, setConfig] = useState<any>({ enable_map: false });

  useEffect(() => {
    async function loadConfig() {
      try {
        const configData = await api('/config');
        setConfig(configData);
      } catch (e) {
        console.error('Failed to load config:', e);
      }
    }
    loadConfig();
  }, []);

  async function onSave(m:any){
    try{
  const body = normalizePayload(titleCaseAll(m));
  await api('/tree/members', { method:'POST', body: JSON.stringify(body) });

      // Invalidate tree cache since we added a new member
      const cacheManager = TreeCacheManager.getInstance();
      cacheManager.invalidateCache('structure_changed');

      router.push('/');
    }catch(e:any){
      // Attempt to parse server 422 detail and surface email error inline
      const msg = e?.message || '';
      try{
        const jsonPart = msg.substring(msg.indexOf(':')+1).trim();
        const parsed = JSON.parse(jsonPart);
        if(parsed?.detail && Array.isArray(parsed.detail)){
          const fe: Record<string,string> = {};
          for(const d of parsed.detail){
            if(d.loc && d.loc[0]==='body' && d.loc[1]){
              fe[d.loc[1]] = d.msg?.startsWith('value is not a valid email') ? 'Error: Not a valid email format' : (d.msg || 'Invalid value');
            }
          }
          setFieldErrors(fe);
          setError(null);
          return;
        }
      }catch{}
      setError(msg || 'Failed to add member');
    }
  }

  function normalizePayload(m:any){
    const out: any = { ...m };
    for(const k of Object.keys(out)){
      if(typeof out[k] === 'string' && out[k].trim() === ''){
        out[k] = null;
      }
    }
    // remove nulls to avoid sending explicit nulls
    for(const k of Object.keys(out)){
      if(out[k] === null) delete out[k];
    }
    return out;
  }

  function titleCaseAll(m:any){
    const out = { ...m };
    const keys = ['first_name','nick_name','middle_name','last_name','birth_location','residence_location','email','phone'];
    for(const k of keys){
      if(typeof out[k] === 'string') out[k] = toTitle(out[k]);
    }
    if(Array.isArray(out.hobbies)){
      out.hobbies = out.hobbies.map((s:any)=> typeof s === 'string' ? toTitle(s) : s);
    }
    return out;
  }
  function toTitle(s:string){
    return s.split(/\s+/).filter(Boolean).map(w=> w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
  }

  return (
    <div className="container">
      <TopNav />
      <div className="card">
        <h2>Add member</h2>
        {error && <p style={{color:'crimson'}}>{error}</p>}
  <MemberEditor member={member} externalErrors={fieldErrors} config={config} onSave={(m:any)=>{
          // MemberEditor won't call onSave if invalid (button disabled), but if form submit is forced, gate it here
          // Client-side validation already runs inside MemberEditor; we can double-check minimal keys
          const errs: string[] = [];
          if(!m.first_name?.trim()) errs.push('First name is required.');
          if(!m.last_name?.trim()) errs.push('Last name is required.');
          if(!m.dob?.trim()) errs.push('Date of Birth is required.');
          if(errs.length){ setInvalidMsgs(errs); setShowInvalid(true); return; }
          onSave(m);
        }} requireBasics hideSubmit formId="add-member-form" />
        <div className="bottombar">
          <div className="bottombar-left"></div>
          <div className="bottombar-right">
            <button className="btn secondary" onClick={()=>router.push('/')}>Cancel</button>
            <button className="btn" type="submit" form="add-member-form">Save</button>
          </div>
        </div>
      </div>
      <Modal open={showInvalid} title="Please fix the following" onClose={()=>setShowInvalid(false)}>
        <ul>
          {invalidMsgs.map((m,i)=>(<li key={i}>{m}</li>))}
        </ul>
      </Modal>
    </div>
  );
}
