import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

type Props = {
  showBack?: boolean;
  showAdd?: boolean;
  showInvite?: boolean;
  showLogout?: boolean;
};

export default function TopNav({ showBack=true, showAdd=true, showInvite=true, showLogout=true }: Props){
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  useEffect(()=>{
    if (typeof window !== 'undefined') {
      setAuthed(!!localStorage.getItem('token'));
    }
  },[]);
  function logout(){
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
    router.push('/login');
  }
  return (
    <div className="topbar">
      <div className="topbar-left">
        {authed && (
          <>
            {showBack && <Link className="btn secondary" href="/">Back to Family Tree</Link>}
            {showAdd && <Link className="btn secondary" href="/add">Add member</Link>}
          </>
        )}
      </div>
      <div className="topbar-center">
        <Link href="/" className="brand">🌳 Family Tree</Link>
      </div>
      <div className="topbar-right">
        {authed && (
          <>
            {showInvite && <Link className="btn secondary" href="/invite">Invite</Link>}
            {showLogout && <button className="btn" onClick={logout}>Logout</button>}
          </>
        )}
      </div>
    </div>
  );
}
