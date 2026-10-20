export function ScrollJumpButtons() {
  return (
    <div className="scroll-jump">
      <button type="button" className="btn btn-fab" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} title="В начало">
        ↑
      </button>
      <button
        type="button"
        className="btn btn-fab"
        onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" })}
        title="В конец"
      >
        ↓
      </button>
    </div>
  );
}
