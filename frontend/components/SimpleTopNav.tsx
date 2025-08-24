import Link from 'next/link';

export default function SimpleTopNav(){
  return (
    <div className="topbar">
      <div className="container" style={{display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', padding: 0}}>
        <div className="topbar-left">
        </div>
        <div className="topbar-center">
          <Link href="/login" className="brand">🌳 Family Tree</Link>
        </div>
        <div className="topbar-right">
        </div>
      </div>
    </div>
  );
}
