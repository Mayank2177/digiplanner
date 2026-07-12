import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, User, Send,
  Sparkles, Copy, ThumbsUp, ThumbsDown
} from 'lucide-react';
import '../styles/ChatPage.css';

const ChatPage = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: "Hello! I'm your AI assistant for DigiPlanner. I can help you with expense analysis, receipt queries, and financial insights. How can I assist you today?",
      timestamp: new Date(),
      suggestions: [
        { text: "📊 Analyze my spending patterns", action: "spending_analysis" },
        { text: "🧾 Show recent receipts", action: "recent_receipts" },
        { text: "💰 Monthly expense summary", action: "monthly_summary" },
        { text: "🏷️ Help with categorization", action: "categorization_help" }
      ]
    }
  ]);
  
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Sample data for demonstrations
  const sampleData = {
    totalSpending: 84230,
    monthlySpending: 71000,
    receiptCount: 128,
    pendingReceipts: 3,
    topCategories: [
      { name: 'Travel', amount: 32000, percentage: 38 },
      { name: 'Food', amount: 20000, percentage: 24 },
      { name: 'Utilities', amount: 15000, percentage: 18 },
      { name: 'Office', amount: 10000, percentage: 12 },
      { name: 'Other', amount: 7000, percentage: 8 }
    ],
    recentReceipts: [
      { vendor: 'Cafe Turmeric', amount: 640, date: 'Jul 08', category: 'Food' },
      { vendor: 'IndiGo Airlines', amount: 5240, date: 'Jul 06', category: 'Travel' },
      { vendor: 'BESCOM Electricity', amount: 2380, date: 'Jul 02', category: 'Utility' }
    ]
  };

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

  const simulateTyping = async (duration = 1500) => {
    setIsTyping(true);
    await new Promise(resolve => setTimeout(resolve, duration));
    setIsTyping(false);
  };

  const generateBotResponse = async (userMessage) => {
    const message = userMessage.toLowerCase();
    
    // Analyze user intent and provide relevant responses
    if (message.includes('spending') || message.includes('expense') || message.includes('money')) {
      return {
        content: `📊 **Spending Analysis**\n\nHere's your spending overview:\n• **Total this month:** ₹${sampleData.monthlySpending.toLocaleString()}\n• **Year to date:** ₹${sampleData.totalSpending.toLocaleString()}\n• **Average daily:** ₹${Math.round(sampleData.monthlySpending / 30).toLocaleString()}\n\n**Top spending categories:**\n${sampleData.topCategories.slice(0, 3).map(cat => `• ${cat.name}: ₹${cat.amount.toLocaleString()} (${cat.percentage}%)`).join('\n')}\n\nWould you like me to dive deeper into any specific category?`,
        suggestions: [
          { text: "🔍 Analyze travel expenses", action: "travel_analysis" },
          { text: "📈 Show spending trends", action: "spending_trends" },
          { text: "⚡ Cost reduction tips", action: "cost_tips" }
        ]
      };
    }
    
    if (message.includes('receipt') || message.includes('document')) {
      return {
        content: `🧾 **Recent Receipts Overview**\n\nYou have **${sampleData.receiptCount}** receipts processed this month:\n\n${sampleData.recentReceipts.map(receipt => 
          `• **${receipt.vendor}** - ₹${receipt.amount} (${receipt.date})\n  Category: ${receipt.category}`
        ).join('\n\n')}\n\n**Status Summary:**\n• ✅ Validated: ${sampleData.receiptCount - sampleData.pendingReceipts}\n• ⏳ Pending review: ${sampleData.pendingReceipts}\n• 🔍 Flagged for attention: 1`,
        suggestions: [
          { text: "📋 Show all pending receipts", action: "pending_receipts" },
          { text: "🔍 Search specific receipt", action: "search_receipt" },
          { text: "📤 Upload new receipt", action: "upload_receipt" }
        ]
      };
    }
    
    if (message.includes('tax') || message.includes('gst') || message.includes('compliance')) {
      return {
        content: `💼 **Tax & Compliance Summary**\n\n**This Month's Tax Overview:**\n• Total tax paid: ₹6,738\n• Average tax rate: 8.2%\n• GST compliance: ✅ 98% verified\n\n**Recent Tax Activities:**\n• 15 receipts auto-validated for GST\n• 2 receipts flagged for tax rate review\n• 1 vendor GSTIN verification pending\n\n**Compliance Status:**\n• ✅ All major transactions documented\n• ⚠️ 2 receipts need manual review\n• 📋 Monthly tax report ready for download`,
        suggestions: [
          { text: "📊 Generate tax report", action: "tax_report" },
          { text: "⚠️ Review flagged items", action: "review_flags" },
          { text: "🏢 Vendor compliance check", action: "vendor_compliance" }
        ]
      };
    }
    
    if (message.includes('category') || message.includes('categorize') || message.includes('classification')) {
      return {
        content: `🏷️ **Expense Categorization Help**\n\nI can help you better organize your expenses:\n\n**Current Categories:**\n${sampleData.topCategories.map(cat => 
          `• **${cat.name}**: ₹${cat.amount.toLocaleString()} (${cat.percentage}%)`
        ).join('\n')}\n\n**Smart Categorization Features:**\n• 🤖 Auto-categorize by merchant\n• 📍 Location-based categorization\n• 🔄 Bulk re-categorization tools\n• ✏️ Custom category creation\n\n**Tips for Better Organization:**\n• Use subcategories for detailed tracking\n• Set up rules for recurring merchants\n• Review and adjust categories monthly`,
        suggestions: [
          { text: "🔧 Set up auto-categorization", action: "auto_categorize" },
          { text: "📝 Create custom categories", action: "custom_categories" },
          { text: "🔄 Bulk categorize receipts", action: "bulk_categorize" }
        ]
      };
    }
    
    if (message.includes('trend') || message.includes('pattern') || message.includes('analysis')) {
      return {
        content: `📈 **Spending Trends & Patterns**\n\n**Monthly Trend Analysis:**\n• This month: ₹${sampleData.monthlySpending.toLocaleString()} (↑12% vs last month)\n• Highest category: Travel (₹32,000)\n• Fastest growing: Food expenses (↑18%)\n• Most stable: Utilities (±2%)\n\n**Spending Patterns Detected:**\n• 🎯 Peak spending: First week of month\n• 📅 Heaviest days: Mondays & Fridays\n• 🕐 Time pattern: 60% expenses between 9 AM - 6 PM\n• 💳 Payment preference: 75% digital payments\n\n**Insights & Recommendations:**\n• Consider setting weekly spending limits\n• Review travel expenses for optimization\n• Food expenses trending up - track dining vs groceries`,
        suggestions: [
          { text: "📊 Detailed trend report", action: "trend_report" },
          { text: "⚡ Set spending alerts", action: "spending_alerts" },
          { text: "🎯 Create budget goals", action: "budget_goals" }
        ]
      };
    }
    
    // Default response for general queries
    return {
      content: `I understand you're asking about "${userMessage}". I'm here to help with your expense management needs!\n\n**I can assist with:**\n• 📊 Spending analysis and trends\n• 🧾 Receipt management and search\n• 💰 Budget tracking and alerts\n• 🏷️ Expense categorization\n• 📈 Financial reporting\n• 🔍 Transaction validation\n• 💼 Tax compliance and GST\n\nWhat specific area would you like to explore?`,
      suggestions: [
        { text: "📊 Show my spending dashboard", action: "dashboard" },
        { text: "🔍 Search specific transactions", action: "search" },
        { text: "💡 Get expense insights", action: "insights" },
        { text: "📋 Help with setup", action: "setup_help" }
      ]
    };
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message
    addMessage(userMessage, 'user');

    // Simulate typing and generate response
    await simulateTyping();
    
    try {
      const response = await generateBotResponse(userMessage);
      addMessage(response.content, 'bot', response.suggestions);
    } catch (error) {
      addMessage(
        "I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
        'bot'
      );
    } finally {
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
    
    await simulateTyping();
    
    // Handle specific actions
    let response;
    switch (action) {
      case 'spending_analysis':
        response = await generateBotResponse('show me spending analysis');
        break;
      case 'recent_receipts':
        response = await generateBotResponse('show recent receipts');
        break;
      case 'monthly_summary':
        response = await generateBotResponse('monthly expense summary');
        break;
      case 'categorization_help':
        response = await generateBotResponse('help with categorization');
        break;
      default:
        response = {
          content: `I'm working on the "${action}" feature. In the meantime, you can ask me about spending analysis, receipt management, or tax compliance.`,
          suggestions: [
            { text: "📊 View spending overview", action: "spending_analysis" },
            { text: "🧾 Check recent receipts", action: "recent_receipts" },
            { text: "💼 Tax compliance status", action: "tax_compliance" }
          ]
        };
    }
    
    addMessage(response.content, 'bot', response.suggestions);
    setIsLoading(false);
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