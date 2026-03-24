import { API_BASE } from '../api/client';

export default function AudioPlayer({ audio_url }) {
  const fullUrl = `${API_BASE}${audio_url}`;

  return (
    <div className="card p-4 space-y-3 fade-in-up">
      <div className="flex items-center justify-between">
        <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          Generated Speech
        </h4>
        <a
          href={fullUrl}
          download="empathy_engine_speech.mp3"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white/[0.04] hover:bg-white/[0.08] 
                     rounded-lg text-[10px] font-semibold text-slate-400 hover:text-white 
                     transition-all duration-200 border border-white/[0.06]"
        >
          <span>⬇</span>
          <span>Download MP3</span>
        </a>
      </div>
      <audio
        controls
        autoPlay
        src={fullUrl}
        className="w-full"
        style={{ filter: 'invert(1)', opacity: 0.6 }}
      />
    </div>
  );
}
