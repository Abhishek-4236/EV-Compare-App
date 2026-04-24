import { Mic, MicOff, Send } from 'lucide-react';

const SUGGESTIONS = [
  'Show EV cars under 15 lakh',
  'Compare Tata Nexon EV vs MG ZS EV',
  'Explain TCO for EVs',
  'I travel 35 km daily, what should I buy?',
];

export default function ChatComposer({
  textareaRef,
  input,
  loading,
  isListening,
  hasSpeechRecognition,
  onInputChange,
  onKeyDown,
  onSubmit,
  onToggleListen,
  showSuggestions,
}) {
  return (
    <div className="ev-chat-input-limit">
      {!loading && showSuggestions && (
        <div className="ev-suggestion-row">
          {SUGGESTIONS.map(suggestion => (
            <button key={suggestion} onClick={() => onSubmit(suggestion)} className="suggestion-pill" type="button">
              {suggestion}
            </button>
          ))}
        </div>
      )}

      <div className="ev-input-container">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={event => onInputChange(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Message EViq about EVs..."
        />
        <button
          className={`mic-btn ${isListening ? 'active' : ''}`}
          onClick={onToggleListen}
          title={hasSpeechRecognition ? 'Voice Input' : 'Voice input unavailable'}
          disabled={!hasSpeechRecognition}
          type="button"
        >
          {isListening ? <MicOff size={18} /> : <Mic size={18} />}
        </button>
        <button className={`send-btn ${input.trim() ? 'active' : ''}`} onClick={() => onSubmit()} disabled={loading} type="button">
          <Send size={18} />
        </button>
      </div>
      <div className="disclaimer">Answers are grounded in the current EV dataset and EViq knowledge base. Verify live prices and subsidies before relying on them.</div>
    </div>
  );
}
