import { useCallback, useEffect, useState } from "react";
import {
  adminLogin,
  fetchAdminSettings,
  fetchPublicSettings,
  updateAdminSettings,
  type ModelTier,
  type PublicSettings,
} from "../api";
import { ErrorNotice } from "./ErrorNotice";
import type { AppError } from "../utils/errors";

const ADMIN_UNLOCK_KEY = "stt_admin_unlocked";
const ADMIN_TOKEN_KEY = "stt_admin_token";

function readStoredToken(): string {
  return sessionStorage.getItem(ADMIN_TOKEN_KEY) || "";
}

function isStoredUnlocked(): boolean {
  return sessionStorage.getItem(ADMIN_UNLOCK_KEY) === "1" && !!readStoredToken();
}

type Props = {
  open: boolean;
  onClose: () => void;
};

export function SettingsModals({ open, onClose }: Props) {
  const [publicSettings, setPublicSettings] = useState<PublicSettings | null>(null);
  const [unlocked, setUnlocked] = useState(isStoredUnlocked);
  const [token, setToken] = useState(readStoredToken);
  const [loginUser, setLoginUser] = useState("admin");
  const [loginPass, setLoginPass] = useState("");
  const [modelTier, setModelTier] = useState<ModelTier>("medium");
  const [maxMin, setMaxMin] = useState(30);
  const [error, setError] = useState<AppError | null>(null);
  const [saving, setSaving] = useState(false);

  const clearAdminSession = useCallback(() => {
    sessionStorage.removeItem(ADMIN_UNLOCK_KEY);
    sessionStorage.removeItem(ADMIN_TOKEN_KEY);
    setToken("");
    setUnlocked(false);
  }, []);

  const handleAuthFailure = useCallback(
    (err: AppError) => {
      if (err.type === "admin_unauthorized" || err.type === "admin_invalid_credentials") {
        clearAdminSession();
        if (err.type === "admin_unauthorized") {
          setError({
            type: "admin_unauthorized",
            message: "Сессия администратора истекла. Войдите снова.",
          });
        } else {
          setError(err);
        }
        return;
      }
      setError(err);
    },
    [clearAdminSession],
  );

  useEffect(() => {
    if (!open) return;
    setError(null);
    if (sessionStorage.getItem(ADMIN_UNLOCK_KEY) === "1" && !readStoredToken()) {
      clearAdminSession();
    }
    void fetchPublicSettings()
      .then(setPublicSettings)
      .catch((e) => handleAuthFailure(e as AppError));
  }, [open, clearAdminSession, handleAuthFailure]);

  useEffect(() => {
    if (!open || !unlocked || !token) return;
    void fetchAdminSettings(token)
      .then((s) => {
        setModelTier(s.model_tier);
        setMaxMin(s.max_duration_minutes);
      })
      .catch((e) => handleAuthFailure(e as AppError));
  }, [open, unlocked, token, handleAuthFailure]);

  if (!open) return null;

  async function handleLogin(ev: React.FormEvent) {
    ev.preventDefault();
    setError(null);
    try {
      const { token: t } = await adminLogin(loginUser, loginPass);
      sessionStorage.setItem(ADMIN_UNLOCK_KEY, "1");
      sessionStorage.setItem(ADMIN_TOKEN_KEY, t);
      setToken(t);
      setUnlocked(true);
      setLoginPass("");
      const s = await fetchAdminSettings(t);
      setModelTier(s.model_tier);
      setMaxMin(s.max_duration_minutes);
    } catch (e) {
      handleAuthFailure(e as AppError);
    }
  }

  async function handleSave(ev: React.FormEvent) {
    ev.preventDefault();
    if (!token) return;
    setSaving(true);
    setError(null);
    try {
      const s = await updateAdminSettings(token, {
        model_tier: modelTier,
        max_duration_minutes: maxMin,
      });
      setModelTier(s.model_tier);
      setMaxMin(s.max_duration_minutes);
      onClose();
    } catch (e) {
      handleAuthFailure(e as AppError);
    } finally {
      setSaving(false);
    }
  }

  const durationMin = publicSettings?.min_duration_minutes ?? 10;
  const durationMax = publicSettings?.max_duration_limit_minutes ?? 120;
  const showLogin = !unlocked || !token;

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div className="modal card" onClick={(e) => e.stopPropagation()} role="dialog" aria-labelledby="settings-title">
        <div className="modal-head">
          <h2 id="settings-title" className="section-title">
            Настройки системы
          </h2>
          <button
            type="button"
            className="error-dismiss"
            onClick={onClose}
            aria-label="Закрыть"
            title="Закрыть окно настроек"
          >
            ×
          </button>
        </div>

        {error && <ErrorNotice error={error} onDismiss={() => setError(null)} />}

        {showLogin ? (
          <form className="stack gap-md" onSubmit={(e) => void handleLogin(e)}>
            <p className="muted small">Введите учётные данные администратора (один раз за сессию браузера).</p>
            <label className="field">
              <span className="field-label">Логин</span>
              <input value={loginUser} onChange={(e) => setLoginUser(e.target.value)} autoComplete="username" />
            </label>
            <label className="field">
              <span className="field-label">Пароль</span>
              <input
                type="password"
                value={loginPass}
                onChange={(e) => setLoginPass(e.target.value)}
                autoComplete="current-password"
              />
            </label>
            <button type="submit" className="btn btn-primary" title="Войти в панель администратора">
              Войти
            </button>
          </form>
        ) : (
          <form className="stack gap-md" onSubmit={(e) => void handleSave(e)}>
            <label className="field">
              <span className="field-label">Модель распознавания</span>
              <select value={modelTier} onChange={(e) => setModelTier(e.target.value as ModelTier)}>
                <option value="light">Лёгкая</option>
                <option value="medium">Средняя</option>
                <option value="heavy">Тяжёлая</option>
              </select>
            </label>
            <div className="field duration-limit-field">
              <div className="duration-limit-head">
                <span className="field-label">Макс. длительность загружаемого файла</span>
                <span className="duration-limit-value">{maxMin} мин</span>
              </div>
              <input
                type="range"
                className="duration-limit-slider"
                min={durationMin}
                max={durationMax}
                step={1}
                value={maxMin}
                onChange={(e) => setMaxMin(Number(e.target.value))}
                title={`Лимит: от ${durationMin} до ${durationMax} минут`}
              />
              <div className="duration-limit-scale">
                <span>{durationMin} мин</span>
                <span>{durationMax} мин</span>
              </div>
              <p className="muted small">
                Файлы длиннее {maxMin} мин не принимаются. Диапазон: {durationMin}–{durationMax} мин.
              </p>
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
              title="Сохранить модель и лимит длительности для всех пользователей"
            >
              {saving ? "Сохранение…" : "Применить для всех"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
