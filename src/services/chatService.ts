/**
 * Chat Service - integrates ChatStore with API calls
 */

import { useChatStore } from '../stores/chatStore';
import { useStatsStore } from '../stores/statsStore';
import { ApiClient } from '../api/client';

export interface ChatMessage {
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  tokens?: number;
  modelUsed?: string;
  responseTime?: number;
}

export interface ChatResponse {
  id: string;
  content: string;
  tokens: number;
  responseTime: number;
  model: string;
}

export class ChatService {
  private apiClient: ApiClient;
  private chatStore: ReturnType<typeof useChatStore>;
  private statsStore: ReturnType<typeof useStatsStore>;

  constructor(apiBaseUrl: string = 'http://localhost:3000/api') {
    this.apiClient = new ApiClient({
      baseUrl: apiBaseUrl,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    this.chatStore = useChatStore();
    this.statsStore = useStatsStore();
  }

  async sendMessage(
    conversationId: string,
    message: string,
    model?: string,
    temperature?: number
  ): Promise<ChatResponse | null> {
    try {
      // Add user message to store immediately
      const messageId = this.chatStore.addMessage(conversationId, {
        role: 'user',
        content: message,
        tokens: this.estimateTokens(message),
        model,
        timestamp: new Date(),
      });

      const startTime = Date.now();

      // Send to API
      const response = await this.apiClient.post<ChatResponse>('/chat/message', {
        conversationId,
        message,
        model,
        temperature: temperature ?? 0.7,
      });

      if (!response.data || response.error) {
        throw new Error(response.error || 'Failed to get response');
      }

      const responseTime = Date.now() - startTime;

      // Add assistant message to store
      this.chatStore.addMessage(conversationId, {
        role: 'assistant',
        content: response.data.content,
        tokens: response.data.tokens,
        model: response.data.model,
        timestamp: new Date(),
        metadata: {
          responseTime,
        },
      });

      // Record usage in stats
      this.statsStore.recordUsage({
        tokensUsed: (this.estimateTokens(message) || 0) + response.data.tokens,
        messagesCount: 1,
        modelUsed: response.data.model,
        cost: this.calculateCost(response.data.model, response.data.tokens),
      });

      this.statsStore.updateModelStats(
        response.data.model,
        'anthropic',
        response.data.tokens,
        this.calculateCost(response.data.model, response.data.tokens)
      );

      return response.data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      this.chatStore.addMessage(conversationId, {
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date(),
        metadata: {
          error: true,
        },
      });
      return null;
    }
  }

  async createConversation(title?: string): Promise<string> {
    try {
      const response = await this.apiClient.post<{ id: string }>('/chat/conversations', {
        title: title || 'New Conversation',
      });

      if (!response.data?.id || response.error) {
        throw new Error(response.error || 'Failed to create conversation');
      }

      const conversationId = response.data.id;
      this.chatStore.createConversation(conversationId, title || 'New Conversation');
      return conversationId;
    } catch (error) {
      throw new Error(`Failed to create conversation: ${error}`);
    }
  }

  async deleteConversation(conversationId: string): Promise<boolean> {
    try {
      const response = await this.apiClient.post<{ success: boolean }>(
        `/chat/conversations/${conversationId}/delete`,
        {}
      );

      if (response.error) {
        throw new Error(response.error);
      }

      this.chatStore.deleteConversation(conversationId);
      return true;
    } catch (error) {
      throw new Error(`Failed to delete conversation: ${error}`);
    }
  }

  async getConversations(): Promise<any[]> {
    try {
      const response = await this.apiClient.get<any[]>('/chat/conversations');

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to fetch conversations: ${error}`);
    }
  }

  private estimateTokens(text: string): number {
    return Math.ceil(text.length / 4);
  }

  private calculateCost(model: string, tokens: number): number {
    const costPerMillion: Record<string, number> = {
      'claude-opus': 15,
      'claude-sonnet': 3,
      'claude-haiku': 0.8,
    };

    const cost = costPerMillion[model.toLowerCase()] || 1;
    return (cost / 1000000) * tokens;
  }

  setBaseUrl(url: string): void {
    this.apiClient.setBaseUrl(url);
  }

  setAuthToken(token: string): void {
    this.apiClient.setAuthHeader(token, 'Bearer');
  }
}
