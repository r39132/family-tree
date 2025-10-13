import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import TopNav from '../../components/TopNav';
import MemberEditor from '../../components/MemberEditor';
import { api } from '../../lib/api';
import Modal from '../../components/Modal';
import LoadingOverlay from '../../components/LoadingOverlay';
import { isEligibleForMarriage } from '../../lib/dateUtils';

export default function EditMemberPage(){
  const router = useRouter();
  const { id } = router.query as { id?: string };
  const [member,setMember] = useState<any|null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string,string>>({});
  const [allMembers, setAllMembers] = useState<any[]>([]);
  const [treeData, setTreeData] = useState<any>({ roots: [], members: [] });
  const [error,setError] = useState<string|null>(null);
  const [showInvalid, setShowInvalid] = useState(false);
  const [invalidMsgs, setInvalidMsgs] = useState<string[]>([]);
  const [config, setConfig] = useState<any>({ enable_map: false });
  const [hasFormChanges, setHasFormChanges] = useState(false);
  const [hasSpouseChange, setHasSpouseChange] = useState(false);
  const [originalSpouseId, setOriginalSpouseId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Helper function to get all member IDs that are part of the tree structure
  function getMembersInTree(roots: any[]): Set<string> {
    const membersInTree = new Set<string>();

    function addNodeMembers(node: any) {
      if (node.member?.id) {
        membersInTree.add(node.member.id);
      }
      if (node.spouse?.id) {
        membersInTree.add(node.spouse.id);
      }
      if (node.children) {
        node.children.forEach(addNodeMembers);
      }
    }

    roots.forEach(addNodeMembers);
    return membersInTree;
  }

  useEffect(()=>{
    if(!id) return;
    (async()=>{
      setLoading(true);
      try{
        const configData = await api('/config');
        setConfig(configData);

        // The tree endpoint returns all members; pick the one we need
        const data = await api('/tree');
        setTreeData(data);
        setAllMembers(data.members || []);
        const m = (data.members || []).find((x:any)=>x.id===id);
        if(!m) throw new Error('Member not found');
        setMember(m);
        setOriginalSpouseId(m.spouse_id || '');
      }catch(e:any){
        setError(e?.message || 'Failed to load member');
      } finally {
        setLoading(false);
      }
    })();
  },[id]);

  // Track spouse changes
  useEffect(() => {
    if (member) {
      setHasSpouseChange((member.spouse_id || '') !== originalSpouseId);
    }
  }, [member?.spouse_id, originalSpouseId]);

  // Check if there are any changes overall
  const hasChanges = hasFormChanges || hasSpouseChange;

    async function onSave(m:any){
    const errs: string[] = [];
    if(!m.first_name?.trim()) errs.push('First name is required.');
    if(!m.last_name?.trim()) errs.push('Last name is required.');
    if(!m.dob?.trim()) errs.push('Date of Birth is required.');
    if(errs.length){ setInvalidMsgs(errs); setShowInvalid(true); return; }

    setSaving(true);
    try{
      const body = normalizePayload(titleCaseAll(m));

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
    } finally {
      setSaving(false);
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
            <MemberEditor
              member={member}
              externalErrors={fieldErrors}
              onChangesDetected={setHasFormChanges}
              onSave={onSave}
              requireBasics
              hideSubmit
              formId="edit-member-form"
              config={config}
            />
            <div style={{marginTop:12}}>
              <label>Spouse
                <select className="input" value={member.spouse_id||''} onChange={e=>setSpouse(e.target.value)}>
                  <option value="">(None)</option>
                  {(() => {
                    const membersInTree = getMembersInTree(treeData.roots || []);
                    return allMembers.filter(m=>
                      m.id !== member.id && // Not themselves
                      (!m.spouse_id || m.spouse_id === member.id) && // Not married to someone else
                      (!membersInTree.has(m.id) || m.id === member.spouse_id) && // Not part of the family tree structure, unless they're the current spouse
                      isEligibleForMarriage(m.dob) // At least 18 years old
                    ).map((m:any)=>(
                      <option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>
                    ));
                  })()}
                </select>
              </label>
            </div>
            <div className="bottombar">
              <div className="bottombar-left"></div>
              <div className="bottombar-right">
                <button className="btn secondary" onClick={()=>router.push('/')}>Cancel</button>
                <button
                  className="btn"
                  type="submit"
                  form="edit-member-form"
                  disabled={!hasChanges}
                  title={hasChanges ? "Save changes" : "No changes to save"}
                >
                  Save
                </button>
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

      {/* Loading Overlays */}
      <LoadingOverlay
        isLoading={loading}
        message="Loading member data..."
      />
      <LoadingOverlay
        isLoading={saving}
        message="Saving changes..."
        transparent={true}
      />
    </div>
  );
}
