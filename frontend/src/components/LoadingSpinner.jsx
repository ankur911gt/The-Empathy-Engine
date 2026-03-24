export default function LoadingSpinner() {
  return (
    <div className="card p-6 fade-in-up">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="w-10 h-10 rounded-full border-2 border-indigo-500/20 border-t-indigo-500 animate-spin" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Processing pipeline...</p>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Detecting emotion → Mapping voice → Enriching text → Generating SSML → Synthesizing speech
          </p>
        </div>
      </div>
    </div>
  );
}
