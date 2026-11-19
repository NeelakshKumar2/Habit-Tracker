// Loads the real front-end scripts (in the order app.html lists them) into a Node vm with a tiny DOM stub.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';

const WEB = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', 'web');

export function scriptsOf(htmlFile) {
  const html = fs.readFileSync(path.join(WEB, htmlFile), 'utf8');
  return [...html.matchAll(/<script src="([^"]+)"/g)].map(m => m[1]);
}

function el(id) {
  return {
    id, innerHTML: '', textContent: '', value: '', disabled: false, attrs: {}, children: [],
    style: { setProperty() {} }, classList: { add() {}, remove() {} },
    setAttribute(k, v) { this.attrs[k] = v; }, removeAttribute(k) { delete this.attrs[k]; },
    addEventListener() {}, contains() { return false; }, closest() { return null; }, focus() {},
    appendChild() {}, remove() {}, click() {},
  };
}

export function makeEnv({ base = 'http://localhost', cookie = '' } = {}) {
  const els = {};
  const jar = { cookie };
  const location = { hash: '', search: '', protocol: 'http:', replaced: [], replace(u) { this.replaced.push(u); } };
  const store = {};
  const sandbox = {
    console, setTimeout, clearTimeout, URL, Blob, FormData, Headers, Promise, JSON, Date, Math,
    location,
    localStorage: { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: k => { delete store[k]; } },
    document: {
      activeElement: null,
      getElementById: id => (els[id] ||= el(id)),
      querySelector: sel => (sel.startsWith('#') ? (els[sel.slice(1)] ||= el(sel.slice(1))) : null),
      createElement: () => el('tmp'),
      body: el('body'),
    },
    addEventListener() {}, scrollTo() {},
    fetch: async (url, init = {}) => {
      const headers = new Headers(init.headers || {});
      if (jar.cookie) headers.set('Cookie', jar.cookie);
      const r = await fetch(new URL(url, base), { ...init, headers });
      for (const sc of r.headers.getSetCookie?.() || []) {
        const pair = sc.split(';')[0];
        jar.cookie = /=;?$/.test(pair) || /Expires=Thu, 01 Jan 1970/i.test(sc) ? '' : pair;
      }
      return r;
    },
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  return {
    ctx: sandbox, els, jar, location,
    load(files) {
      for (const f of files) vm.runInContext(fs.readFileSync(path.join(WEB, f), 'utf8'), sandbox, { filename: f });
    },
    async until(fn, ms = 4000) {
      const t = Date.now();
      while (Date.now() - t < ms) { if (fn()) return true; await new Promise(r => setTimeout(r, 20)); }
      return false;
    },
    run(code) { return vm.runInContext(code, sandbox); },
  };
}
