export function Spinner({ size = 20, color = 'var(--green)' }) {
  return (
    <div style={{
      width: size, height: size,
      border: `2px solid ${color}20`,
      borderTop: `2px solid ${color}`,
      borderRadius: '50%',
    }} className="anim-spin" role="status" aria-label="Loading" />
  )
}

export function PageSpinner() {
  return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100vh', background:'var(--bg2)' }}>
      <Spinner size={32} />
    </div>
  )
}
