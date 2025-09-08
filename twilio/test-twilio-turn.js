#!/usr/bin/env node

// Test Twilio TURN server credentials
const crypto = require('crypto');

// Parse the credentials from service.yaml
const username = "1757273052:SK5346918f48275d6571be927e84cfd6f8";
const credential = "12HiXDndTPnUQZorm6TDDHd9Co8=";

console.log("Testing Twilio TURN credentials:");
console.log("Username:", username);
console.log("Credential:", credential);

// Extract timestamp from username
const parts = username.split(':');
const timestamp = parseInt(parts[0]);
const apiKeySid = parts[1];

console.log("\nParsed values:");
console.log("Timestamp:", timestamp);
console.log("API Key SID:", apiKeySid);

// Check if timestamp is valid (not expired)
const now = Math.floor(Date.now() / 1000);
const expiresIn = timestamp - now;

console.log("\nTimestamp validation:");
console.log("Current time (Unix):", now);
console.log("Credential timestamp:", timestamp);
console.log("Expires in:", expiresIn, "seconds");

if (expiresIn < 0) {
    console.log("❌ Credentials have EXPIRED!");
} else {
    console.log("✅ Credentials are still valid for", Math.floor(expiresIn / 3600), "hours");
}

// To verify the credential, we would need the API Key Secret
// The credential should be: base64(hmac-sha1(username, apiKeySecret))
console.log("\nNote: To fully verify the credential, we would need the API Key Secret.");
console.log("The credential should be computed as: base64(hmac-sha1(username, apiKeySecret))");

// Test with curl (requires actual network test)
console.log("\nTo test the TURN server directly, you can use a tool like 'turnutils_uclient':");
console.log(`turnutils_uclient -T -p 3478 -u "${username}" -w "${credential}" turn:global.turn.twilio.com`);