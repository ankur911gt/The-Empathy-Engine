import { useState } from 'react';

const EXAMPLES = [
  "I finally did it, I got into my dream university... I worked so hard for this and it actually happened... I'm so proud of myself.",
  "She was always there for me, never letting me down, always making sure I was okay. Now she's gone and I have absolutely nothing left to hold on to.",
  "You had one simple job, just one, and you completely ruined everything. I am NEVER trusting you with anything important again. Unbelievable.",
  "I heard something downstairs, and I don't know what it is. What if someone broke in? I can't move. It is so dark and I am completely alone.",
  "They just called my name on stage. I actually won first place out of five hundred people. I never thought this was even possible.",
  "The way he treated that poor waiter was absolutely disgusting. He was so rude and disrespectful for no reason at all. It made everyone uncomfortable.",
];

export default function TextInput({ onSubmit, loading }) {
  const [text, setText] = useState('');

  const handleSubmit = () => {
    if (text.trim() && !loading) {
      onSubmit(text.trim());
    }
  };

  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="space-y-4">
      {/* Examples */}
      <div className="space-y-2">
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          Try an example
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {EXAMPLES.map((example, i) => (
            <button
              key={i}
              onClick={() => setText(example)}
              className="card card-hover text-left p-3 text-[12px] text-slate-400 
                         hover:text-slate-200 transition-all duration-200 cursor-pointer"
              id={`example-prompt-${i}`}
            >
              <span className="line-clamp-2">"{example}"</span>
            </button>
          ))}
        </div>
      </div>

      {/* Textarea */}
      <div className="relative">
        <textarea
          id="text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter text to analyze emotion and generate expressive speech..."
          rows={3}
          maxLength={2000}
          className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-white 
                     placeholder-slate-600 resize-none focus:outline-none focus:ring-1 
                     focus:ring-indigo-500/30 focus:border-indigo-500/20 transition-all duration-200
                     text-sm leading-relaxed"
        />
        <div className="absolute bottom-3 right-3 text-[10px] font-mono text-slate-600">
          {text.length}/2000
        </div>
      </div>

      {/* Submit */}
      <div className="flex items-center justify-between">
        <p className="text-[10px] text-slate-600">
          <kbd className="px-1.5 py-0.5 bg-white/[0.04] rounded text-slate-500 font-mono text-[9px] border border-white/[0.06]">
            Ctrl
          </kbd>
          {' + '}
          <kbd className="px-1.5 py-0.5 bg-white/[0.04] rounded text-slate-500 font-mono text-[9px] border border-white/[0.06]">
            Enter
          </kbd>
          {' to submit'}
        </p>
        <button
          id="submit-button"
          onClick={handleSubmit}
          disabled={loading || !text.trim()}
          className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white 
                     font-semibold rounded-lg shadow-lg shadow-indigo-500/20 
                     hover:shadow-indigo-500/30 hover:scale-[1.02] 
                     disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100
                     transition-all duration-200 text-sm"
        >
          {loading ? 'Processing...' : 'Analyze & Speak'}
        </button>
      </div>
    </div>
  );
}
