export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-1">
      <span
        className="h-1.5 w-1.5 animate-bounce-dot rounded-full bg-slate-400"
        style={{ animationDelay: '0ms' }}
      />
      <span
        className="h-1.5 w-1.5 animate-bounce-dot rounded-full bg-slate-400"
        style={{ animationDelay: '150ms' }}
      />
      <span
        className="h-1.5 w-1.5 animate-bounce-dot rounded-full bg-slate-400"
        style={{ animationDelay: '300ms' }}
      />
    </div>
  );
}
