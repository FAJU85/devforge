# Phase 6: Advanced Features & Optimization

This guide covers the advanced features and optimization capabilities added in Phase 6.

## Overview

Phase 6 enhances the API layer with:
- **Request Optimization**: Caching, deduplication, and batching
- **Real-time Communication**: WebSocket support with automatic reconnection
- **Performance Improvements**: Reduced redundant calls and network traffic
- **Developer Experience**: Easy-to-use React hooks

## Request Optimization

### 1. Request Caching

The `RequestCache` provides intelligent caching with TTL support and LRU eviction.

**Features:**
- Configurable TTL (time to live)
- LRU (Least Recently Used) eviction
- Hit/miss statistics
- Pattern-based invalidation
- Memory efficient

**Usage:**

```typescript
import { RequestCache } from '@devforge/utils';

const cache = new RequestCache({
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxSize: 100,               // max 100 entries
});

// Set cache value
cache.set('user-1', userData, 10 * 60 * 1000); // 10 minute TTL

// Get cache value
const data = cache.get('user-1');

// Check if key exists
if (cache.has('user-1')) {
  // Use cached data
}

// Invalidate by pattern
cache.invalidatePattern(/^user-/); // Invalidate all user-* keys

// Get statistics
console.log(cache.getStats());
// { hits: 10, misses: 2, hitRate: '83.33%', evictions: 0, size: 5, capacity: 100 }
```

### 2. Request Deduplication

The `RequestDeduplicator` prevents duplicate concurrent requests, returning the same promise for identical calls.

**Features:**
- Zero configuration
- Automatic deduplication
- Statistics tracking
- Memory safe

**Usage:**

```typescript
import { RequestDeduplicator } from '@devforge/utils';

const deduplicator = new RequestDeduplicator();

// First call executes the function
const promise1 = deduplicator.dedupe('api-user', async () => {
  return fetch('/api/user').then(r => r.json());
});

// Simultaneous second call returns same promise
const promise2 = deduplicator.dedupe('api-user', async () => {
  return fetch('/api/user').then(r => r.json());
});

// Both resolve to same result
console.log(promise1 === promise2); // true

// Statistics
console.log(deduplicator.getStats());
// { deduped: 1, executed: 1, pending: 0, ratio: '50.00%' }
```

### 3. Request Batching

The `RequestBatcher` batches multiple requests for improved network efficiency.

**Features:**
- Configurable batch size and wait time
- Automatic processing
- Efficiency statistics
- Optional feature (can be disabled)

**Usage:**

```typescript
import { RequestBatcher } from '@devforge/utils';

const batcher = new RequestBatcher({
  maxBatchSize: 10,    // Process after 10 requests
  maxWaitTime: 50,     // Or after 50ms
});

// Queue requests
const promise1 = batcher.add('req-1', async () => { /* ... */ });
const promise2 = batcher.add('req-2', async () => { /* ... */ });
const promise3 = batcher.add('req-3', async () => { /* ... */ });

// After maxBatchSize or maxWaitTime, batch is processed

// Flush remaining requests
await batcher.flush();

// Statistics
console.log(batcher.getStats());
// { batchCount: 1, requestCount: 3, savedRequests: 2, efficiency: '66.67%' }
```

## Optimized API Client

The `OptimizedApiClient` combines all optimization techniques.

**Features:**
- Automatic caching for GET requests
- Request deduplication across all methods
- Optional request batching
- Combined statistics
- Runtime configuration

**Usage:**

```typescript
import { OptimizedApiClient } from '@devforge/api';

const client = new OptimizedApiClient({
  baseUrl: 'http://localhost:3000/api',
  cacheEnabled: true,
  dedupeEnabled: true,
  batchEnabled: false,
  cacheTTL: 5 * 60 * 1000,
});

// Use like regular API client
const response = await client.get('/users');

// Control optimizations
client.setOptimizations({
  cache: true,
  dedupe: true,
  batch: true,
});

// Invalidate cache
client.invalidateCache(/^users-/);

// Get statistics
console.log(client.getStats());
// { cache: {...}, dedupe: {...}, batch: {...} }

// Flush batched requests
await client.flushBatch();
```

## useOptimizedApi Hook

The `useOptimizedApi` React hook makes optimization easy in components.

**Example:**

