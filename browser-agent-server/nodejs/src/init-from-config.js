/**
 * Config-based Client Initialization
 *
 * Auto-generates client YAML files from /config/browser-operator-config.yaml
 * This eliminates the need for manual client setup when using AUTOMATED_MODE.
 *
 * Behavior:
 * - Reads /config/browser-operator-config.yaml on server startup
 * - Extracts eval_server.client_id and eval_server.secret_key
 * - Auto-generates clients/{client_id}.yaml if it doesn't exist
 * - Logs info/errors but doesn't fail server startup if config is missing
 */

import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CONFIG_PATH = '/config/browser-operator-config.yaml';
const CLIENTS_DIR = path.join(__dirname, '../clients');

/**
 * Load and parse YAML config file
 */
function loadConfig() {
  try {
    if (!fs.existsSync(CONFIG_PATH)) {
      console.log(`Config file not found at ${CONFIG_PATH}, skipping auto-generation`);
      return null;
    }

    const yamlContent = fs.readFileSync(CONFIG_PATH, 'utf8');
    const config = yaml.load(yamlContent);

    if (!config || !config.eval_server) {
      console.log('Config file does not contain eval_server section');
      return null;
    }

    return config;
  } catch (error) {
    console.error('Failed to load config file:', error.message);
    return null;
  }
}

/**
 * Substitute environment variables in string values
 * Replaces ${VAR_NAME} with process.env.VAR_NAME
 */
function substituteEnvVars(value) {
  if (typeof value !== 'string') {
    return value;
  }

  return value.replace(/\$\{([^}]+)\}/g, (match, varName) => {
    const envValue = process.env[varName];
    if (envValue !== undefined) {
      console.log(`Substituted ${varName} with environment variable`);
      return envValue;
    }

    console.warn(`Environment variable ${varName} not found, keeping placeholder`);
    return match;
  });
}

/**
 * Auto-generate client YAML file from config
 */
function generateClientFile(config) {
  const evalServerConfig = config.eval_server;

  if (!evalServerConfig.client_id) {
    console.log('No client_id in config, skipping auto-generation');
    return;
  }

  const clientId = substituteEnvVars(evalServerConfig.client_id);
  const secretKey = substituteEnvVars(evalServerConfig.secret_key || 'default-secret-change-me');
  const clientName = substituteEnvVars(evalServerConfig.client_name || `Auto-generated ${clientId}`);
  const clientDescription = substituteEnvVars(evalServerConfig.client_description || 'Auto-configured from browser-operator-config.yaml');
  const maxConcurrentEvaluations = evalServerConfig.max_concurrent_evaluations || 3;
  const defaultTimeout = evalServerConfig.default_timeout || 45000;

  // Ensure clients directory exists
  if (!fs.existsSync(CLIENTS_DIR)) {
    fs.mkdirSync(CLIENTS_DIR, { recursive: true });
    console.log(`Created clients directory: ${CLIENTS_DIR}`);
  }

  const clientFilePath = path.join(CLIENTS_DIR, `${clientId}.yaml`);

  // Check if client file already exists
  if (fs.existsSync(clientFilePath)) {
    console.log(`Client file already exists: ${clientFilePath}`);
    return;
  }

  // Generate client YAML content
  const clientYAML = {
    client: {
      id: clientId,
      name: clientName,
      secret_key: secretKey,
      description: clientDescription
    },
    settings: {
      max_concurrent_evaluations: maxConcurrentEvaluations,
      default_timeout: defaultTimeout,
      retry_policy: {
        max_retries: 2,
        backoff_multiplier: 2,
        initial_delay: 1000
      }
    }
  };

  try {
    // Write YAML file
    const yamlString = yaml.dump(clientYAML, {
      indent: 2,
      lineWidth: 100,
      noRefs: true
    });

    fs.writeFileSync(clientFilePath, yamlString, 'utf8');
    console.log(`✓ Auto-generated client file: ${clientFilePath}`);
    console.log(`  Client ID: ${clientId}`);
    console.log(`  Client Name: ${clientName}`);
  } catch (error) {
    console.error(`Failed to write client file ${clientFilePath}:`, error.message);
  }
}

/**
 * Initialize clients from config file
 * Called on server startup before starting WebSocket server
 */
export async function initClientsFromConfig() {
  try {
    console.log('Initializing clients from config file...');

    const config = loadConfig();
    if (!config) {
      console.log('No config available, skipping client auto-generation');
      return;
    }

    generateClientFile(config);

    console.log('Client initialization from config complete');
  } catch (error) {
    console.error('Error during client initialization from config:', error);
    // Don't throw - we want server to start even if config init fails
  }
}
