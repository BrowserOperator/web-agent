#!/usr/bin/env node

const https = require('https');

const ACCOUNT_SID = 'SK5346918f48275d6571be927e84cfd6f8';
const AUTH_TOKEN = 'OWJDRGxZZnxUlwOVXbupRs9yhQaylXzo';

function getTwilioTurnCredentials() {
    return new Promise((resolve, reject) => {
        console.log('Fetching TURN credentials from Twilio...');
        
        const auth = Buffer.from(`${ACCOUNT_SID}:${AUTH_TOKEN}`).toString('base64');
        
        const options = {
            hostname: 'api.twilio.com',
            port: 443,
            path: `/2010-04-01/Accounts/${ACCOUNT_SID}/Tokens.json`,
            method: 'POST',
            headers: {
                'Authorization': `Basic ${auth}`,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': 0
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const response = JSON.parse(data);
                    if (res.statusCode === 201 || res.statusCode === 200) {
                        console.log('✅ Success!');
                        resolve(response.ice_servers || []);
                    } else {
                        reject(new Error(`API error: ${response.message}`));
                    }
                } catch (error) {
                    reject(error);
                }
            });
        });

        req.on('error', reject);
        req.end();
    });
}

getTwilioTurnCredentials()
    .then(servers => {
        const nekoServers = servers
            .filter(s => s.url && s.url.startsWith('turn'))
            .map(s => ({
                urls: [s.url],
                username: s.username,
                credential: s.credential
            }));
        
        console.log('\nFormatted for NEKO_ICESERVERS:');
        console.log(JSON.stringify(nekoServers));
    })
    .catch(console.error);