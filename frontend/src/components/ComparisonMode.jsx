import { API_BASE } from '../api/client';

const EMOTION_CONFIG = {
  joy:      { color: '#fbbf24', emoji: '😊' },
  sadness:  { color: '#60a5fa', emoji: '😢' },
  anger:    { color: '#f87171', emoji: '😠' },
  fear:     { color: '#a78bfa', emoji: '😨' },
  surprise: { color: '#f472b6', emoji: '😲' },
  disgust:  { color: '#34d399', emoji: '🤢' },
  neutral:  { color: '#94a3b8', emoji: '😐' },
};

export default function ComparisonMode({ results }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="space-y-4 fade-in-up">
      <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
        Emotion Comparison — Same Text, Different Vocal Profiles
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {results.map((r, i) => {
          const config = EMOTION_CONFIG[r.emotion] || EMOTION_CONFIG.neutral;
          return (
            <div key={i} className="card p-4 space-y-3">
              {/* Emotion header */}
              <div className="flex items-center gap-2">
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center text-xl"
                  style={{ background: `${config.color}15`, border: `1px solid ${config.color}30` }}
                >
                  {config.emoji}
                </div>
                <div>
                  <h4 className="text-lg font-bold capitalize" style={{ color: config.color }}>
                    {r.emotion}
                  </h4>
                  <p className="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">
                    {Math.round(r.intensity * 100)}% intensity
                  </p>
                </div>
              </div>

              {/* Voice params */}
              <div className="space-y-1.5">
                {[
                  { label: 'Rate', value: r.voice_params.rate },
                  { label: 'Pitch', value: r.voice_params.pitch },
                  { label: 'Volume', value: r.voice_params.volume },
                ].map(({ label, value }) => {
                  const num = parseInt(value);
                  const pct = Math.min(Math.abs(num) / 50, 1) * 100;
                  return (
                    <div key={label} className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-500 w-10">{label}</span>
                      <div className="flex-1 h-1 bg-white/[0.04] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.max(pct, 2)}%`,
                            background: `${config.color}80`,
                          }}
                        />
                      </div>
                      <span className="text-[10px] font-mono font-bold text-slate-300 w-10 text-right">
                        {value}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Audio */}
              <audio
                controls
                src={`${API_BASE}${r.audio_url}`}
                className="w-full h-8"
                style={{ filter: 'invert(1)', opacity: 0.5 }}
              />

              {/* Download */}
              <a
                href={`${API_BASE}${r.audio_url}`}
                download={`${r.emotion}_speech.mp3`}
                className="block text-center text-[10px] text-slate-500 hover:text-white transition-colors"
              >
                ⬇ Download
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
}
