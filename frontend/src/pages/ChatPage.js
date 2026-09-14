import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, User, Send,
  Sparkles, Copy, ThumbsUp, ThumbsDown
} from 'lucide-react';
import { sendChatMessage } from '../api/client';
import '../styles/ChatPage.css';

// Quick-action chips shown under the welcome message and after each bot
// reply. These map to messages the real backend (/api/v1/chat in main.py)
// actually understands — it does simple keyword matching over the user's
// own saved receipts, so we point people at the phrases it recognizes
// instead of pretending the bot can do much more than that.
const DEFAULT_SUGGESTIONS = [
  { text: "💰 Total spend", action: "total spend" },
  { text: "📅 Spend this month", action: "how much have I spent this month" },
  { text: "🏪 Top vendor", action: "who is my top vendor" },
];

const ChatPage = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: "Hello! I'm your DigiPlanner assistant. Ask me about your total spend, this month's spend, or your top vendor — I answer using your real saved receipts.",
      timestamp: new Date(),
      suggestions: DEFAULT_SUGGESTIONS
    }
  ]);
  
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (content, type = 'user', suggestions = null) => {
    const newMessage = {
      id: Date.now(),
      type,
      content,
      timestamp: new Date(),
      suggestions: suggestions || null
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  };

  // Calls the real backend endpoint (POST /api/v1/chat) which answers
  // using the logged-in user's own saved receipts. See main.py::chat —
  // it currently recognizes "this month"/"month", "total"/"overall", and
  // "vendor"/"merchant"/"where"; anything else gets a helpful fallback.
  const fetchBotReply = async (userMessage) => {
    const data = await sendChatMessage(userMessage);
    return { content: data.reply, suggestions: DEFAULT_SUGGESTIONS };
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message
    addMessage(userMessage, 'user');
    setIsTyping(true);
    
    try {
      const response = await fetchBotReply(userMessage);
      addMessage(response.content, 'bot', response.suggestions);
    } catch (error) {
      addMessage(
        error.message || "I couldn't reach the server just now. Please try again in a moment.",
        'bot'
      );
    } finally {
      setIsTyping(false);
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage('');
    handleQuickAction(suggestion.action, suggestion.text);
  };

  const handleQuickAction = async (action, text) => {
    setIsLoading(true);
    addMessage(text, 'user');
    setIsTyping(true);

    try {
      const response = await fetchBotReply(action);
      addMessage(response.content, 'bot', response.suggestions);
    } catch (error) {
      addMessage(
        error.message || "I couldn't reach the server just now. Please try again in a moment.",
        'bot'
      );
    } finally {
      setIsTyping(false);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content);
    // You could add a toast notification here
  };

  const formatTimestamp = (timestamp) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(timestamp);
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div className="chat-title">
          <div className="title-icon">
            <Bot size={24} />
            <div className="status-indicator online" />
          </div>
          <div className="title-content">
            <h2>AI Assistant</h2>
            <p>DigiPlanner Expert • Always available</p>
          </div>
        </div>
        <div className="chat-stats">
          <div className="stat-item">
            <span className="stat-value">{messages.length}</span>
            <span className="stat-label">Messages</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">24/7</span>
            <span className="stat-label">Available</span>
          </div>
        </div>
      </div>

      <div className="chat-messages-container">
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-avatar">
                {message.type === 'bot' ? (
                  <div className="bot-avatar">
                    <Bot size={16} />
                  </div>
                ) : (
                  <div className="user-avatar">
                    <User size={16} />
                  </div>
                )}
              </div>
              
              <div className="message-content">
                <div className="message-header">
                  <span className="message-sender">
                    {message.type === 'bot' ? 'AI Assistant' : 'You'}
                  </span>
                  <span className="message-time">
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>
                
                <div className="message-text">
                  {message.content.split('\n').map((line, i) => (
                    <div key={i} className="message-line">
                      {line.startsWith('• ') ? (
                        <div className="bullet-point">
                          <span className="bullet">•</span>
                          <span>{line.substring(2)}</span>
                        </div>
                      ) : line.startsWith('**') && line.endsWith('**') ? (
                        <div className="message-section-title">
                          {line.replace(/\*\*/g, '')}
                        </div>
                      ) : (
                        <span>{line}</span>
                      )}
                    </div>
                  ))}
                </div>

                {message.suggestions && (
                  <div className="message-suggestions">
                    {message.suggestions.map((suggestion, i) => (
                      <button
                        key={i}
                        className="suggestion-chip"
                        onClick={() => handleSuggestionClick(suggestion)}
                      >
                        {suggestion.text}
                      </button>
                    ))}
                  </div>
                )}

                <div className="message-actions">
                  <button 
                    className="action-btn"
                    onClick={() => copyMessage(message.content)}
                    title="Copy message"
                  >
                    <Copy size={14} />
                  </button>
                  {message.type === 'bot' && (
                    <>
                      <button className="action-btn" title="Helpful">
                        <ThumbsUp size={14} />
                      </button>
                      <button className="action-btn" title="Not helpful">
                        <ThumbsDown size={14} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="message bot typing-indicator">
              <div className="message-avatar">
                <div className="bot-avatar">
                  <Bot size={16} />
                </div>
              </div>
              <div className="message-content">
                <div className="typing-animation">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="typing-text">AI is typing...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-input-container">
        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about your expenses, receipts, or financial insights..."
            className="chat-input"
            rows={1}
            disabled={isLoading}
          />
          <button
            className={`send-button ${inputMessage.trim() ? 'active' : ''}`}
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
          >
            {isLoading ? (
              <div className="loading-spinner" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
        
        <div className="input-footer">
          <div className="input-tips">
            <Sparkles size={14} />
            <span>Try asking about spending trends, receipt validation, or tax compliance</span>
          </div>
          <div className="input-status">
            <div className="status-indicator online" />
            <span>Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;