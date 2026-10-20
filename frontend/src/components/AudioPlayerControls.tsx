type Props = {
  src: string;
  audioRef: React.RefObject<HTMLAudioElement | null>;
};

/** Native `<audio controls>` — volume and mute are in the browser player UI. */
export function AudioPlayerControls({ src, audioRef }: Props) {
  return <audio ref={audioRef} src={src} controls className="audio-controls" />;
}
