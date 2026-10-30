// Test-only CDP transport using Node's installed native WebSocket (no npm install).
'use strict';
const readline = require('node:readline');
if (typeof WebSocket !== 'function') throw new Error('Node 22+ native WebSocket is required');
const socket = new WebSocket(process.argv[2]);
const output = value => process.stdout.write(JSON.stringify(value) + '\n');
socket.addEventListener('open', () => {
  output({ready: true});
  readline.createInterface({input: process.stdin}).on('line', line => {
    try { socket.send(line); } catch (error) { output({transportError: String(error)}); }
  });
});
socket.addEventListener('message', event => output(JSON.parse(event.data)));
socket.addEventListener('error', event => { output({transportError: String(event.message || event)}); process.exitCode = 1; });
socket.addEventListener('close', () => process.exit());
