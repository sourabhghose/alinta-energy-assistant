import React, { useState, useRef, useEffect } from 'react';
import { Message, ChatRequest, ChatResponse } from '../types';
import MessageList from './MessageList';
import InputBox from './InputBox';
import StarterQuestions from './StarterQuestions';

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return;

    // Clear any previous errors
    setError(null);

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      // Prepare conversation history (exclude sources/metadata)
      const history = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
      }));

      // Make API request
      const requestBody: ChatRequest = {
        question,
        conversation_history: history,
      };

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get response');
      }

      const data: ChatResponse = await response.json();

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        metadata: data.metadata,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Error sending message:', err);

      const errorMessage = err instanceof Error ? err.message : 'Something went wrong';
      setError(errorMessage);

      // Add error message to chat
      const errorAssistantMessage: Message = {
        role: 'assistant',
        content: `I'm sorry, I encountered an error: ${errorMessage}. Please try again.`,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorAssistantMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleStarterQuestion = (question: string) => {
    sendMessage(question);
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-content">
          <h1>Alinta Energy Assistant</h1>
          <p>Ask me anything about plans, billing, payments, or support</p>
        </div>
        {messages.length > 0 && (
          <button onClick={clearChat} className="clear-button" title="Clear conversation">
            Clear Chat
          </button>
        )}
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-content">
              <h2>Welcome! How can I help you today?</h2>
              <p>
                I can answer questions about Alinta Energy plans, billing, payments,
                and support options. Try asking one of these:
              </p>
              <StarterQuestions onSelectQuestion={handleStarterQuestion} />
            </div>
          </div>
        ) : (
          <>
            <MessageList messages={messages} />
            {loading && (
              <div className="message assistant loading">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="loading-text">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <InputBox onSend={sendMessage} disabled={loading} />

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;
