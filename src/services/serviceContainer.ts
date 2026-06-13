/**
 * Service Container - centralized service management
 */

import { ChatService } from './chatService';
import { RepositoryService } from './repoService';
import { ConfigService } from './configService';
import { ContextService } from './contextService';

export interface ServiceConfig {
  apiBaseUrl: string;
  authToken?: string;
  timeout?: number;
}

export class ServiceContainer {
  private static instance: ServiceContainer;
  private config: ServiceConfig;

  private chatService: ChatService;
  private repoService: RepositoryService;
  private configService: ConfigService;
  private contextService: ContextService;

  private constructor(config: ServiceConfig) {
    this.config = config;

    this.chatService = new ChatService(config.apiBaseUrl);
    this.repoService = new RepositoryService(config.apiBaseUrl);
    this.configService = new ConfigService(config.apiBaseUrl);
    this.contextService = new ContextService(config.apiBaseUrl);

    if (config.authToken) {
      this.setAuthToken(config.authToken);
    }
  }

  static initialize(config: ServiceConfig): ServiceContainer {
    if (!ServiceContainer.instance) {
      ServiceContainer.instance = new ServiceContainer(config);
    }
    return ServiceContainer.instance;
  }

  static getInstance(): ServiceContainer {
    if (!ServiceContainer.instance) {
      throw new Error('ServiceContainer not initialized. Call initialize() first.');
    }
    return ServiceContainer.instance;
  }

  // Getters for individual services
  getChat(): ChatService {
    return this.chatService;
  }

  getRepository(): RepositoryService {
    return this.repoService;
  }

  getConfig(): ConfigService {
    return this.configService;
  }

  getContext(): ContextService {
    return this.contextService;
  }

  // Configuration management
  setBaseUrl(url: string): void {
    this.config.apiBaseUrl = url;
    this.chatService.setBaseUrl(url);
    this.repoService.setBaseUrl(url);
    this.configService.setBaseUrl(url);
    this.contextService.setBaseUrl(url);
  }

  setAuthToken(token: string): void {
    this.config.authToken = token;
    this.chatService.setAuthToken(token);
    this.repoService.setAuthToken(token);
    this.configService.setAuthToken(token);
    this.contextService.setAuthToken(token);
  }

  getCurrentConfig(): ServiceConfig {
    return { ...this.config };
  }

  updateConfig(updates: Partial<ServiceConfig>): void {
    if (updates.apiBaseUrl) {
      this.setBaseUrl(updates.apiBaseUrl);
    }
    if (updates.authToken) {
      this.setAuthToken(updates.authToken);
    }
    if (updates.timeout) {
      this.config.timeout = updates.timeout;
    }
  }

  // Service health checks
  async healthCheck(): Promise<{ healthy: boolean; services: Record<string, boolean> }> {
    try {
      const statusResponse = await this.configService.getSystemStatus();

      return {
        healthy: statusResponse?.status === 'healthy',
        services: {
          chat: true,
          repository: true,
          config: true,
          context: true,
        },
      };
    } catch (error) {
      return {
        healthy: false,
        services: {
          chat: false,
          repository: false,
          config: false,
          context: false,
        },
      };
    }
  }

  // Reset all services
  reset(): void {
    this.config = {
      apiBaseUrl: this.config.apiBaseUrl,
    };
    ServiceContainer.instance = new ServiceContainer(this.config);
  }
}
