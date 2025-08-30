import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';

type Props = {
  member: any;
  onSave: (m:any)=>void;
  requireBasics?: boolean;
  hideSubmit?: boolean;
  formId?: string;
  externalErrors?: Record<string,string>;
  config?: any;
};

export default function MemberEditor({member, onSave, requireBasics=false, hideSubmit=false, formId='member-form', externalErrors = {}, config = {}}: Props){
  const [m,setM]=useState({...member});
  const [errors, setErrors] = useState<Record<string,string>>({});
  const router = useRouter();
  function ch(k:string,v:any){ setM((p:any)=>({...p,[k]:v})); }
  const nameRe = useMemo(()=>/^[A-Za-z-]+$/,[]);
  const dobRe = useMemo(()=>/^(0[1-9]|1[0-2])\/(0[1-9]|[12][0-9]|3[01])\/\d{4}$/ ,[]);
  const emailRe = useMemo(()=>/^[^\s@]+@[^\s@]+\.[^\s@]+$/,[]);

  // Live-format DOB as MM/DD/YYYY while typing
  function fmtDob(input: string): string {
    const digits = (input || '').replace(/\D/g, '').slice(0, 8); // keep up to 8 digits
    if (digits.length <= 2) return digits; // MM
    if (digits.length <= 4) return `${digits.slice(0,2)}/${digits.slice(2)}`; // MM/DD
    return `${digits.slice(0,2)}/${digits.slice(2,4)}/${digits.slice(4)}`; // MM/DD/YYYY
  }

  function validate(values:any){
    const errs: Record<string,string> = {};
    if(requireBasics){
      if(!values.first_name?.trim()) errs.first_name = 'First name is required.';
      if(!values.last_name?.trim()) errs.last_name = 'Last name is required.';
      if(!values.dob?.trim()) errs.dob = 'Date of Birth is required.';
    }
    if(values.first_name && !nameRe.test(values.first_name.trim())) errs.first_name = 'Only letters and - are allowed.';
    if(values.last_name && !nameRe.test(values.last_name.trim())) errs.last_name = 'Only letters and - are allowed.';
    if(values.dob){
      const dobVal = values.dob.trim();
      if(!dobRe.test(dobVal)){
        errs.dob = 'Use MM/DD/YYYY format.';
      }else{
        // Disallow future dates
        const [mm,dd,yyyy] = dobVal.split('/').map((s:string)=>parseInt(s,10));
        const dt = new Date(Date.UTC(yyyy, mm-1, dd, 0, 0, 0));
        const today = new Date();
        const todayUTC = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
        if(dt.getTime() > todayUTC.getTime()){
          errs.dob = 'Date of Birth cannot be in the future.';
        }
      }
    }
    if(values.email && !emailRe.test(values.email.trim())) errs.email = 'Error: Not a valid email format';
    return errs;
  }

  useEffect(()=>{
    const base = validate(m);
    // Merge in externalErrors, but for email drop server error once client validation passes
    const merged: Record<string,string> = { ...base };
    for(const [k,v] of Object.entries(externalErrors || {})){
      if(k === 'email' && !base.email){
        // client-side email is valid now; clear server email error
        continue;
      }
      merged[k] = v;
    }
    setErrors(merged);
  },[m.first_name, m.last_name, m.dob, m.email, requireBasics, externalErrors]);

  function save(e:any){
    e.preventDefault();
    const base = validate(m);
    const merged: Record<string,string> = { ...base };
    for(const [k,v] of Object.entries(externalErrors || {})){
      if(k === 'email' && !base.email){
        continue;
      }
      merged[k] = v;
    }
    setErrors(merged);
    if(Object.keys(merged).length>0) return;
    onSave(m);
  }
  return (
  <form id={formId} onSubmit={save}>
      <div className="grid2">
  <label>First Name <sup style={{color:'crimson'}}>*</sup><input className="input" placeholder="First Name" value={m.first_name||''} onChange={e=>ch('first_name',e.target.value)}/>{errors.first_name && <span className="error">{errors.first_name}</span>}</label>
  <label>Nick Name<input className="input" placeholder="Nick Name" value={m.nick_name||''} onChange={e=>ch('nick_name',e.target.value)}/></label>
        <label>Middle Name<input className="input" placeholder="Middle Name" value={m.middle_name||''} onChange={e=>ch('middle_name',e.target.value)}/></label>
  <label>Last Name <sup style={{color:'crimson'}}>*</sup><input className="input" placeholder="Last Name" value={m.last_name||''} onChange={e=>ch('last_name',e.target.value)}/>{errors.last_name && <span className="error">{errors.last_name}</span>}</label>
  <label>Date of Birth (MM/DD/YYYY) <sup style={{color:'crimson'}}>*</sup><input className="input" placeholder="MM/DD/YYYY" value={m.dob||''} onChange={e=>ch('dob', fmtDob(e.target.value))}/>{errors.dob && <span className="error">{errors.dob}</span>}</label>
    <label>Birth Location<input className="input" placeholder="Birth Location" value={m.birth_location||''} onChange={e=>ch('birth_location',e.target.value)}/></label>
    <label>
      Residence Location
      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
        <input
          className="input"
          style={{ flex: 1 }}
          placeholder="Residence Location"
          value={m.residence_location||''}
          onChange={e=>ch('residence_location',e.target.value)}
        />
        {config.enable_map && m.residence_location && (
          <button
            type="button"
            className="btn secondary"
            style={{ fontSize: '12px', padding: '4px 8px', whiteSpace: 'nowrap' }}
            onClick={() => router.push(`/map?member=${member.id}`)}
          >
            View on Map
          </button>
        )}
      </div>
    </label>
  <label>Email<input className="input" type="email" placeholder="Email" value={m.email||''} onChange={e=>ch('email',e.target.value)}/>{errors.email && <span className="error">{errors.email}</span>}</label>
    <label>Phone<input className="input" placeholder="Phone" value={m.phone||''} onChange={e=>ch('phone',e.target.value)}/></label>
  <label>Hobbies (comma-separated)<input className="input" placeholder="e.g., Reading, Hiking" value={(m.hobbies||[]).join(', ')} onChange={e=>ch('hobbies', e.target.value.split(',').map((s:string)=>s.trim()).filter(Boolean))}/></label>
  <label><input type="checkbox" checked={!!m.is_deceased} onChange={e=>ch('is_deceased', e.target.checked)} /> Deceased</label>
      </div>
      {!hideSubmit && (
        <div className="nav"><button className="btn" type="submit" disabled={Object.keys(errors).length>0}>Save</button></div>
      )}
    </form>
  );
}
