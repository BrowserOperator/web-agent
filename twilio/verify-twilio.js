#!/usr/bin/env node

const crypto = require('crypto');

// Your Twilio API credentials
const API_KEY_SID = 'SK5346918f48275d6571be927e84cfd6f8';
const API_KEY_SECRET = 'OWJDRGxZZnxUlwOVXbupRs9yhQaylXzo';

// Generate credentials
const ttl = 86400; // 24 hours
const unixTimestamp = Math.floor(Date.now() / 1000) + ttl;
const username = `${unixTimestamp}:${API_KEY_SID}`;
const password = crypto
    .createHmac('sha1', API_KEY_SECRET)
    .update(username)
    .digest('base64');

console.log('Testing Twilio TURN credentials locally');
console.log('=' .repeat(60));
console.log('Username:', username);
console.log('Password:', password);
console.log('=' .repeat(60));

// Test with curl commands
console.log('\nTest commands to verify TURN server access:\n');

// Test STUN binding
console.log('1. Test STUN binding (should work without auth):');
console.log(`curl -X POST "https://global.turn.twilio.com:5349" --http1.1 -k`);

// Test with turnutils if available
console.log('\n2. Test with turnutils_uclient (if installed):');
console.log(`turnutils_uclient -T -p 3478 -u "${username}" -w "${password}" turn:global.turn.twilio.com`);

// Test with Node.js TURN client
console.log('\n3. Testing connection with Node.js...\n');

const net = require('net');
const tls = require('tls');

function testTurnServer(host, port, useTLS = false) {
    return new Promise((resolve, reject) => {
        console.log(`Testing ${useTLS ? 'TLS' : 'TCP'} connection to ${host}:${port}...`);
        
        const options = {
            host: host,
            port: port,
            rejectUnauthorized: false
        };
        
        const socket = useTLS ? 
            tls.connect(options, () => {
                console.log(`✅ TLS connection established to ${host}:${port}`);
                socket.end();
                resolve(true);
            }) :
            net.connect(options, () => {
                console.log(`✅ TCP connection established to ${host}:${port}`);
                socket.end();
                resolve(true);
            });
        
        socket.on('error', (err) => {
            console.log(`❌ Failed to connect: ${err.message}`);
            resolve(false);
        });
        
        socket.setTimeout(5000, () => {
            console.log(`❌ Connection timeout`);
            socket.destroy();
            resolve(false);
        });
    });
}

// Run tests
(async () => {
    await testTurnServer('global.turn.twilio.com', 3478, false);
    await testTurnServer('global.turn.twilio.com', 5349, true);
    
    console.log('\n' + '=' .repeat(60));
    console.log('If connections succeed, credentials should work in service.yaml');
    console.log('=' .repeat(60));
})();