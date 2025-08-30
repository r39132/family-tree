import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import TopNav from '../../components/TopNav';
import MemberEditor from '../../components/MemberEditor';
import { api } from '../../lib/api';
import Modal from '../../components/Modal';
import TreeCacheManager from '../../lib/treeCache';

export default function EditMemberPage(){
  const router = useRouter();
  const { id } = router.query as { id?: string };
  const [member,setMember] = useState<any|null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string,string>>({});
  const [allMembers, setAllMembers] = useState<any[]>([]);
  const [error,setError] = useState<string|null>(null);
  const [showInvalid, setShowInvalid] = useState(false);
  const [invalidMsgs, setInvalidMsgs] = useState<string[]>([]);
  const [config, setConfig] = useState<any>({ enable_map: false });

  useEffect(()=>{
    if(!id) return;
    (async()=>{
      try{
        const configData = await api('/config');
        setConfig(configData);

        // The tree endpoint returns all members; pick the one we need
  const data = await api('/tree');
  setAllMembers(data.members || []);
        const m = (data.members || []).find((x:any)=>x.id===id);
        if(!m) throw new Error('Member not found');
        setMember(m);
      }catch(e:any){ setError(e?.message || 'Failed to load member'); }
    })();
  },[id]);

  async function onSave(m:any){
    const errs: string[] = [];
    if(!m.first_name?.trim()) errs.push('First name is required.');
    if(!m.last_name?.trim()) errs.push('Last name is required.');
    if(!m.dob?.trim()) errs.push('Date of Birth is required.');
    if(errs.length){ setInvalidMsgs(errs); setShowInvalid(true); return; }
    try{
      const body = normalizePayload(titleCaseAll(m));

      const cacheManager = TreeCacheManager.getInstance();

      // Check if this update affects tree display before making the API call
      if (cacheManager.shouldInvalidateForMemberUpdate(body)) {
        cacheManager.invalidateCache('data_changed');
      }

      await api(`/tree/members/${m.id}`, { method:'PATCH', body: JSON.stringify(body) });
      router.push('/');
    }catch(e:any){
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
          return;
        }
      }catch{}
      throw e;
    }
  }

  function normalizePayload(m:any){
    const out: any = { ...m };
    for(const k of Object.keys(out)){
      if(typeof out[k] === 'string' && out[k].trim() === ''){
        out[k] = null;
      }
    }
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

  async function setSpouse(spouseId: string){
    if(!id) return;
    await api(`/tree/members/${id}/spouse`, { method:'POST', body: JSON.stringify({ spouse_id: spouseId || null })});
    // refresh member
    const data = await api('/tree');
    const m = (data.members || []).find((x:any)=>x.id===id);
    if(m) setMember(m);
  }

  return (
    <div className="container">
      <TopNav />
      <div className="card">
        <h2>Edit member</h2>
        {error && <p style={{color:'crimson'}}>{error}</p>}
        {member && (
          <>
            <MemberEditor member={member} externalErrors={fieldErrors} onSave={onSave} requireBasics hideSubmit formId="edit-member-form" config={config} />
            <div style={{marginTop:12}}>
              <label>Spouse
                <select className="input" value={member.spouse_id||''} onChange={e=>setSpouse(e.target.value)}>
                  <option value="">(None)</option>
                  {allMembers.filter(m=>m.id!==member.id).map((m:any)=>(
                    <option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="bottombar">
              <div className="bottombar-left"></div>
              <div className="bottombar-right">
                <button className="btn secondary" onClick={()=>router.push('/')}>Cancel</button>
                <button className="btn" type="submit" form="edit-member-form">Save</button>
              </div>
            </div>
          </>
        )}
      </div>
      <Modal open={showInvalid} title="Please fix the following" onClose={()=>setShowInvalid(false)}>
        <ul>
          {invalidMsgs.map((m,i)=>(<li key={i}>{m}</li>))}
        </ul>
      </Modal>
    </div>
  );
}
