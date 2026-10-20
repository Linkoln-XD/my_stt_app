import { errorTypeLabel, type AppError } from "../utils/errors";

type Props = {
  error: AppError;
  onDismiss?: () => void;
};

export function ErrorNotice({ error, onDismiss }: Props) {
  return (
    <div className="alert alert-error error-notice" role="alert">
      <div className="error-notice-head">
        <strong>{errorTypeLabel(error.type)}</strong>
        {onDismiss && (
          <button
            type="button"
            className="error-dismiss"
            onClick={onDismiss}
            aria-label="Закрыть"
            title="Закрыть сообщение об ошибке"
          >
            ×
          </button>
        )}
      </div>
      <p className="error-notice-msg">{error.message}</p>
      <p className="muted small error-code">Код: {error.type}</p>
    </div>
  );
}
