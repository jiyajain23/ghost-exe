const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const Module = require('node:module');
const test = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const filename = resolve(__dirname, '../src/components/EndingScreen.tsx');
const compiled = ts.transpileModule(readFileSync(filename, 'utf8'), {
  compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS }
}).outputText;
const mod = new Module(filename, module);
mod.filename = filename;
mod.paths = module.paths;
mod._compile(compiled, filename);
const { EndingScreen } = mod.exports;
const snapshot = { status: 'completed', ending: 'DO_NOT_FORGET', ending_presentation: {
  title: 'DO NOT FORGET', final_line: 'If you close the archive, who will remember she was here?',
  narrative: 'RELAY STATUS: ISOLATED\nOUTCOME: UNKNOWN'
}};
const render = value => renderToStaticMarkup(React.createElement(EndingScreen, { snapshot: value, onRestart() {} }));
test('completed ending renders title, canonical text and restart outside a document window', () => {
  const html = render(snapshot);
  for (const text of ['INVESTIGATION COMPLETE', 'DO NOT FORGET', snapshot.ending_presentation.final_line, 'OUTCOME: UNKNOWN', 'Restart Investigation']) assert.ok(html.includes(text));
  assert.ok(html.startsWith('<main'));
  assert.ok(html.includes('min-h-screen'));
});
test('restored JSON state renders the same ending', () => {
  assert.equal(render(JSON.parse(JSON.stringify(snapshot))), render(snapshot));
});
test('active run does not render ending', () => {
  assert.equal(render({status: 'active', ending_presentation: null}), '');
});
