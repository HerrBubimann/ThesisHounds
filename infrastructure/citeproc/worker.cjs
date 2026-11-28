'use strict';

// Fixed worker: inputs arrive as JSON; all locales and items are supplied locally.
// Disable networking/process spawning before loading the pinned CSL dependency.
for (const name of ['net', 'http', 'https', 'http2', 'tls', 'dgram', 'dns', 'child_process']) {
  const module = require(name);
  for (const key of ['connect', 'createConnection', 'createServer', 'request', 'get',
    'createSocket', 'lookup', 'resolve', 'exec', 'execFile', 'spawn', 'fork',
    'execSync', 'execFileSync', 'spawnSync']) {
    if (typeof module[key] === 'function') {
      module[key] = () => { throw new Error('CITEPROC_NETWORK_OR_PROCESS_DENIED'); };
    }
  }
}
require('net').Socket.prototype.connect = () => { throw new Error('CITEPROC_NETWORK_DENIED'); };
global.fetch = () => { throw new Error('CITEPROC_NETWORK_DENIED'); };
const CSL = require('./node_modules/citeproc/citeproc_commonjs.js');
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  input += chunk;
  if (Buffer.byteLength(input, 'utf8') > 1000000) process.exit(2);
});
process.stdin.on('end', () => {
  try {
    const payload = JSON.parse(input);
    if (!Array.isArray(payload.items) || payload.items.length > 100) throw new Error('ITEM_LIMIT');
    const items = new Map(payload.items.map(item => [String(item.id), item]));
    if (items.size !== payload.items.length) throw new Error('DUPLICATE_ITEM');
    const processor = new CSL.Engine({
      retrieveLocale: tag => payload.locales[tag] || false,
      retrieveItem: id => items.get(String(id))
    }, payload.style, payload.language || 'de-DE');
    processor.setOutputFormat('text');
    processor.updateItems([...items.keys()]);
    const bibliography = processor.makeBibliography();
    if (!bibliography) throw new Error('NO_BIBLIOGRAPHY');
    const [metadata, rendered] = bibliography;
    const rows = rendered.map((text, i) => ({
      ids: metadata.entry_ids[i].map(String), text: text.trim()
    }));
    process.stdout.write(JSON.stringify({status: 'COMPLETED', entries: rows, processor: 'citeproc-js/2.4.63'}));
  } catch (_) {
    process.stdout.write(JSON.stringify({status: 'LOCAL_CITEPROC_REJECTED'}));
    process.exitCode = 1;
  }
});
