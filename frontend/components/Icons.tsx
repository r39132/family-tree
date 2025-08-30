import React from 'react';

type IconProps = { size?: number; title?: string; className?: string };

export function IconMagnifier({ size=20, title='View', className }: IconProps){
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-label={title} role="img">
      <title>{title}</title>
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2"/>
      <line x1="16.65" y1="16.65" x2="21" y2="21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

export function IconPencil({ size=20, title='Edit', className }: IconProps){
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-label={title} role="img">
      <title>{title}</title>
      <path d="M3 17.25V21h3.75L18.81 8.94l-3.75-3.75L3 17.25z" fill="currentColor"/>
      <path d="M20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z" fill="currentColor"/>
    </svg>
  );
}

export function IconTrash({ size=20, title='Delete', className }: IconProps){
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-label={title} role="img">
      <title>{title}</title>
      <path d="M6 7h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M7 7l1 13a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2l1-13" stroke="currentColor" strokeWidth="2"/>
      <path d="M10 11v6M14 11v6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

export function IconMap({ size=20, title='Map', className }: IconProps){
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-label={title} role="img">
      <title>{title}</title>
      <path d="M9 20L3 17V4l6 3 6-3 6 3v13l-6-3-6 3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M9 4v16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M15 7v13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

export const Icons = { View: IconMagnifier, Edit: IconPencil, Delete: IconTrash, Map: IconMap };
