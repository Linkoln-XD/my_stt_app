import { useCallback, useEffect, useState } from "react";

type Props = {
  src: string;
  audioRef: React.RefObject<HTMLAudioElement | null>;
};

const VOLUME_STEP = 0.05;

/** Native transport + always-visible volume row (native volume hides in some layouts). */
export function AudioPlayerControls({ src, audioRef }: Props) {
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);

  const applyToAudio = useCallback(
    (vol: number, isMuted: boolean) => {
      const el = audioRef.current;
      if (!el) return;
      el.volume = vol;
      el.muted = isMuted;
    },
    [audioRef],
  );

  useEffect(() => {
    applyToAudio(volume, muted);
  }, [volume, muted, src, applyToAudio]);

  const bump = (delta: number) => {
    setMuted(false);
    setVolume((v) => Math.min(1, Math.max(0, Math.round((v + delta) * 100) / 100)));
  };

  const toggleMute = () => setMuted((m) => !m);

  const volumeLabel = `${Math.round((muted ? 0 : volume) * 100)}%`;

  return (
    <div className="audio-player">
      <audio
        ref={audioRef}
        src={src}
        controls
        controlsList="nodownload noplaybackrate novolume"
        className="audio-controls"
        title="Плеер: воспроизведение, пауза и перемотка"
      />
      <div className="audio-volume" aria-label="Громкость">
        <button
          type="button"
          className="btn btn-volume"
          onClick={() => bump(-VOLUME_STEP)}
          aria-label="Тише"
          title="Тише"
        >
          −
        </button>
        <input
          type="range"
          className="audio-volume-slider"
          min={0}
          max={1}
          step={0.01}
          value={muted ? 0 : volume}
          onChange={(e) => {
            const v = Number(e.target.value);
            setMuted(v === 0);
            setVolume(v);
          }}
          aria-valuetext={volumeLabel}
          title={`Громкость: ${volumeLabel}`}
        />
        <button
          type="button"
          className="btn btn-volume"
          onClick={() => bump(VOLUME_STEP)}
          aria-label="Громче"
          title="Громче"
        >
          +
        </button>
        <button
          type="button"
          className={`btn btn-volume ${muted || volume === 0 ? "is-muted" : ""}`}
          onClick={toggleMute}
          aria-label={muted ? "Включить звук" : "Без звука"}
          title={muted ? "Включить звук" : "Без звука"}
        >
          {muted || volume === 0 ? "🔇" : "🔊"}
        </button>
      </div>
    </div>
  );
}
