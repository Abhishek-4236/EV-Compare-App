import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bot, Car, Copy, RefreshCw, User, Volume2, VolumeX } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MotionDiv = motion.div;

function SourceChips({ sources }) {
  if (!sources?.length) return null;
  return (
    <div className="ev-source-grid">
      {sources.slice(0, 4).map((source, index) => {
        const vehicleId = source.id || source.vehicle_id;
        const content = (
          <>
            {source.image_url ? (
              <img src={source.image_url} alt={source.model} className="ev-source-img" />
            ) : (
              <div className="ev-source-placeholder"><Car size={14} /></div>
            )}
            <div className="ev-source-info">
              <div className="name">{source.brand} {source.model}</div>
              <div className="price">{source.price ? `₹${(source.price / 100000).toFixed(1)}L` : 'Dataset match'}</div>
              <div className="view-hint">{vehicleId ? 'View details →' : 'From current EV dataset'}</div>
              {source.matched_on?.length ? (
                <div className="source-match-reason">{source.matched_on.slice(0, 3).join(' · ')}</div>
              ) : null}
            </div>
          </>
        );

        if (!vehicleId) {
          return <div key={index} className="ev-source-card" role="note">{content}</div>;
        }

        return (
          <Link key={index} to={`/vehicle/${vehicleId}`} className="ev-source-card" style={{ textDecoration: 'none' }}>
            {content}
          </Link>
        );
      })}
    </div>
  );
}

export default function ChatMessage({ msg, onCopy, onRetry }) {
  const isUser = msg.role === 'user';
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => () => {
    window.speechSynthesis?.cancel();
  }, []);

  const toggleSpeak = () => {
    if (!window.speechSynthesis || !msg.text) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const cleanText = msg.text.replace(/[*#`~|-]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'en-IN';
    utterance.rate = 1.05;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <MotionDiv
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
      className={`ev-msg-row ${isUser ? 'user' : 'bot'}`}
    >
      {!isUser && <div className="ev-avatar bot"><Bot size={16} /></div>}
      <div className={`ev-msg-bubble ${isUser ? 'user' : 'bot'}`}>
        {isUser ? (
          <p className="ev-msg-text">{msg.text}</p>
        ) : (
          <div className="ev-msg-markdown">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => <div className="ev-table-wrap"><table className="ev-chat-table">{children}</table></div>,
                p: ({ children }) => <p>{children}</p>,
                strong: ({ children }) => <strong className="highlight">{children}</strong>,
              }}
            >
              {msg.text}
            </ReactMarkdown>
            {msg.confidence || msg.queryType ? (
              <div className="ev-answer-meta" aria-label="Answer grounding">
                {msg.confidence ? <span>{msg.confidence === 'grounded' ? 'Grounded' : msg.confidence}</span> : null}
                {msg.queryType ? <span>{msg.queryType.replace('_', ' ')}</span> : null}
              </div>
            ) : null}
            <SourceChips sources={msg.sources} />
            <div className="ev-message-actions">
              <button className="ev-inline-action" onClick={toggleSpeak} type="button">
                {isSpeaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                {isSpeaking ? 'Stop' : 'Listen'}
              </button>
              <button className="ev-inline-action" onClick={() => onCopy?.(msg.text)} type="button">
                <Copy size={14} />
                Copy
              </button>
              {msg.retryText ? (
                <button className="ev-inline-action" onClick={() => onRetry?.(msg.retryText)} type="button">
                  <RefreshCw size={14} />
                  Retry
                </button>
              ) : null}
            </div>
          </div>
        )}
      </div>
      {isUser && <div className="ev-avatar user"><User size={16} /></div>}
    </MotionDiv>
  );
}
