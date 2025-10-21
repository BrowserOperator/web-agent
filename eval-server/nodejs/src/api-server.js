// Copyright 2025 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import http from 'http';
import url from 'url';
import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import { v4 as uuidv4 } from 'uuid';

import logger from './logger.js';
// No need to import EvaluationServer - it's passed as constructor parameter

class APIServer {
  constructor(evaluationServer, port = 8081) {
    this.evaluationServer = evaluationServer;
    this.port = port;
    this.server = null;
    this.configDefaults = null;
    this.loadConfigDefaults();
  }

  /**
   * Load default model configuration from config.yaml
   */
  loadConfigDefaults() {
    try {
      const configPath = path.resolve('./evals/config.yaml');
      if (fs.existsSync(configPath)) {
        const configContent = fs.readFileSync(configPath, 'utf8');
        this.configDefaults = yaml.load(configContent);
        logger.info('Loaded config.yaml defaults:', this.configDefaults);
      } else {
        logger.warn('config.yaml not found, using hardcoded defaults');
        this.configDefaults = {
          model: {
            main_model: 'gpt-4.1',
            mini_model: 'gpt-4.1-mini',
            nano_model: 'gpt-4.1-nano',
            provider: 'openai'
          }
        };
      }
    } catch (error) {
      logger.error('Failed to load config.yaml:', error);
      this.configDefaults = {
        model: {
          main_model: 'gpt-4.1',
          mini_model: 'gpt-4.1-mini',
          nano_model: 'gpt-4.1-nano',
          provider: 'openai'
        }
      };
    }
  }

  start() {
    this.server = http.createServer((req, res) => {
      // Enable CORS
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

      if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
      }

      this.handleRequest(req, res);
    });

