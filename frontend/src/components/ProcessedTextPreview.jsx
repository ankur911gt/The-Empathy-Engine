import { useState } from 'react';

export default function ProcessedTextPreview({ original_text, processed_text, ssml_text }) {
  const [activeTab, setActiveTab] = useState('enriched');

  const tabs = [
    { id: 'enriched', label: 'Enriched Text', icon: '✍️' },
    { id: 'original', label: 'Original', icon: '📝' },
    ...(ssml_text ? [{ id: 'ssml', label: 'SSML Markup', icon: '🏷️' }] : []),
  ];

  return (
    <div className="card p-4 space-y-3 fade-in-up">
      {/* Tab header */}
      <div className="flex items-center gap-3">
        <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          Text Processing
        </h4>
        <div className="flex gap-1 ml-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200
                flex items-center gap-1.5
                ${activeTab === tab.id
                  ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/20'
                  : 'text-slate-500 hover:text-slate-300 border border-transparent'
                }`}
            >
              <span className="text-xs">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === 'original' && (
        <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.04]">
          <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">
            {original_text}
          </p>
        </div>
      )}

      {activeTab === 'enriched' && (
        <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.04]">
          <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">
            {processed_text}
          </p>
          {original_text !== processed_text && (
            <p className="text-[10px] text-slate-500 mt-3 italic flex items-center gap-1">
              <span>✨</span> Text enriched with emotion-specific punctuation for enhanced prosody
            </p>
          )}
        </div>
      )}

      {activeTab === 'ssml' && ssml_text && (
        <div className="code-block p-4 overflow-x-auto">
          <pre className="text-[11px] text-emerald-400 leading-relaxed whitespace-pre">
            {ssml_text}
          </pre>
          <p className="text-[10px] text-slate-500 mt-3 italic flex items-center gap-1">
            <span>🏷️</span> SSML with per-sentence prosody, emotional breaks, and emphasis
          </p>
        </div>
      )}
    </div>
  );
}
