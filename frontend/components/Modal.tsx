import React from 'react';

export default function Modal({ open, title, onClose, children }:{ open:boolean; title?:string; onClose:()=>void; children: React.ReactNode }){
  if(!open) return null;
  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-header">
          <h3>{title || 'Notice'}</h3>
          <button className="btn secondary" onClick={onClose}>Close</button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
}
