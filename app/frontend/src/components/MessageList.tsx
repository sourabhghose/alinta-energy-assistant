import React from 'react';
import { Message } from '../types';
import SourceCard from './SourceCard';

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="message-list">
      {messages.map((message, index) => (
        <div key={index} className={`message ${message.role}`}>
          <div className="message-content">
            {/* Message text */}
            <div className="message-text">{message.content}</div>

            {/* Sources (only for assistant messages) */}
            {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
              <div className="sources-section">
                <h4>Sources:</h4>
                <div className="sources-list">
                  {message.sources.map((source, idx) => (
                    <SourceCard key={idx} source={source} />
                  ))}
                </div>
              </div>
            )}

            {/* Metadata (optional, for debugging) */}
            {message.metadata && message.metadata.retrieved_chunks && (
              <div className="message-metadata">
                <small>
                  Retrieved {message.metadata.retrieved_chunks} sources
                  {message.metadata.tokens_used && ` • ${message.metadata.tokens_used} tokens`}
                </small>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;