```typescript
import { useOptimizedApi } from '@devforge/hooks';

function UserComponent() {
  const api = useOptimizedApi({
    baseUrl: 'http://localhost:3000/api',
  });

  const loadUsers = async () => {
    const response = await api.get('/users');
    // Automatic caching and deduplication
  };

  const clearCache = () => {
    api.clearCache();
  };

  const updateOptimizations = () => {
    api.setOptimizations({
      cache: true,
      dedupe: true,
      batch: false,
    });
  };

  const stats = api.getStats();
  console.log('Cache hits:', stats.cache.hits);
  console.log('Dedup ratio:', stats.dedupe.ratio);

  return (
    <>
      <button onClick={loadUsers}>Load Users</button>
      <button onClick={clearCache}>Clear Cache</button>
      <button onClick={updateOptimizations}>Update Settings</button>
      <pre>{JSON.stringify(stats, null, 2)}</pre>
    </>
  );
}
```

## Real-time Communication

### WebSocket Client

The `WebSocketClient` provides full-duplex communication with automatic reconnection.

**Features:**
- Automatic reconnection with exponential backoff
- Event-based architecture
- Heartbeat mechanism
- Comprehensive statistics
- Debug logging

**Usage:**

```typescript
import { WebSocketClient } from '@devforge/api';

const client = new WebSocketClient({
  url: 'ws://localhost:3000/ws',
  reconnectAttempts: 5,
  reconnectDelay: 3000,
  heartbeatInterval: 30000,
  debug: true,
});

// Connect
await client.connect();

// Subscribe to events
const unsubscribe = client.on('update', (message) => {
  console.log('Update received:', message.data);
});

// Send message
client.send('user-action', {
  action: 'click',
  target: 'button-1',
});

// Subscribe once
client.once('sync', (message) => {
  console.log('Initial sync:', message.data);
});

// Unsubscribe
unsubscribe();

// Check connection status
if (client.isConnected()) {
  console.log('Connected');
}

// Get statistics
console.log(client.getStats());
// {
//   connected: true,
//   messagesReceived: 10,
//   messagesSent: 5,
//   reconnects: 0,
//   errors: 0,
//   ...
// }

// Disconnect
client.disconnect();
```

### useRealtimeUpdates Hook

The `useRealtimeUpdates` React hook simplifies WebSocket integration.

**Example:**

```typescript
import { useRealtimeUpdates } from '@devforge/hooks';

function ChatComponent() {
  const realtime = useRealtimeUpdates({
    url: 'ws://localhost:3000/ws',
    autoConnect: true,
    debug: false,
  });

  // Listen for messages
  useEffect(() => {
    const unsubscribe = realtime.on('message', (msg) => {
      console.log('New message:', msg.data);
      // Update component state
    });

    return unsubscribe;
  }, [realtime]);

  const sendMessage = (text) => {
    try {
      const messageId = realtime.send('message', {
        text,
        timestamp: Date.now(),
      });
      console.log('Message sent with ID:', messageId);
    } catch (error) {
      console.error('Failed to send:', error);
    }
  };

  const handleReconnect = async () => {
    try {
      await realtime.reconnect();
    } catch (error) {
      console.error('Reconnection failed:', error);
    }
  };

  return (
    <div>
      <div className="status">
        {realtime.isConnecting && 'Connecting...'}
        {realtime.isConnected && '✓ Connected'}
        {realtime.error && `Error: ${realtime.error}`}
      </div>

      <input
        type="text"
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            sendMessage(e.target.value);
            e.target.value = '';
          }
        }}
      />

      {!realtime.isConnected && (
        <button onClick={handleReconnect}>Reconnect</button>
      )}

      <pre>{JSON.stringify(realtime.getStats(), null, 2)}</pre>
    </div>
  );
}
```

## Performance Optimization Patterns

### 1. Selective Caching

Cache only important GET requests:

```typescript
const api = useOptimizedApi({
  baseUrl: 'http://localhost:3000/api',
  cacheEnabled: true,
  cacheTTL: 10 * 60 * 1000, // 10 minutes
});

// User data: cache it
const users = await api.get('/users');

// POST requests: not cached
const result = await api.post('/users', newUser);
```

### 2. Cache Invalidation

Invalidate related data when updated:

