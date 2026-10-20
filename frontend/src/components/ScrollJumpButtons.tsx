export function ScrollJumpButtons() {
  return (
    <div className="scroll-jump">
      <button
        type="button"
        className="btn btn-fab"
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        title="Прокрутить страницу в начало"
        aria-label="Прокрутить в начало"
      >
        ↑
      </button>
      <button
        type="button"
        className="btn btn-fab"
        onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" })}
        title="Прокрутить страницу в конец"
        aria-label="Прокрутить в конец"
      >
        ↓
      </button>
    </div>
  );
}
