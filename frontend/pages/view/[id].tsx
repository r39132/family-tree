import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import TopNav from '../../components/TopNav';
import { api } from '../../lib/api';

export default function ViewMemberPage(){
  const router = useRouter();
  const { id } = router.query as { id?: string };
  const [member,setMember] = useState<any|null>(null);
  const [error,setError] = useState<string|null>(null);

  useEffect(()=>{
    if(!id) return;
    (async()=>{
      try{
        const data = await api('/tree');
        const m = (data.members || []).find((x:any)=>x.id===id);
        if(!m) throw new Error('Member not found');
        setMember(m);
      }catch(e:any){ setError(e?.message || 'Failed to load member'); }
    })();
  },[id]);

  return (
    <div className="container">
      <TopNav />
      <div className="card">
        <h2>View member</h2>
        {error && <p style={{color:'crimson'}}>{error}</p>}
        {member && (
          <div className="grid2">
            <Field label="First Name" value={member.first_name} />
            <Field label="Nick Name" value={member.nick_name} />
            <Field label="Middle Name" value={member.middle_name} />
            <Field label="Last Name" value={member.last_name} />
            <Field label="Date of Birth" value={member.dob} />
            <Field label="Birth Location" value={member.birth_location} />
            <Field label="Residence Location" value={member.residence_location} />
            <Field label="Email" value={member.email} />
            <Field label="Phone" value={member.phone} />
            <Field label="Hobbies" value={(member.hobbies||[]).join(', ')} />
          </div>
        )}
        <div className="bottombar">
          <div className="bottombar-left"></div>
          <div className="bottombar-right">
            {member && <button className="btn" onClick={()=>router.push(`/edit/${member.id}`)}>Edit</button>}
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({label, value}:{label:string, value:any}){
  return (
    <label>
      {label}
      <div className="input" style={{background:'#f7f7f7'}}>{value || '-'}</div>
    </label>
  );
}
