export function SkeletonCard() {
  return (
    <div className="rc" style={{ marginBottom:6 }}>
      <div style={{ display:'flex', gap:6, marginBottom:6 }}>
        <div className="skeleton" style={{ width:36, height:14 }} />
        <div className="skeleton" style={{ width:24, height:14, marginLeft:'auto' }} />
      </div>
      <div className="skeleton" style={{ width:'70%', height:13, marginBottom:4 }} />
      <div className="skeleton" style={{ width:'50%', height:11, marginBottom:6 }} />
      <div style={{ display:'flex', justifyContent:'space-between' }}>
        <div className="skeleton" style={{ width:60, height:11 }} />
        <div className="skeleton" style={{ width:42, height:14, borderRadius:99 }} />
      </div>
      <div className="pbar" style={{ marginTop:6 }}>
        <div className="skeleton" style={{ width:'33%', height:'100%' }} />
      </div>
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div style={{ padding:'8px 0', borderBottom:'0.5px solid var(--border)', display:'flex', gap:8 }}>
      <div className="skeleton" style={{ width:6, height:6, borderRadius:'50%', marginTop:4, flexShrink:0 }} />
      <div style={{ flex:1 }}>
        <div className="skeleton" style={{ width:'80%', height:12, marginBottom:4 }} />
        <div className="skeleton" style={{ width:'50%', height:10 }} />
      </div>
      <div className="skeleton" style={{ width:20, height:10 }} />
    </div>
  )
}

export function SkeletonBadge() {
  return (
    <div style={{ width:64, textAlign:'center' }}>
      <div className="skeleton" style={{ width:32, height:32, borderRadius:'50%', margin:'0 auto 4px' }} />
      <div className="skeleton" style={{ width:40, height:10, margin:'0 auto' }} />
    </div>
  )
}
