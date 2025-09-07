import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState, useRef } from 'react';
import { api } from '../lib/api';

type Props = {
  showBack?: boolean;
  showAdd?: boolean;
  showInvite?: boolean;
  showLogout?: boolean;
};

type UserInfo = {
  username: string;
  email: string;
  roles?: string[];
  profile_photo_data_url?: string;
};

type AppConfig = {
  enable_map: boolean;
  require_invite: boolean;
};

export default function TopNav({ showBack=true, showAdd=true, showInvite=true, showLogout=true }: Props){
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [config, setConfig] = useState<AppConfig>({ enable_map: false, require_invite: true });
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(()=>{
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      const isAuthenticated = !!token;
      setAuthed(isAuthenticated);

      if (isAuthenticated) {
        // Fetch user profile (includes roles and optional photo)
        api('/user/profile')
          .then(data => setUserInfo(data))
          .catch(err => {
            console.error('Failed to fetch user info:', err);
            // If token is invalid, log out
            if (err.message.includes('401')) {
              logout();
            }
          });

        // Fetch app configuration
        api('/config')
          .then(data => setConfig(data))
          .catch(err => {
            console.error('Failed to fetch config:', err);
          });
      }
    }
  },[]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  function logout(){
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
    setUserInfo(null);
    setDropdownOpen(false);
    router.push('/login');
  }

  function toggleDropdown() {
    setDropdownOpen(!dropdownOpen);
  }
  return (
    <div className="topbar">
      <div className="topbar-left">
        {authed && (
          <>
            {showBack && <Link className="btn secondary" href="/">Family Tree</Link>}
            {showAdd && <Link className="btn secondary" href="/add">Add Member</Link>}
            <Link className="btn secondary" href="/events">Events</Link>
            {config.enable_map && <Link className="btn secondary" href="/map">Map</Link>}
          </>
        )}
      </div>
      <div className="topbar-center">
        <Link href="/" className="brand">🌳 Family Tree</Link>
      </div>
      <div className="topbar-right">
        {authed && userInfo && (
          <div className="user-avatar-container" ref={dropdownRef} style={{ position: 'relative', marginLeft: 'auto' }}>
            <div
              className="user-avatar"
              onClick={toggleDropdown}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '36px',
                height: '36px',
                backgroundColor: '#f0f0f0',
                color: '#333',
                borderRadius: '50%',
                fontSize: '18px',
                cursor: 'pointer',
                border: '2px solid transparent',
                transition: 'border-color 0.2s ease',
                ...(dropdownOpen && { borderColor: '#007bff' })
              }}
            >
              {userInfo.profile_photo_data_url ? (
                <img src={userInfo.profile_photo_data_url} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
              ) : (
                <span>👤</span>
              )}
            </div>

            {dropdownOpen && (
              <div
                className="avatar-dropdown"
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: '0',
                  marginTop: '8px',
                  backgroundColor: 'white',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                  minWidth: '160px',
                  zIndex: 1000,
                  overflow: 'hidden'
                }}
              >
                <Link
                  href="/profile"
                  onClick={() => setDropdownOpen(false)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '12px 16px',
                    borderBottom: '1px solid #eee',
                    color: '#333',
                    fontSize: '14px',
                    fontWeight: 500,
                    textDecoration: 'none'
                  }}
                >
                  <span
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: '50%',
                      overflow: 'hidden',
                      background: '#f2f2f2',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '1px solid #ddd'
                    }}
                  >
                    {/* Placeholder avatar; actual photo rendered on profile page */}
                    👤
                  </span>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{userInfo.username}</span>
                </Link>
                {userInfo?.roles?.includes('admin') && (
                  <Link
                    href="/admin"
                    style={{
                      display: 'block',
                      width: '100%',
                      padding: '10px 16px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: '#333',
                      fontSize: '14px',
                      textDecoration: 'none',
                      transition: 'background-color 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f8f9fa';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                    onClick={() => setDropdownOpen(false)}
                  >
                    Admin
                  </Link>
                )}
                {showInvite && (
                  <Link
                    href="/invite"
                    style={{
                      display: 'block',
                      width: '100%',
                      padding: '10px 16px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: '#333',
                      fontSize: '14px',
                      textDecoration: 'none',
                      transition: 'background-color 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f8f9fa';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                    onClick={() => setDropdownOpen(false)}
                  >
                    Invite
                  </Link>
                )}
                {showLogout && (
                  <button
                    onClick={logout}
                    style={{
                      width: '100%',
                      padding: '10px 16px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: '#dc3545',
                      fontSize: '14px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'background-color 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f8f9fa';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    Logout
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
