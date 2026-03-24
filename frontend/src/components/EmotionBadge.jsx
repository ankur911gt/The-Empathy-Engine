const EMOTION_CONFIG = {
  joy:      { color: '#fbbf24', emoji: '😊', label: 'Joy' },
  sadness:  { color: '#60a5fa', emoji: '😢', label: 'Sadness' },
  anger:    { color: '#f87171', emoji: '😠', label: 'Anger' },
  fear:     { color: '#a78bfa', emoji: '😨', label: 'Fear' },
  disgust:  { color: '#34d399', emoji: '🤢', label: 'Disgust' },
  surprise: { color: '#f472b6', emoji: '😲', label: 'Surprise' },
  neutral:  { color: '#94a3b8', emoji: '😐', label: 'Neutral' },
};

export default function EmotionBadge({ emotion, intensity, all_scores }) {
  const config = EMOTION_CONFIG[emotion] || EMOTION_CONFIG.neutral;
  const percentage = Math.round(intensity * 100);
  const sortedScores = Object.entries(all_scores).sort(([, a], [, b]) => b - a);

  return (
    <div className="space-y-5 fade-in-up">
      {/* Main emotion */}
      <div className="flex items-center gap-4">
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl"
          style={{ background: `${config.color}15`, border: `1px solid ${config.color}30` }}
        >
          {config.emoji}
        </div>
        <div className="flex-1">
          <div className="flex items-baseline gap-2">
            <h3 className="text-2xl font-extrabold capitalize" style={{ color: config.color }}>
              {emotion}
            </h3>
            <span className="text-sm font-mono font-bold text-slate-400">
              {percentage}%
            </span>
          </div>
          <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mt-0.5">
            Primary detected emotion
          </p>
        </div>
      </div>

      {/* Intensity bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
            Confidence / Intensity
          </span>
          <span className="text-xs font-mono font-bold" style={{ color: config.color }}>
            {percentage}%
          </span>
        </div>
        <div className="h-2 bg-white/[0.04] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-1000 ease-out"
            style={{
              width: `${percentage}%`,
              background: `linear-gradient(90deg, ${config.color}80, ${config.color})`,
            }}
          />
        </div>
      </div>

      {/* All scores */}
      <div className="space-y-2">
        <h4 className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
          Full Emotion Spectrum
        </h4>
        {sortedScores.map(([emo, score]) => {
          const emoConfig = EMOTION_CONFIG[emo] || EMOTION_CONFIG.neutral;
          const pct = Math.round(score * 100);
          return (
            <div key={emo} className="flex items-center gap-2">
              <span className="text-sm w-5">{emoConfig.emoji}</span>
              <span className="text-[11px] font-medium capitalize w-14" style={{ color: emoConfig.color }}>
                {emo}
              </span>
              <div className="flex-1 h-1 bg-white/[0.04] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${Math.max(pct, 1)}%`,
                    background: `${emoConfig.color}90`,
                  }}
                />
              </div>
              <span className="text-[10px] font-mono text-slate-500 w-8 text-right">
                {pct}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