```typescript
// After updating user
await api.patch('/users/1', updatedData);

// Invalidate cached data
api.invalidateCache(/^\/users/); // Invalidate all user-related caches
```

### 3. Real-time Sync

Use WebSocket for real-time updates instead of polling:

```typescript
// BAD: Polling
setInterval(async () => {
  const data = await api.get('/notifications');
  updateUI(data);
}, 5000);

// GOOD: WebSocket
const realtime = useRealtimeUpdates({ url: 'ws://...' });
realtime.on('notification', (msg) => {
  updateUI(msg.data);
});
```

### 4. Batch Operations

Batch multiple operations:

```typescript
const api = useOptimizedApi({
  baseUrl: 'http://localhost:3000/api',
  batchEnabled: true,
  maxBatchSize: 10,
});

// Queue multiple operations
const p1 = api.post('/items', item1);
const p2 = api.post('/items', item2);
const p3 = api.post('/items', item3);

// Wait for flush or timeout
const results = await Promise.all([p1, p2, p3]);
```

## Monitoring & Statistics

### Cache Statistics

```typescript
const stats = api.getCacheStats();
// {
//   hits: 42,
//   misses: 8,
//   hitRate: '84.00%',
//   evictions: 0,
//   size: 15,
//   capacity: 100
// }
```

### Deduplication Statistics

```typescript
const stats = api.getDedupeStats();
// {
//   deduped: 5,
//   executed: 10,
//   pending: 0,
//   ratio: '50.00%'
// }
```

### Combined Statistics

```typescript
const allStats = api.getStats();
// {
//   cache: { ... },
//   dedupe: { ... },
//   batch: { ... }
// }
```

### Real-time Statistics

```typescript
const stats = realtime.getStats();
// {
//   connected: true,
//   messagesReceived: 100,
//   messagesSent: 50,
//   reconnects: 1,
//   errors: 0,
//   ...
// }
```

## Best Practices

1. **Cache Strategically**
   - Cache GET requests
   - Don't cache mutations (POST, PUT, DELETE)
   - Set appropriate TTL values

2. **Dedupe Automatically**
   - Enabled by default
   - Prevents duplicate processing
   - Zero configuration

3. **Batch When Possible**
   - Enable for bulk operations
   - Disable for real-time updates
   - Monitor batch statistics

4. **Use Real-time for Live Data**
   - Chat messages
   - Notifications
   - Collaborative editing
   - Status updates

5. **Monitor Performance**
   - Track cache hit rate
   - Monitor dedup effectiveness
   - Watch reconnection patterns
   - Profile network usage

## Troubleshooting

### High Cache Miss Rate

```typescript
// Check cache configuration
const stats = api.getCacheStats();
if (stats.hitRate < 50) {
  // Increase TTL or cache more requests
  api.setOptimizations({ cache: true });
}
```

### WebSocket Reconnection Issues

```typescript
const realtime = useRealtimeUpdates({
  url: 'ws://localhost:3000/ws',
  reconnectAttempts: 10,      // Increase attempts
  reconnectDelay: 5000,        // Increase initial delay
  debug: true,                 // Enable debug logging
});

// Monitor reconnection
console.log(realtime.getStats().reconnects);
```

### Memory Leaks

```typescript
// Always unsubscribe
useEffect(() => {
  const unsubscribe = realtime.on('message', handler);
  return () => {
    unsubscribe();
    realtime.disconnect();
  };
}, []);
```

## Migration Guide

### From Phase 5 to Phase 6

**Phase 5:**
```typescript
const api = useChat();
// No caching or optimization
```

**Phase 6:**
```typescript
const api = useOptimizedApi({
  baseUrl: 'http://localhost:3000/api',
  cacheEnabled: true,
  dedupeEnabled: true,
});

// Automatic optimization with better performance
```

## Summary

Phase 6 provides production-ready optimization and real-time features:

✅ **Request Caching** - Reduce redundant API calls
✅ **Request Deduplication** - Eliminate duplicate concurrent requests
✅ **Request Batching** - Improve network efficiency
✅ **WebSocket Support** - Real-time two-way communication
✅ **React Hooks** - Easy integration in components
✅ **Statistics Tracking** - Monitor and optimize performance
✅ **Automatic Reconnection** - Reliable real-time connections

These features enable building high-performance, responsive applications with optimal API usage.