    this.server.listen(this.port, () => {
      logger.info(`API server started on http://localhost:${this.port}`);
    });
  }

  async handleRequest(req, res) {
    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;
    const method = req.method;

    try {
      // Get body for POST requests
      let body = '';
      if (method === 'POST') {
        for await (const chunk of req) {
          body += chunk;
        }
      }

      let result;

      // Handle dynamic client evaluations route
      if (pathname.startsWith('/clients/') && pathname.endsWith('/evaluations')) {
        const clientId = pathname.split('/')[2];
        result = this.getClientEvaluations(clientId);
      } else if (pathname.startsWith('/clients/') && pathname.endsWith('/tabs')) {
        // Handle dynamic client tabs route
        const clientId = pathname.split('/')[2];
        result = this.getClientTabsById(clientId);
      } else {
        switch (pathname) {
          case '/status':
            result = this.getStatus();
            break;

          case '/clients':
            result = this.getClients();
            break;

          case '/evaluate':
            if (method !== 'POST') {
              this.sendError(res, 405, 'Method not allowed');
              return;
            }
            result = await this.triggerEvaluation(JSON.parse(body));
            break;

          case '/tabs/open':
            if (method !== 'POST') {
              this.sendError(res, 405, 'Method not allowed');
              return;
            }
            result = await this.openTab(JSON.parse(body));
            break;

          case '/tabs/close':
            if (method !== 'POST') {
              this.sendError(res, 405, 'Method not allowed');
              return;
            }
            result = await this.closeTab(JSON.parse(body));
            break;

          case '/v1/responses':
            if (method !== 'POST') {
              this.sendError(res, 405, 'Method not allowed');
              return;
            }
            result = await this.handleResponsesRequest(JSON.parse(body));
            break;

          default:
            this.sendError(res, 404, 'Not found');
            return;
        }
      }

      this.sendResponse(res, 200, result);

    } catch (error) {
      logger.error('API error:', error);
      this.sendError(res, 500, error.message);
    }
  }

  getStatus() {
    const status = this.evaluationServer.getStatus();
    const clients = this.evaluationServer.getClientManager().getAllClients();

    return {
      server: status,
      clients: clients.map(client => ({
        id: client.id,
        name: client.name,
        connected: this.evaluationServer.connectedClients.has(client.id),
        ready: this.evaluationServer.connectedClients.get(client.id)?.ready || false
      }))
    };
  }

  getClients() {
    const clients = this.evaluationServer.getClientManager().getAllClients();
    const connectedClients = this.evaluationServer.connectedClients;

    return clients.map(client => {
      const tabs = this.evaluationServer.getClientManager().getClientTabs(client.id);

      return {
        id: client.id,
        name: client.name,
        description: client.description,
        tabCount: tabs.length,
        tabs: tabs.map(tab => ({
          tabId: tab.tabId,
          compositeClientId: tab.compositeClientId,
          connected: connectedClients.has(tab.compositeClientId),
          ready: connectedClients.get(tab.compositeClientId)?.ready || false,
          connectedAt: tab.connectedAt,
          remoteAddress: tab.connection?.remoteAddress || 'unknown'
        }))
      };
    });
  }

  getClientEvaluations(clientId) {
    if (!clientId) {
      throw new Error('Client ID is required');
    }

    const evaluations = this.evaluationServer.getClientManager().getClientEvaluations(clientId);
    return {
      clientId,
      evaluations: evaluations.map(evaluation => ({
        id: evaluation.id,
        name: evaluation.name,
        description: evaluation.description,
        tool: evaluation.tool,
        status: evaluation.status || 'pending',
        enabled: evaluation.enabled !== false,
        lastRun: evaluation.lastRun,
        lastResult: evaluation.lastResult
      }))
    };
  }

  getClientTabsById(clientId) {
    if (!clientId) {
      throw new Error('Client ID is required');
    }

    const tabs = this.evaluationServer.getClientManager().getClientTabs(clientId);
    const connectedClients = this.evaluationServer.connectedClients;
    const client = this.evaluationServer.getClientManager().getClient(clientId);

    if (!client) {
      throw new Error(`Client '${clientId}' not found`);
    }

    return {
      baseClientId: clientId,
      clientName: client.name,
      tabCount: tabs.length,
      tabs: tabs.map(tab => ({
        tabId: tab.tabId,
        compositeClientId: tab.compositeClientId,
        connected: connectedClients.has(tab.compositeClientId),
        ready: connectedClients.get(tab.compositeClientId)?.ready || false,
        connectedAt: tab.connectedAt,
        remoteAddress: tab.connection?.remoteAddress || 'unknown'
      }))
    };
  }

  async triggerEvaluation(payload) {
    const { clientId, evaluationId, runAll = false } = payload;

    if (!clientId) {
      throw new Error('Client ID is required');
    }

    // Check if client is connected
    const connection = this.evaluationServer.connectedClients.get(clientId);
    if (!connection || !connection.ready) {
      throw new Error(`Client '${clientId}' is not connected or not ready`);
    }

    if (runAll) {
      // Run all evaluations for the client
      const evaluations = this.evaluationServer.getClientManager().getClientEvaluations(clientId);
      const results = [];

      for (const evaluation of evaluations) {
        try {
          this.evaluationServer.getClientManager().updateEvaluationStatus(clientId, evaluation.id, 'pending');
          await this.evaluationServer.executeEvaluation(connection, evaluation);
          results.push({ id: evaluation.id, status: 'completed' });
        } catch (error) {
          results.push({ id: evaluation.id, status: 'failed', error: error.message });
        }
      }

      return {
        clientId,
        type: 'batch',
        results
      };
    }
      // Run specific evaluation
      if (!evaluationId) {
        throw new Error('Evaluation ID is required when runAll is false');
      }

      const evaluation = this.evaluationServer.getClientManager().getClientEvaluations(clientId)
        .find(e => e.id === evaluationId);

      if (!evaluation) {
        throw new Error(`Evaluation '${evaluationId}' not found for client '${clientId}'`);
      }

      this.evaluationServer.getClientManager().updateEvaluationStatus(clientId, evaluationId, 'pending');
      await this.evaluationServer.executeEvaluation(connection, evaluation);

      return {
        clientId,
        evaluationId,
        type: 'single',
        status: 'completed'
      };

  }

  async openTab(payload) {
    const { clientId, url = 'about:blank', background = false } = payload;

    if (!clientId) {
      throw new Error('Client ID is required');
    }

    // Since we use direct CDP, we don't need the client to be connected
    // Just extract the baseClientId (first part before colon if composite, or the whole ID)
    const baseClientId = clientId.split(':')[0];

    const result = await this.evaluationServer.openTab(baseClientId, { url, background });

    return {
      clientId: baseClientId,
      tabId: result.tabId,
      compositeClientId: result.compositeClientId,
      url: result.url || url,
      status: 'opened'
    };
  }

  async closeTab(payload) {
    const { clientId, tabId } = payload;

    if (!clientId) {
      throw new Error('Client ID is required');
    }

    if (!tabId) {
      throw new Error('Tab ID is required');
    }

    // Since we use direct CDP, we don't need the client to be connected
    // Just extract the baseClientId
    const baseClientId = clientId.split(':')[0];

    const result = await this.evaluationServer.closeTab(baseClientId, { tabId });

    return {
      clientId: baseClientId,
      tabId,
      status: 'closed',
      success: result.success !== false
    };
  }

  /**
   * Handle OpenAI Responses API compatible requests with nested model format
   */
  async handleResponsesRequest(requestBody) {
    try {
      // Validate required input field
      if (!requestBody.input || typeof requestBody.input !== 'string') {
        throw new Error('Missing or invalid "input" field. Expected a string.');
      }

      // Handle nested model configuration directly
      const nestedModelConfig = this.processNestedModelConfig(requestBody);

      // Extract optional URL and wait timeout
      const targetUrl = requestBody.url || 'about:blank';
      const waitTimeout = requestBody.wait_timeout || 5000;

      const redact = (mk) => ({
        ...mk,
        api_key: mk?.api_key ? `${String(mk.api_key).slice(0, 4)}...` : undefined
      });
      logger.info('Processing responses request:', {
        input: requestBody.input,
        url: targetUrl,
        wait_timeout: targetUrl !== 'about:blank' ? waitTimeout : 0,
        modelConfig: {
          main_model: redact(nestedModelConfig.main_model),
          mini_model: redact(nestedModelConfig.mini_model),
          nano_model: redact(nestedModelConfig.nano_model),
        }
      });

      // Find a client with existing tabs (not the dummy client)
      const baseClientId = this.findClientWithTabs();

      // Open a new tab for this request at the specified URL
      logger.info('Opening new tab for responses request', { baseClientId, url: targetUrl });
      const tabResult = await this.evaluationServer.openTab(baseClientId, {
        url: targetUrl,
        background: false
      });

      logger.info('Tab opened successfully', {
        tabId: tabResult.tabId,
        compositeClientId: tabResult.compositeClientId
      });

      // Wait for the new tab's DevTools to connect
      const tabClient = await this.waitForClientConnection(tabResult.compositeClientId);

      // Wait for page to load if a custom URL was provided
      if (targetUrl !== 'about:blank') {
        logger.info('Waiting for page to load', { waitTimeout });
        await new Promise(resolve => setTimeout(resolve, waitTimeout));
      }

      // Create a dynamic evaluation for this request
      const evaluation = this.createDynamicEvaluationNested(requestBody.input, nestedModelConfig);

      // Execute the evaluation on the new tab's DevTools client
      logger.info('Executing evaluation on new tab', {
        compositeClientId: tabResult.compositeClientId,
        evaluationId: evaluation.id
      });

      const result = await this.evaluationServer.executeEvaluation(tabClient, evaluation);

      // Debug: log the result structure
      logger.debug('executeEvaluation result:', result);

      // Extract the response text from the result
      const responseText = this.extractResponseText(result);

      // Format in OpenAI-compatible Responses API format with tab metadata
      return this.formatResponse(responseText, tabResult.compositeClientId.split(':')[0], tabResult.tabId);

    } catch (error) {
      logger.error('Error handling responses request:', error);
      throw error;
    }
  }

  /**
   * Process nested model configuration from request body
   * @param {Object} requestBody - Request body containing optional model configuration
   * @returns {import('./types/model-config').ModelConfig} Nested model configuration
   */
  processNestedModelConfig(requestBody) {
    const defaults = this.configDefaults?.model || {};

    // If nested format is provided, use it directly with fallbacks
    if (requestBody.model) {
      return {
        main_model: requestBody.model.main_model || this.createDefaultModelConfig('main', defaults),
        mini_model: requestBody.model.mini_model || this.createDefaultModelConfig('mini', defaults),
        nano_model: requestBody.model.nano_model || this.createDefaultModelConfig('nano', defaults)
      };
    }

    // No model config provided, use defaults
    return {
      main_model: this.createDefaultModelConfig('main', defaults),
      mini_model: this.createDefaultModelConfig('mini', defaults),
      nano_model: this.createDefaultModelConfig('nano', defaults)
    };
  }

  /**
   * Create default model configuration for a tier
   * @param {'main' | 'mini' | 'nano'} tier - Model tier
   * @param {Object} defaults - Default configuration from config.yaml
   * @returns {import('./types/model-config').ModelTierConfig} Model tier configuration
   */
  createDefaultModelConfig(tier, defaults) {
    const defaultModels = {
      main: defaults.main_model || 'gpt-4',
      mini: defaults.mini_model || 'gpt-4-mini',
      nano: defaults.nano_model || 'gpt-3.5-turbo'
    };

    return {
      provider: defaults.provider || 'openai',
      model: defaultModels[tier],
      api_key: process.env.OPENAI_API_KEY
    };
  }


  /**
   * Find a connected and ready client
   */
  findReadyClient() {
    for (const [clientId, connection] of this.evaluationServer.connectedClients) {
      if (connection.ready) {
        return connection;
      }
    }
    return null;
  }

  /**
   * Find a client that has existing tabs (not the dummy client)
   * @returns {string} Base client ID
   */
  findClientWithTabs() {
    const clients = this.evaluationServer.getClientManager().getAllClients();

    // First, try to find a client with existing tabs
    for (const client of clients) {
      const tabs = this.evaluationServer.getClientManager().getClientTabs(client.id);
      if (tabs.length > 0) {
        logger.info('Found client with tabs', { clientId: client.id, tabCount: tabs.length });
        return client.id;
      }
    }

    // If no client with tabs, use the first available client (even with 0 tabs)
    if (clients.length > 0) {
      logger.info('No clients with tabs found, using first available client', { clientId: clients[0].id });
      return clients[0].id;
    }

    throw new Error('No clients found. Please ensure at least one DevTools client is registered.');
  }

  /**
   * Wait for a client connection to be established and ready
   * @param {string} compositeClientId - Composite client ID (baseClientId:tabId)
   * @param {number} maxWaitMs - Maximum time to wait in milliseconds
   * @returns {Promise<Object>} Connection object
   */
  async waitForClientConnection(compositeClientId, maxWaitMs = 10000) {
    const startTime = Date.now();
    const pollInterval = 500; // Check every 500ms

    logger.info('Waiting for client connection', { compositeClientId, maxWaitMs });

    while (Date.now() - startTime < maxWaitMs) {
      const connection = this.evaluationServer.connectedClients.get(compositeClientId);

      if (connection && connection.ready) {
        logger.info('Client connection established and ready', {
          compositeClientId,
          waitedMs: Date.now() - startTime
        });
        return connection;
      }

      // Wait before next check
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error(`Timeout waiting for client connection: ${compositeClientId}. Tab may not have connected to eval-server.`);
  }

  /**
   * Create a dynamic evaluation object with nested model configuration
   * @param {string} input - Input message for the evaluation
   * @param {import('./types/model-config').ModelConfig} nestedModelConfig - Model configuration
   * @returns {import('./types/model-config').EvaluationRequest} Evaluation request object
   */
  createDynamicEvaluationNested(input, nestedModelConfig) {
    const evaluationId = `api-eval-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    return {
      id: evaluationId,
      name: 'API Request',
      description: 'Dynamic evaluation created from API request',
      enabled: true,
      tool: 'chat',
      timeout: 7200000, // 2 hours (increased for slow custom API)
      input: {
        message: input
      },
      model: nestedModelConfig,
      validation: {
        type: 'none' // No validation needed for API responses
      },
      metadata: {
        tags: ['api', 'dynamic'],
        priority: 'high',
        source: 'api'
      }
    };
  }


  /**
   * Extract response text from evaluation result
   */
  extractResponseText(result) {
    if (!result) {
      return 'No response received from evaluation';
    }

    // Handle different result formats
    if (typeof result === 'string') {
      return result;
    }

    // Check for nested evaluation result structure
    if (result.output && result.output.response) {
      return result.output.response;
    }

    if (result.output && result.output.text) {
      return result.output.text;
    }

    if (result.output && result.output.answer) {
      return result.output.answer;
    }

    // Check top-level properties
    if (result.response) {
      return result.response;
    }

    if (result.text) {
      return result.text;
    }

    if (result.answer) {
      return result.answer;
    }

    // If result is an object, try to extract meaningful content
    if (typeof result === 'object') {
      return JSON.stringify(result, null, 2);
    }

    return 'Unable to extract response text from evaluation result';
  }

  /**
   * Format response in OpenAI-compatible Responses API format
   */
  formatResponse(responseText, clientId = null, tabId = null) {
    const messageId = `msg_${uuidv4().replace(/-/g, '')}`;

    // Debug: log the parameters
    logger.debug('formatResponse called with:', { clientId, tabId, hasClientId: !!clientId, hasTabId: !!tabId });

    const response = [
      {
        id: messageId,
        type: 'message',
        role: 'assistant',
        content: [
          {
            type: 'output_text',
            text: responseText,
            annotations: []
          }
        ]
      }
    ];

    // Add metadata if clientId and tabId are provided
    if (clientId && tabId) {
      response[0].metadata = {
        clientId,
        tabId
      };
      logger.debug('Metadata added to response:', response[0].metadata);
    } else {
      logger.debug('Metadata NOT added - clientId or tabId missing');
    }

    return response;
  }

  sendResponse(res, statusCode, data) {
    res.writeHead(statusCode, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data, null, 2));
  }

  sendError(res, statusCode, message) {
    res.writeHead(statusCode, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: message }));
  }

  stop() {
    if (this.server) {
      this.server.close();
      logger.info('API server stopped');
    }
  }
}

export { APIServer };
