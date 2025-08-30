import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';
import TopNav from '../../components/TopNav';
import { api } from '../../lib/api';

export default function ViewMemberPage(){
  const router = useRouter();
  const { id } = router.query as { id?: string };
  const [member,setMember] = useState<any|null>(null);
  const [allMembers, setAllMembers] = useState<any[]>([]);
  const [error,setError] = useState<string|null>(null);
  const [config, setConfig] = useState<any>({ enable_map: false });

  useEffect(()=>{
    if(!id) return;
    (async()=>{
      try{
        const configData = await api('/config');
        setConfig(configData);

        const data = await api('/tree');
        setAllMembers(data.members || []);
        const m = (data.members || []).find((x:any)=>x.id===id);
        if(!m) throw new Error('Member not found');
        setMember(m);
      }catch(e:any){ setError(e?.message || 'Failed to load member'); }
    })();
  },[id]);

  const spouse = useMemo(()=>{
    if(!member?.spouse_id) return null;
    return (allMembers || []).find((x:any)=>x.id === member.spouse_id) || null;
  }, [member?.spouse_id, allMembers]);

  return (
    <div className="container">
      <TopNav />
      <div className="card">
        <h2 style={{display:'flex', alignItems:'center', gap:8}}>
          View member
          {member?.is_deceased && (
            <span style={{
              fontSize:12,
              background:'crimson',
              color:'#fff',
              borderRadius:12,
              padding:'2px 8px'
            }}>Deceased</span>
          )}
        </h2>
        {error && <p style={{color:'crimson'}}>{error}</p>}
        {member && (
          <div className="grid2">
            <Field label="First Name" value={member.first_name} />
            <Field label="Nick Name" value={member.nick_name} />
            <Field label="Middle Name" value={member.middle_name} />
            <Field label="Last Name" value={member.last_name} />
            <Field label="Date of Birth" value={member.dob} />
            <Field label="Birth Location" value={member.birth_location} />
            <Field
              label="Residence Location"
              value={
                member.residence_location ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>{member.residence_location}</span>
                    {config.enable_map && (
                      <button
                        className="btn secondary"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                        onClick={() => router.push(`/map?member=${member.id}`)}
                      >
                        View on Map
                      </button>
                    )}
                  </div>
                ) : '-'
              }
            />
            <Field label="Email" value={member.email} />
            <Field label="Phone" value={member.phone} />
            <Field label="Hobbies" value={(member.hobbies||[]).join(', ')} />
            <Field label="Deceased" value={member.is_deceased ? 'Yes' : 'No'} />
            <Field
              label="Spouse/Partner"
              value={member.spouse_id ? (
                spouse ? (
                  <a href={`/view/${spouse.id}`} style={{textDecoration:'underline'}}>
                    {spouse.first_name} {spouse.last_name}
                  </a>
                ) : (
                  '(Unknown)'
                )
              ) : ''}
            />
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
