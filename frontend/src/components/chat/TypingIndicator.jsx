import { Bot } from 'lucide-react';

export default function TypingIndicator() {
  return (
    <div className="ev-msg-row bot">
      <div className="ev-avatar bot"><Bot size={16} /></div>
      <div className="ev-msg-bubble bot typing">
        <div className="typing-dots"><span></span><span></span><span></span></div>
      </div>
    </div>
  );
}
