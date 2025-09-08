#!/usr/bin/env node

const crypto = require('crypto');

// Twilio API credentials
const API_KEY_SID = 'SK5346918f48275d6571be927e84cfd6f8';
const API_KEY_SECRET = process.env.TWILIO_API_KEY_SECRET || 'YOUR_API_KEY_SECRET_HERE';

// Time to live (in seconds) - 24 hours
const ttl = 86400;

// Calculate expiration timestamp
const unixTimestamp = Math.floor(Date.now() / 1000) + ttl;

// Create username (timestamp:apiKeySid)
const username = `${unixTimestamp}:${API_KEY_SID}`;

// Generate password using HMAC-SHA1
const password = crypto
    .createHmac('sha1', API_KEY_SECRET)
    .update(username)
    .digest('base64');

console.log('Twilio TURN Credential Generator');
console.log('=' .repeat(60));
console.log('\nConfiguration:');
console.log(`API Key SID: ${API_KEY_SID}`);
console.log(`API Key Secret: ${API_KEY_SECRET === 'YOUR_API_KEY_SECRET_HERE' ? '[NOT SET - Please provide]' : '[HIDDEN]'}`);
console.log(`TTL: ${ttl} seconds (${ttl/3600} hours)`);
console.log('\nGenerated Credentials:');
console.log(`Username: ${username}`);
console.log(`Password: ${password}`);
console.log(`\nExpires at: ${new Date(unixTimestamp * 1000).toISOString()}`);

console.log('\nFor service.yaml, use:');
console.log(`- name: NEKO_ICESERVERS`);
console.log(`  value: '[{"urls": ["turn:global.turn.twilio.com:3478?transport=tcp", "turns:global.turn.twilio.com:5349?transport=tcp"], "username": "${username}", "credential": "${password}"}]'`);

if (API_KEY_SECRET === 'YOUR_API_KEY_SECRET_HERE') {
    console.log('\n⚠️  WARNING: You need to set the actual API Key Secret!');
    console.log('Run with: TWILIO_API_KEY_SECRET=your_actual_secret node generate-twilio-credential.js');
}