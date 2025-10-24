#!/usr/bin/env node

// Custom browser-agent-server startup script for Cloud Run
// Uses environment variables for port configuration

import { BrowserAgentServer } from './nodejs/src/lib/BrowserAgentServer.js';
import { HTTPWrapper } from './nodejs/src/lib/HTTPWrapper.js';

const WS_PORT = parseInt(process.env.EVAL_SERVER_WS_PORT || '8082');
const HTTP_PORT = parseInt(process.env.EVAL_SERVER_HTTP_PORT || '8083');
const HOST = process.env.EVAL_SERVER_HOST || '127.0.0.1';

console.log('🔧 Creating BrowserAgentServer...');
const browserAgentServer = new BrowserAgentServer({
  // No authKey - authentication disabled for automated mode
  host: HOST,
  port: WS_PORT,
  clientsDir: './clients'  // In Docker, nodejs/ is flattened to root
});

console.log('🔧 Creating HTTP wrapper...');
const httpWrapper = new HTTPWrapper(browserAgentServer, {
  port: HTTP_PORT,
  host: HOST
});

console.log('🔧 Starting BrowserAgentServer...');
await browserAgentServer.start();
console.log(`✅ BrowserAgentServer started on ws://${HOST}:${WS_PORT}`);

console.log('🔧 Starting HTTP wrapper...');
await httpWrapper.start();
console.log(`✅ HTTP API started on http://${HOST}:${HTTP_PORT}`);

console.log('⏳ Waiting for DevTools client to connect...');
console.log(`   WebSocket URL: ws://${HOST}:${WS_PORT}`);
console.log(`   HTTP API URL: http://${HOST}:${HTTP_PORT}`);
console.log('   Auth: Disabled (automated mode)');

// Add periodic status check
setInterval(() => {
  const browserAgentServerStatus = browserAgentServer.getStatus();
  const httpWrapperStatus = httpWrapper.getStatus();
  console.log(`📊 BrowserAgentServer: ${browserAgentServerStatus.connectedClients} clients, ${browserAgentServerStatus.readyClients} ready`);
  console.log(`📊 HTTP API: ${httpWrapperStatus.isRunning ? 'running' : 'stopped'} on ${httpWrapperStatus.url}`);
}, 30000);
