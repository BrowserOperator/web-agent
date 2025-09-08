#!/usr/bin/env node

/**
 * Twilio Network Traversal Service Token Generator
 * Generates short-lived TURN credentials using Twilio's API
 */

const https = require('https');
const express = require('express');

// Twilio Account credentials (these are different from API Key)
const ACCOUNT_SID = process.env.TWILIO_ACCOUNT_SID || 'YOUR_ACCOUNT_SID';
const AUTH_TOKEN = process.env.TWILIO_AUTH_TOKEN || 'YOUR_AUTH_TOKEN';

// Optional: API Key credentials (if using API keys instead of master credentials)
const API_KEY_SID = process.env.TWILIO_API_KEY_SID || 'SK5346918f48275d6571be927e84cfd6f8';
const API_KEY_SECRET = process.env.TWILIO_API_KEY_SECRET || 'OWJDRGxZZnxUlwOVXbupRs9yhQaylXzo';

// Cache for tokens
let tokenCache = null;
let tokenExpiry = 0;

/**
 * Get TURN credentials from Twilio Network Traversal Service
 */
async function getTwilioTurnCredentials() {
    return new Promise((resolve, reject) => {
        // Check cache first
        if (tokenCache && Date.now() < tokenExpiry) {
            console.log('Returning cached TURN credentials');
            return resolve(tokenCache);
        }

        console.log('Fetching new TURN credentials from Twilio...');
        
        // Twilio API endpoint for Network Traversal Service
        const options = {
            hostname: 'api.twilio.com',
            port: 443,
            path: `/2010-04-01/Accounts/${ACCOUNT_SID}/Tokens.json`,
            method: 'POST',
            auth: `${ACCOUNT_SID}:${AUTH_TOKEN}`,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': 0
            }
        };

        const req = https.request(options, (res) => {
            let data = '';

            res.on('data', (chunk) => {
                data += chunk;
            });

            res.on('end', () => {
                try {
                    const response = JSON.parse(data);
                    
                    if (res.statusCode !== 201 && res.statusCode !== 200) {
                        console.error('Twilio API error:', response);
                        return reject(new Error(`Twilio API error: ${response.message || 'Unknown error'}`));
                    }

                    // Parse the ice_servers from response
                    const iceServers = response.ice_servers || [];
                    
                    // Cache for 1 hour (Twilio tokens are typically valid for 24 hours)
                    tokenCache = iceServers;
                    tokenExpiry = Date.now() + (60 * 60 * 1000); // 1 hour
                    
                    console.log(`Received ${iceServers.length} ICE servers from Twilio`);
                    resolve(iceServers);
                } catch (error) {
                    reject(new Error(`Failed to parse Twilio response: ${error.message}`));
                }
            });
        });

        req.on('error', (error) => {
            reject(new Error(`Twilio API request failed: ${error.message}`));
        });

        req.end();
    });
}

/**
 * Format ICE servers for neko
 */
function formatForNeko(twilioIceServers) {
    // Twilio returns format: {"url": "...", "username": "...", "credential": "..."}
    // Neko expects: {"urls": ["..."], "username": "...", "credential": "..."}
    return twilioIceServers.map(server => {
        if (server.url) {
            // Add TCP transport for TURN servers in Cloud Run
            let url = server.url;
            if (url.startsWith('turn:') && !url.includes('transport=')) {
                url += '?transport=tcp';
            }
            
            return {
                urls: [url],
                username: server.username,
                credential: server.credential
            };
        }
        return server;
    }).filter(server => {
        // Only keep TURN servers for Cloud Run (STUN won't work)
        return server.urls && server.urls[0] && server.urls[0].startsWith('turn');
    });
}

// Create Express server for health checks and credential endpoint
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.get('/turn-credentials', async (req, res) => {
    try {
        const twilioServers = await getTwilioTurnCredentials();
        const nekoServers = formatForNeko(twilioServers);
        
        res.json({
            iceServers: nekoServers,
            ttl: 3600, // 1 hour
            expires: new Date(tokenExpiry).toISOString()
        });
    } catch (error) {
        console.error('Error getting TURN credentials:', error);
        res.status(500).json({ error: error.message });
    }
});

// Standalone mode - get credentials and output for service.yaml
if (require.main === module) {
    if (process.argv.includes('--server')) {
        // Start HTTP server
        app.listen(PORT, () => {
            console.log(`Twilio token service listening on port ${PORT}`);
            console.log(`Health check: http://localhost:${PORT}/health`);
            console.log(`TURN credentials: http://localhost:${PORT}/turn-credentials`);
        });
    } else {
        // One-time credential generation
        getTwilioTurnCredentials()
            .then(twilioServers => {
                const nekoServers = formatForNeko(twilioServers);
                
                console.log('\n=== Twilio TURN Credentials ===');
                console.log('For service.yaml, use:');
                console.log('- name: NEKO_ICESERVERS');
                console.log(`  value: '${JSON.stringify(nekoServers)}'`);
                console.log('\nCredentials expire in ~24 hours');
                console.log('Raw response:', JSON.stringify(twilioServers, null, 2));
            })
            .catch(error => {
                console.error('Failed to get credentials:', error);
                process.exit(1);
            });
    }
}

module.exports = { getTwilioTurnCredentials, formatForNeko };