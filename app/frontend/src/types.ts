/**
 * Type definitions for Alinta Energy Assistant frontend
 */

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  metadata?: Record<string, any>;
  timestamp?: string;
}

export interface Source {
  title: string;
  url: string;
}

export interface ChatRequest {
  question: string;
  conversation_history?: Array<{
    role: string;
    content: string;
  }>;
  top_k?: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  metadata?: Record<string, any>;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
}
