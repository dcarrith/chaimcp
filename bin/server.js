#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// Resolve the src directory relative to this script
const srcDir = path.resolve(__dirname, '../src');

console.error('Starting ChaiMCP server via npx...');
console.error(`Using PYTHONPATH: ${srcDir}`);

// Set PYTHONPATH to include the src directory
const env = {
    ...process.env,
    PYTHONPATH: srcDir + (path.delimiter + (process.env.PYTHONPATH || ''))
};

// Spawn the python3 process
// We use -m chaimcp.main to run the module
const child = spawn('python3', ['-m', 'chaimcp.main', ...process.argv.slice(2)], {
    env,
    stdio: 'inherit' // Forward stdin/stdout/stderr
});

child.on('error', (err) => {
    if (err.code === 'ENOENT') {
        console.error('Error: python3 not found. Please ensure python3 is installed and in your PATH.');
    } else {
        console.error('Failed to start python process:', err);
    }
    process.exit(1);
});

child.on('close', (code) => {
    process.exit(code);
});
