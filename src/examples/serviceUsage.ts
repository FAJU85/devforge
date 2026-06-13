/**
 * Service Usage Examples - demonstrates how to use services and API clients
 */

import {
  ServiceContainer,
  ChatService,
  RepositoryService,
  ConfigService,
  ContextService,
} from '../services';
import { useChatStore } from '../stores/chatStore';
import { useConfigStore } from '../stores/configStore';

/**
 * Example 1: Initialize services and send a chat message
 */
export async function example1_sendMessage() {
  // Initialize the service container
  const services = ServiceContainer.initialize({
    apiBaseUrl: 'http://localhost:3000/api',
    authToken: 'your-api-token',
  });

  // Get chat service
  const chatService = services.getChat();

  // Create a conversation
  const conversationId = await chatService.createConversation('My Conversation');

  // Send a message
  const response = await chatService.sendMessage(
    conversationId,
    'What is TypeScript?',
    'claude-opus',
    0.7
  );

  console.log('Response:', response);
}

/**
 * Example 2: Load a repository and explore its structure
 */
export async function example2_exploreRepository() {
  const services = ServiceContainer.initialize({
    apiBaseUrl: 'http://localhost:3000/api',
  });

  const repoService = services.getRepository();

  // Load repository info
  const repoInfo = await repoService.loadRepository('/path/to/repo');
  console.log('Repository:', repoInfo);

  // Load file tree
  const fileTree = await repoService.loadFileTree('/path/to/repo', 3);
  console.log('File tree:', fileTree);

  // Search for files
  const searchResults = await repoService.searchFiles('/path/to/repo', 'component');
  console.log('Search results:', searchResults);

  // Get code statistics
  const stats = await repoService.getCodeStats('/path/to/repo');
  console.log('Code stats:', stats);
}

/**
 * Example 3: Manage configuration and API keys
 */
export async function example3_manageConfig() {
  const services = ServiceContainer.initialize({
    apiBaseUrl: 'http://localhost:3000/api',
  });

  const configService = services.getConfig();
  const configStore = useConfigStore();

  // Load providers
  const providers = await configService.loadProviders();
  console.log('Available providers:', providers);

  // Load models
  const models = await configService.loadModels();
  console.log('Available models:', models);

  // Create API key
  const apiKey = await configService.createAPIKey('anthropic', 'sk-...');
  console.log('Created API key:', apiKey);

  // Validate API key
  const isValid = await configService.validateAPIKey('anthropic', 'sk-...');
  console.log('API key valid:', isValid);

  // Load feature flags
  const flags = await configService.loadFeatureFlags();
  console.log('Feature flags:', flags);

  // Check if feature is enabled
  const isEnabled = await configService.isFeatureEnabled('canaryDeployment');
  console.log('Feature enabled:', isEnabled);

  // Get system status
  const status = await configService.getSystemStatus();
  console.log('System status:', status);
}

/**
 * Example 4: Build context from repository files
 */
export async function example4_buildContext() {
  const services = ServiceContainer.initialize({
    apiBaseUrl: 'http://localhost:3000/api',
  });

  const contextService = services.getContext();
  const contextStore = useContextStore();

  // Add files to context
  await contextService.addFileToContext(
    '/path/to/repo',
    'src/components/Button.tsx'
  );

  // Add multiple files
  await contextService.addMultipleFilesToContext('/path/to/repo', [
    'src/components/Input.tsx',
    'src/components/Dialog.tsx',
    'src/types/ui.ts',
  ]);

  // Get context summary
  const summary = contextService.getContextSummary();
  console.log('Context summary:', summary);
  console.log(`Used ${summary.percentageUsed.toFixed(1)}% of available tokens`);

  // Search and add files automatically
  const foundFiles = await contextService.searchAndAddFiles(
    '/path/to/repo',
    'store',
    5
  );
  console.log('Found and added files:', foundFiles);

  // Check available space
  const hasRoom = contextService.hasRoom(1000);
  console.log('Has room for 1000 tokens:', hasRoom);
}

/**
 * Example 5: Complete workflow - chat with codebase context
 */
export async function example5_chatWithContext() {
  const services = ServiceContainer.initialize({
    apiBaseUrl: 'http://localhost:3000/api',
    authToken: 'your-api-token',
  });

  const chatService = services.getChat();
  const contextService = services.getContext();
  const repoService = services.getRepository();

  // Load and analyze repository
  const repoInfo = await repoService.loadRepository('/path/to/repo');
  console.log('Analyzing repository:', repoInfo?.name);

  // Build context from important files
  const contextFiles = [
    'src/index.ts',
    'src/types/index.ts',
    'src/stores/chatStore.ts',
    'src/api/client.ts',
  ];

  console.log('Building context...');
  for (const file of contextFiles) {
    try {
      await contextService.addFileToContext('/path/to/repo', file);
    } catch (error) {
      console.warn(`Failed to add ${file}:`, error);
    }
  }

  const contextSummary = contextService.getContextSummary();
  console.log(`Context ready: ${contextSummary.filesCount} files, ${contextSummary.totalTokens} tokens`);

  // Create conversation and start chatting
  const conversationId = await chatService.createConversation('Code Review');

  // Ask question with context
  const response = await chatService.sendMessage(
    conversationId,
    'Can you review the API client implementation and suggest improvements?',
    'claude-opus',
    0.5
  );

  console.log('Claude response:', response?.content);
}

/**
 * Example 6: Monitor service health
 */
export async function example6_serviceHealth() {
  const services = ServiceContainer.initialize({
    apiBaseUrl: 'http://localhost:3000/api',
  });

  // Check health
  const health = await services.healthCheck();
  console.log('Service health:', health);

  if (health.healthy) {
    console.log('✓ All services are healthy');
  } else {
    console.log('✗ Some services are degraded');
  }
}

/**
 * Example 7: Update service configuration at runtime
 */
export async function example7_updateConfig() {
  const services = ServiceContainer.initialize({
    apiBaseUrl: 'http://localhost:3000/api',
  });

  // Get current config
  let config = services.getCurrentConfig();
  console.log('Current config:', config);

  // Update to different API endpoint
  services.setBaseUrl('http://api-staging.example.com/api');

  // Update auth token
  services.setAuthToken('new-api-token');

  // Check updated config
  config = services.getCurrentConfig();
  console.log('Updated config:', config);
}

/**
 * Example 8: Error handling with services
 */
export async function example8_errorHandling() {
  const services = ServiceContainer.initialize({
    apiBaseUrl: 'http://localhost:3000/api',
  });

  const chatService = services.getChat();

  try {
    // This will fail if API is not available
    const conversationId = await chatService.createConversation('Test');
    console.log('Conversation created:', conversationId);
  } catch (error) {
    console.error('Error creating conversation:', error);
  }

  try {
    // Send message with error handling
    const response = await chatService.sendMessage('invalid-id', 'Hello');
    if (!response) {
      console.error('Failed to get response');
    }
  } catch (error) {
    console.error('Error sending message:', error);
  }
}
