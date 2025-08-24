export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";

export async function api(path: string, opts: RequestInit = {}){
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const headers = new Headers(opts.headers || {});
  headers.set('Content-Type','application/json');
  if(token) headers.set('Authorization',`Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if(!res.ok){
    const t = await res.text();
    throw new Error(`${res.status}: ${t}`);
  }
  return res.json();
}
