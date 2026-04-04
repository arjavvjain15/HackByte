import { useEffect } from 'react'

export function BottomSheet({ open, onClose, title, children }) {
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className="bottom-sheet">
        <div className="sheet-handle" />
        {title && (
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'4px 16px 10px', borderBottom:'0.5px solid var(--border)' }}>
            <span style={{ fontWeight:500, fontSize:14 }}>{title}</span>
            <button onClick={onClose} style={{ background:'none', border:'none', cursor:'pointer', color:'var(--text3)', fontSize:18, lineHeight:1 }} aria-label="Close">×</button>
          </div>
        )}
        <div style={{ flex:1, overflowY:'auto' }}>
          {children}
        </div>
      </div>
    </>
  )
}
