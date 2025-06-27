import React, { useEffect, useRef } from 'react';
import { User, Bot } from 'lucide-react';
import { format } from 'date-fns';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ConversationPanelProps {
  messages: Message[];
  className?: string;
  isLoading?: boolean;
}

export const ConversationPanel: React.FC<ConversationPanelProps> = ({
  messages,
  className = '',
  isLoading = false,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="border-b p-4">
        <h3 className="text-lg font-semibold">Conversation History</h3>
      </div>

      {/* Messages container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center space-x-2 text-gray-500">
                <Bot className="w-5 h-5" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            )}
          </>
        )}
        
        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

// Message bubble component
const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex items-start space-x-2 max-w-[80%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-500' : 'bg-gray-600'
        }`}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>
        
        {/* Message content */}
        <div className="flex flex-col">
          <div className={`rounded-lg px-4 py-2 ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-white'
          }`}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>
          
          {/* Timestamp */}
          <span className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {format(message.timestamp, 'HH:mm')}
          </span>
        </div>
      </div>
    </div>
  );
}; 