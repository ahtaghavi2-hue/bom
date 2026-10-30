// Temporary verification; no browser storage or network access.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const fields = {};
const writes = [];
let timer;
const widget = selector => ({
    val(value) { if (arguments.length) { fields[selector] = value; return this; } return fields[selector] ?? ''; },
    ready() { return this; }, on() { return this; }, stop() { return this; }, text() { return this; },
    fadeIn() { return this; }, delay() { return this; }, fadeOut() { return this; }
});
const context = vm.createContext({
    console, document: {}, window: {}, localStorage: { getItem() { return null; } },
    $: widget, setTimeout(fn) { timer = fn; return 1; }, clearTimeout() {},
    fetch: async (url, options) => { writes.push({url, payload: JSON.parse(options.body)}); return {ok: true, json: async () => ({success: true})}; }
});
vm.runInContext(fs.readFileSync('F:/bom-system/static/script.js', 'utf8'), context);
vm.runInContext(`
    refreshDemandViews = function() {};
    loadData = async function() {};
    loadNotifications = function() {};
    currentData = {nodes: {a1: {id:'a1', type:'assembly'}, a2:{id:'a2',type:'assembly'}},root_ids:[]};
    currentNodeId = 'a1';
`, context);
fields['#field-name'] = 'Assembly A edit';
fields['#field-required_quantity'] = '3';
fields['#field-quantity'] = '4';
vm.runInContext('autoSaveNode()', context);
vm.runInContext("currentNodeId = 'a2'", context);
fields['#field-name'] = 'Assembly B edit';
fields['#field-required_quantity'] = '2';
fields['#field-quantity'] = '5';
vm.runInContext('autoSaveNode()', context);
timer();
(async () => {
    await vm.runInContext('saveQueue', context);
    assert.deepStrictEqual(writes.map(w => [w.url, w.payload.name, w.payload.quantity]), [
        ['/api/node/a1', 'Assembly A edit', 4], ['/api/node/a2', 'Assembly B edit', 5]
    ]);
    console.log('PASS: debounce selection switch preserves both node-specific snapshots and serialized writes');
    fields['#field-required_quantity'] = '0';
    const result = vm.runInContext('captureNodeSave().payload.required_quantity', context);
    assert.strictEqual(result, 0);
    console.log('PASS: autosave preserves zero per-parent coefficient');
})().catch(error => { console.error(error); process.exitCode = 1; });
