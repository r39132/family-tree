import { useEffect, useState } from 'react';
import TopNav from '../components/TopNav';
import { api } from '../lib/api';

type Profile = {
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  profile_photo_data_url?: string;
};

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [editingFirst, setEditingFirst] = useState(false);
  const [editingLast, setEditingLast] = useState(false);
  const [firstNameDraft, setFirstNameDraft] = useState('');
  const [lastNameDraft, setLastNameDraft] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api('/user/profile').then((p) => {
      setProfile(p);
      setFirstNameDraft(p.first_name || '');
      setLastNameDraft(p.last_name || '');
    }).catch((e) => setError(String(e)));
  }, []);

  async function saveFirst() {
    try {
      const updated = await api('/user/profile', {
        method: 'PUT',
        body: JSON.stringify({ first_name: firstNameDraft })
      });
      setProfile(updated);
      setEditingFirst(false);
    } catch (e) {
      setError(String(e));
    }
  }

  async function saveLast() {
    try {
      const updated = await api('/user/profile', {
        method: 'PUT',
        body: JSON.stringify({ last_name: lastNameDraft })
      });
      setProfile(updated);
      setEditingLast(false);
    } catch (e) {
      setError(String(e));
    }
  }

  function cancelFirst() {
    setFirstNameDraft(profile?.first_name || '');
    setEditingFirst(false);
  }

  function cancelLast() {
    setLastNameDraft(profile?.last_name || '');
    setEditingLast(false);
  }

  async function onPhotoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 256 * 1024) {
      setError('Image too large (max 256KB).');
      return;
    }
    const okTypes = ['image/png', 'image/jpeg'];
    if (!okTypes.includes(file.type)) {
      setError('Unsupported format. Use PNG or JPEG.');
      return;
    }
    const reader = new FileReader();
    reader.onload = async () => {
      const dataUrl = String(reader.result);
      try {
        const updated = await api('/user/profile/photo', {
          method: 'POST',
          body: JSON.stringify({ image_data_url: dataUrl })
        });
        setProfile(updated);
      } catch (e) {
        setError(String(e));
      }
    };
    reader.readAsDataURL(file);
  }

  return (
    <div>
      <TopNav />
      <div className="container" style={{ maxWidth: 720, margin: '24px auto' }}>
        <h1>Profile</h1>
        {error && <div className="error" style={{ color: 'red' }}>{error}</div>}
        {!profile ? (
          <div>Loading…</div>
        ) : (
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
              <div>
                <div
                  style={{
                    width: 100,
                    height: 100,
                    borderRadius: '50%',
                    overflow: 'hidden',
                    background: '#f2f2f2',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid #ddd'
                  }}
                >
                  {profile.profile_photo_data_url ? (
                    <img src={profile.profile_photo_data_url} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    <span style={{ fontSize: 32 }}>👤</span>
                  )}
                </div>
                <div style={{ marginTop: 8 }}>
                  <label className="btn sm">
                    Upload Photo
                    <input type="file" accept="image/png,image/jpeg" onChange={onPhotoChange} style={{ display: 'none' }} />
                  </label>
                </div>
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>User Id</div>
                  <div>{profile.username}</div>
                </div>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>Email</div>
                  <div>{profile.email || '—'}</div>
                </div>

                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>First Name</div>
                  {!editingFirst ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div>{profile.first_name || '—'}</div>
                      <button className="btn secondary sm" onClick={() => setEditingFirst(true)}>Edit</button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input value={firstNameDraft} onChange={e => setFirstNameDraft(e.target.value)} />
                      <button className="btn sm" onClick={saveFirst}>Save</button>
                      <button className="btn secondary sm" onClick={cancelFirst}>Cancel</button>
                    </div>
                  )}
                </div>

                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>Last Name</div>
                  {!editingLast ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div>{profile.last_name || '—'}</div>
                      <button className="btn secondary sm" onClick={() => setEditingLast(true)}>Edit</button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input value={lastNameDraft} onChange={e => setLastNameDraft(e.target.value)} />
                      <button className="btn sm" onClick={saveLast}>Save</button>
                      <button className="btn secondary sm" onClick={cancelLast}>Cancel</button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
