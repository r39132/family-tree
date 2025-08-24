import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import { useRouter } from 'next/router';

export default function Register(){
  const [invite_code,setInvite]=useState('');
  const [username,setUsername]=useState('');
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [confirm,setConfirm]=useState('');
  const [error,setError]=useState<string|null>(null);
  const router = useRouter();

  // Prefill invite from query once ready
  useEffect(()=>{
    if(!router.isReady) return;
    const q = router.query as { invite?: string };
    if (q.invite && !invite_code) {
      setInvite(String(q.invite));
    }
  }, [router.isReady, router.query, invite_code]);

  function isValidEmail(v:string){
    // Simple email regex similar to MemberEditor
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  }

  async function submit(e:any){
    e.preventDefault();
    // Basic client validation
    if(!invite_code.trim()||!username.trim()||!email.trim()||!password.trim()||!confirm.trim()){
      setError('All fields are required.');
      return;
    }
    if(!isValidEmail(email)){
      setError('Please enter a valid email address.');
      return;
    }
    if(password!==confirm){
      setError('Passwords do not match.');
      return;
    }
    try{
      await api('/auth/register',{method:'POST', body:JSON.stringify({invite_code,username,email,password})});
      router.push('/login');
    }catch(err:any){
      setError(err.message);
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h1>Register</h1>
        {error && <p style={{color:'crimson'}}>{error}</p>}
        <form onSubmit={submit}>
          <input className="input" placeholder="Invite Code" value={invite_code} onChange={e=>setInvite(e.target.value)}/>
          <input className="input" placeholder="Username" value={username} onChange={e=>setUsername(e.target.value)}/>
          <input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)}/>
          <input className="input" type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)}/>
          <input className="input" type="password" placeholder="Confirm Password" value={confirm} onChange={e=>setConfirm(e.target.value)}/>
          <div className="bottombar">
            <div className="bottombar-left">
              <Link href="/login">Back to login</Link>
            </div>
            <div className="bottombar-right">
              <button className="btn" type="submit">Create account</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
