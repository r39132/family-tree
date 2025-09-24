import { useRouter } from 'next/router';
import MemberEditor from '../components/MemberEditor';
import TopNav from '../components/TopNav';
import { api } from '../lib/api';
import { useState, useEffect } from 'react';
import Modal from '../components/Modal';
import LoadingOverlay from '../components/LoadingOverlay';

export default function AddMemberPage(){
  const router = useRouter();
  const [member] = useState<any>({ first_name:'', nick_name:'', last_name:'', dob:'', middle_name:'', birth_location:'', residence_location:'', email:'', phone:'', hobbies:[] });
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string,string>>({});
  const [showInvalid, setShowInvalid] = useState(false);
  const [invalidMsgs, setInvalidMsgs] = useState<string[]>([]);
  const [config, setConfig] = useState<any>({ enable_map: false });
  const [allMembers, setAllMembers] = useState<any[]>([]);
  const [treeData, setTreeData] = useState<any>({ roots: [], members: [] });
  const [spouseId, setSpouseId] = useState<string>('');
  const [hasFormChanges, setHasFormChanges] = useState(false);
  const [hasSpouseChange, setHasSpouseChange] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        // Load config
        const configData = await api('/config');
        setConfig(configData);

        // Load tree data
        const tree = await api('/tree');
        setTreeData(tree);
        setAllMembers(tree.members || []);
      } catch (e) {
        console.error('Failed to load data:', e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

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

  // Track spouse changes
  useEffect(() => {
    setHasSpouseChange(spouseId !== '');
  }, [spouseId]);

  // Check if there are any changes overall
  const hasChanges = hasFormChanges || hasSpouseChange;

  async function onSave(m:any){
    setSaving(true);
    try{
      const body = normalizePayload(titleCaseAll({
        ...m,
        spouse_id: spouseId || undefined
      }));
      await api('/tree/members', { method:'POST', body: JSON.stringify(body) });

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
        <MemberEditor
          member={member}
          externalErrors={fieldErrors}
          config={config}
          onChangesDetected={setHasFormChanges}
          onSave={(m:any)=>{
            // MemberEditor won't call onSave if invalid (button disabled), but if form submit is forced, gate it here
            // Client-side validation already runs inside MemberEditor; we can double-check minimal keys
            const errs: string[] = [];
            if(!m.first_name?.trim()) errs.push('First name is required.');
            if(!m.last_name?.trim()) errs.push('Last name is required.');
            if(!m.dob?.trim()) errs.push('Date of Birth is required.');
            if(errs.length){ setInvalidMsgs(errs); setShowInvalid(true); return; }
            onSave(m);
          }}
          requireBasics
          hideSubmit
          formId="add-member-form"
        />
        <div style={{marginTop:12}}>
          <label>Spouse/Partner
            <select className="input" value={spouseId} onChange={e=>setSpouseId(e.target.value)}>
              <option value="">(None)</option>
              {(() => {
                const membersInTree = getMembersInTree(treeData.roots || []);
                return allMembers.filter(m =>
                  !m.spouse_id && // Not already married
                  !membersInTree.has(m.id) // Not part of the family tree structure
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
              form="add-member-form"
              disabled={!hasChanges}
              title={!hasChanges ? 'No changes to save' : 'Save member'}
            >
              Save
            </button>
          </div>
        </div>
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
        message="Saving member..."
        transparent={true}
      />
    </div>
  );
}
