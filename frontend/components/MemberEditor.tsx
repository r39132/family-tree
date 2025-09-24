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
  onChangesDetected?: (hasChanges: boolean) => void;
};

export default function MemberEditor({member, onSave, requireBasics=false, hideSubmit=false, formId='member-form', externalErrors = {}, config = {}, onChangesDetected}: Props){
  const [m,setM]=useState({...member});
  const [errors, setErrors] = useState<Record<string,string>>({});
  const [hobbiesInput, setHobbiesInput] = useState<string>(() => {
    // Initialize hobbies input as a comma-separated string
    return Array.isArray(member.hobbies) ? member.hobbies.join(', ') : '';
  });
  const router = useRouter();

  function parseHobbies(input: string): string[] {
    if (!input || !input.trim()) return [];
    return input.split(',')
      .map(hobby => hobby.trim())
      .filter(hobby => hobby.length > 0);
  }

  // Function to compare if current state differs from original member
  function hasChanges(): boolean {
    // Compare form fields with original member
    const currentHobbies = parseHobbies(hobbiesInput);
    const originalHobbies = Array.isArray(member.hobbies) ? member.hobbies : [];

    // Helper to normalize values for comparison
    const normalize = (val: any) => val || '';

    return (
      normalize(m.first_name) !== normalize(member.first_name) ||
      normalize(m.nick_name) !== normalize(member.nick_name) ||
      normalize(m.middle_name) !== normalize(member.middle_name) ||
      normalize(m.last_name) !== normalize(member.last_name) ||
      normalize(m.dob) !== normalize(member.dob) ||
      normalize(m.date_of_death) !== normalize(member.date_of_death) ||
      normalize(m.birth_location) !== normalize(member.birth_location) ||
      normalize(m.residence_location) !== normalize(member.residence_location) ||
      normalize(m.email) !== normalize(member.email) ||
      normalize(m.phone) !== normalize(member.phone) ||
      !!m.is_deceased !== !!member.is_deceased ||
      JSON.stringify(currentHobbies.sort()) !== JSON.stringify(originalHobbies.sort())
    );
  }

  // Track changes and notify parent component
  useEffect(() => {
    if (onChangesDetected) {
      onChangesDetected(hasChanges());
    }
  }, [m, hobbiesInput, onChangesDetected]);

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

    let dobDate: Date | null = null;
    let dodDate: Date | null = null;

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
        } else {
          dobDate = dt;
        }
      }
    }

    if(values.date_of_death && values.date_of_death.trim()){
      const dodVal = values.date_of_death.trim();
      if(!dobRe.test(dodVal)){
        errs.date_of_death = 'Use MM/DD/YYYY format.';
      }else{
        // Disallow future dates
        const [mm,dd,yyyy] = dodVal.split('/').map((s:string)=>parseInt(s,10));
        const dt = new Date(Date.UTC(yyyy, mm-1, dd, 0, 0, 0));
        const today = new Date();
        const todayUTC = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
        if(dt.getTime() > todayUTC.getTime()){
          errs.date_of_death = 'Date of Death cannot be in the future.';
        } else {
          dodDate = dt;
        }
      }
    }

    // Validate that death date is after birth date
    if(dobDate && dodDate && dodDate.getTime() <= dobDate.getTime()){
      errs.date_of_death = 'Date of Death must be later than Date of Birth.';
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
  },[m.first_name, m.last_name, m.dob, m.date_of_death, m.email, requireBasics, externalErrors]);

  function save(e:any){
    e.preventDefault();
    // Parse hobbies from the input string before validation/saving
    const memberWithParsedHobbies = {
      ...m,
      hobbies: parseHobbies(hobbiesInput)
    };

    const base = validate(memberWithParsedHobbies);
    const merged: Record<string,string> = { ...base };
    for(const [k,v] of Object.entries(externalErrors || {})){
      if(k === 'email' && !base.email){
        continue;
      }
      merged[k] = v;
    }
    setErrors(merged);
    if(Object.keys(merged).length>0) return;
    onSave(memberWithParsedHobbies);
  }
  return (
  <form id={formId} onSubmit={save}>
      <div className="grid2">
  <label>First Name <sup style={{color:'crimson'}}>*</sup><input className="input" placeholder="First Name" value={m.first_name||''} onChange={e=>ch('first_name',e.target.value)}/>{errors.first_name && <span className="error">{errors.first_name}</span>}</label>
  <label>Nick Name<input className="input" placeholder="Nick Name" value={m.nick_name||''} onChange={e=>ch('nick_name',e.target.value)}/></label>
        <label>Middle Name<input className="input" placeholder="Middle Name" value={m.middle_name||''} onChange={e=>ch('middle_name',e.target.value)}/></label>
  <label>Last Name <sup style={{color:'crimson'}}>*</sup><input className="input" placeholder="Last Name" value={m.last_name||''} onChange={e=>ch('last_name',e.target.value)}/>{errors.last_name && <span className="error">{errors.last_name}</span>}</label>
  <label>Date of Birth (MM/DD/YYYY) <sup style={{color:'crimson'}}>*</sup><input className="input" placeholder="MM/DD/YYYY" value={m.dob||''} onChange={e=>ch('dob', fmtDob(e.target.value))}/>{errors.dob && <span className="error">{errors.dob}</span>}</label>
  <label>
    Date of Death (MM/DD/YYYY)
    <input
      className="input"
      placeholder="MM/DD/YYYY"
      value={m.date_of_death||''}
      onChange={e=>ch('date_of_death', fmtDob(e.target.value))}
      disabled={!m.is_deceased}
      style={{opacity: m.is_deceased ? 1 : 0.5}}
    />
    {errors.date_of_death && <span className="error">{errors.date_of_death}</span>}
  </label>
    <label>
      Birth Location
      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
        <input
          className="input"
          style={{ flex: 1 }}
          placeholder="Birth Location"
          value={m.birth_location||''}
          onChange={e=>ch('birth_location',e.target.value)}
        />
        {config.enable_map && m.birth_location && m.birth_location.trim() && (
          <button
            type="button"
            className="btn secondary"
            style={{ fontSize: '12px', padding: '4px 8px', whiteSpace: 'nowrap' }}
            onClick={() => {
              const address = encodeURIComponent(m.birth_location.trim());
              router.push(`/map?layer=birth&addr=${address}`);
            }}
            aria-label="View birthplace on map"
          >
            View on Map
          </button>
        )}
      </div>
    </label>
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
        {config.enable_map && m.residence_location && m.residence_location.trim() && (
          <button
            type="button"
            className="btn secondary"
            style={{ fontSize: '12px', padding: '4px 8px', whiteSpace: 'nowrap' }}
            onClick={() => {
              const address = encodeURIComponent(m.residence_location.trim());
              router.push(`/map?layer=residence&addr=${address}`);
            }}
            aria-label="View residence on map"
          >
            View on Map
          </button>
        )}
      </div>
    </label>
  <label>Email<input className="input" type="email" placeholder="Email" value={m.email||''} onChange={e=>ch('email',e.target.value)}/>{errors.email && <span className="error">{errors.email}</span>}</label>
    <label>Phone<input className="input" placeholder="Phone" value={m.phone||''} onChange={e=>ch('phone',e.target.value)}/></label>
  <label>Hobbies (comma-separated)
    <input
      className="input"
      placeholder="e.g., Reading, Hiking, Cooking"
      value={hobbiesInput}
      onChange={e=>setHobbiesInput(e.target.value)}
    />
    {hobbiesInput && (
      <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
        Preview: {parseHobbies(hobbiesInput).join(' • ')}
      </div>
    )}
  </label>
  <label><input type="checkbox" checked={!!m.is_deceased} onChange={e=>{
    const isDeceased = e.target.checked;
    ch('is_deceased', isDeceased);
    // Clear date of death when unchecking deceased status
    if (!isDeceased) {
      ch('date_of_death', '');
    }
  }} /> Deceased</label>
      </div>
      {!hideSubmit && (
        <div className="nav"><button className="btn" type="submit" disabled={Object.keys(errors).length>0}>Save</button></div>
      )}
    </form>
  );
}
