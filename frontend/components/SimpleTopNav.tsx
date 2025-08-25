import Link from 'next/link';

export default function SimpleTopNav(){
  return (
    <div className="topbar-simple">
      <Link href="/login" className="brand">🌳 Family Tree</Link>
    </div>
  );
}
