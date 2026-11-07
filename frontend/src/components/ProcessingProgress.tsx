import { useEffect, useState } from "react";

/** floor: jump when stage starts; cap: slow creep target while stage runs */
const STAGE_CONFIG: Record<string, { floor: number; cap: number }> = {
  queued: { floor: 0.05, cap: 0.12 },
  waiting: { floor: 0.05, cap: 0.1 },
  prepare: { floor: 0.12, cap: 0.22 },
  model_load: { floor: 0.18, cap: 0.28 },
  asr: { floor: 0.22, cap: 0.9 },
  diarization: { floor: 0.9, cap: 0.96 },
  merge: { floor: 0.96, cap: 0.99 },
  done: { floor: 1, cap: 1 },
};

const STATUS_LINES = [
  "Слушаем аудио...",
  "Распознаем голоса...",
  "Проверяем расшифровку...",
  "Распознаем слова...",
  "Распределяем роли...",
  "Советуемся с моделью...",
  "Отправляем данные на сервер...",
  "Регулируем параметры...",
  "Ждем ответ модели...",
  "Почти готово!",
  "Ещё чуть-чуть...",
  "Совсем скоро!",
  "Ещё немного...",
  "Скоро расшифруем...",
  "Думаем...",
  "Данные почти обработаны!",
  'Думаем что такое "#@!$);%"',
];

function pickStatusLine(current?: string): string {
  let next = STATUS_LINES[Math.floor(Math.random() * STATUS_LINES.length)];
  if (current && STATUS_LINES.length > 1) {
    while (next === current) {
      next = STATUS_LINES[Math.floor(Math.random() * STATUS_LINES.length)];
    }
  }
  return next;
}

type Props = {
  stage: string;
  active: boolean;
};

/** Moves quickly at first, then slows toward stage cap (ASR creeps up to ~90%). */
export function ProcessingProgress({ stage, active }: Props) {
  const [value, setValue] = useState(0.02);
  const [statusLine, setStatusLine] = useState(pickStatusLine);

  useEffect(() => {
    if (!active) return;
    const id = window.setInterval(() => {
      setValue((prev) => {
        const cfg = STAGE_CONFIG[stage] ?? { floor: prev, cap: 0.98 };
        const cap = stage === "done" ? 1 : cfg.cap;
        let next = Math.max(prev, cfg.floor);
        const pace = next < 0.4 ? 0.14 : next < 0.75 ? 0.08 : 0.035;
        const delta = (cap - next) * pace;
        next = Math.min(cap, next + Math.max(delta, 0.001));
        return next;
      });
    }, 180);
    return () => window.clearInterval(id);
  }, [active, stage]);

  useEffect(() => {
    if (stage === "done") setValue(1);
  }, [stage]);

  useEffect(() => {
    if (!active) return;
    const id = window.setInterval(() => {
      setStatusLine((prev) => pickStatusLine(prev));
    }, 3000);
    return () => window.clearInterval(id);
  }, [active]);

  const pct = Math.round(value * 100);

  return (
    <div className="card progress-card">
      <div className="progress-top">
        <span className="progress-stage">{stageLabel(stage)}</span>
        <span className="progress-pct">{pct}%</span>
      </div>
      <div className="progress-track" aria-hidden>
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="muted small progress-msg" aria-hidden>
        {statusLine}
      </p>
    </div>
  );
}

function stageLabel(stage: string): string {
  const map: Record<string, string> = {
    queued: "В очереди",
    waiting: "Ожидание слота",
    prepare: "Подготовка аудио",
    model_load: "Загрузка модели",
    asr: "Распознавание речи",
    diarization: "Определение спикеров",
    merge: "Сборка текста",
    done: "Готово",
    error: "Ошибка",
  };
  return map[stage] ?? stage;
}
