// Runs the real front-end code against the real server (no browser): auth gate, avatar, account page, escaping, persistence.
import { makeEnv, scriptsOf } from './fe_env.mjs';

const base = process.argv[2];
const results = [];
const check = (name, ok, detail = '') => results.push({ name, ok: !!ok, detail: ok ? '' : String(detail).slice(0, 300) });
const H = { 'X-Requested-With': 'grit', 'Content-Type': 'application/json' };
const scripts = scriptsOf('app.html');

async function signUp(email, extra = {}) {
  const r = await fetch(`${base}/api/auth/register`, { method: 'POST', headers: H, body: JSON.stringify({ email, password: 'correct horse battery', ...extra }) });
  return r.headers.getSetCookie()[0].split(';')[0];
}
async function boot(cookie) {
  const env = makeEnv({ base, cookie });
  env.load(scripts);
  await env.until(() => env.ctx.state.ready || env.location.replaced.length);
  return env;
}
function png() {
  // 80x60 red PNG
  return Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAFAAAAA8CAIAAAB+RarbAAAAYUlEQVR4nO3PAQ3AIADAMEAN/oNAXJxkbxVs8+w9/mS9Dvia4TrDdYbrDNcZrjNcZ7jOcJ3hOsN1husM1xmuM1xnuM5wneE6w3WG6wzXGa4zXGe4znCd4TrDdYbrDNcZrrvWGgF8DS9mrAAAAABJRU5ErkJggg==', 'base64');
}

// 1. Not signed in: the app sends you to the sign-in page and shows no data.
{
  const env = await boot('');
  check('signed-out visitor is redirected to sign in', env.location.replaced.includes('auth.html#login'), env.location.replaced);
  check('signed-out visitor sees no private data', !env.ctx.state.ready && !/challenge/i.test(env.els.app.innerHTML), env.els.app.innerHTML);
}

// 2. Signed in: dashboard loads, header shows an initial, then a real uploaded avatar.
{
  const cookie = await signUp('ada@example.com', { name: 'Ada' });
  const env = await boot(cookie);
  check('signed-in user reaches the dashboard', env.ctx.state.ready === true);
  check('home greets the user by name', /Ada/.test(env.els.app.innerHTML), env.els.app.innerHTML.slice(0, 300));
  check('header chip shows an initial before a photo exists', /class="av ini chip"[^>]*>A</.test(env.els.mechip.innerHTML), env.els.mechip.innerHTML);
  check('home has the avatar block linking to Account', /class="av-hero" href="#account"/.test(env.els.app.innerHTML));

  env.location.hash = 'account'; env.run('route()');
  const acct = env.els.app.innerHTML;
  check('account page has profile, security, backup and delete sections', ['Photo and name', 'Password and sessions', 'Backup', 'Delete account'].every(t => acct.includes(t)), acct.length);
  check('account page shows the sign-in email', acct.includes('ada@example.com'));
  check('account page has the password and delete controls', acct.includes('Change password') && acct.includes('Delete my account'));

  // upload a photo through the real module handler
  const file = new Blob([png()], { type: 'image/png' });
  env.ctx.MODULES.accountProfile.on.change({ target: { id: 'avatarfile', files: [file], value: 'x' } });
  const ok = await env.until(() => env.ctx.state.profile.avatar.has);
  check('uploading a photo updates the app state', ok);
  check('header chip now shows the uploaded photo', /<img class="av chip"[^>]+src="\/api\/me\/avatar\?v=\d+"/.test(env.els.mechip.innerHTML), env.els.mechip.innerHTML);
  const img = await fetch(`${base}/api/me/avatar`, { headers: { Cookie: cookie } });
  check('server serves the processed avatar as webp', img.status === 200 && img.headers.get('content-type') === 'image/webp', img.status);

  // saving a name persists on the server
  env.ctx.saveProfile({ name: 'Ada L' });
  await new Promise(r => setTimeout(r, 300));
  const st = await (await fetch(`${base}/api/state`, { headers: { Cookie: cookie } })).json();
  check('profile name persists to the server', st.profile.name === 'Ada L', JSON.stringify(st.profile));

  // saving a challenge persists; the server rejects invalid data and the app says so
  const good = { id: 'c1', name: 'Walk', days: 21, start: '2026-11-01', created: 1, ticks: { 0: true }, notes: {} };
  check('a valid challenge saves', (await env.ctx.persist(good)) === true);
  const bad = { id: 'c2', name: 'Bad', days: 21, start: '2026-11-01', created: 2, ticks: { 99: true }, notes: {} };
  check('an invalid challenge is refused and the user is told', (await env.ctx.persist(bad)) === false && /inside the challenge/.test(env.els.toast.textContent), env.els.toast.textContent);

  // change password through the real handler
  const $el = id => env.ctx.document.getElementById(id);
  $el('pw-cur').value = 'correct horse battery'; $el('pw-new').value = 'an even longer phrase';
  env.ctx.MODULES.accountSecurity.on.submit({ target: { id: 'pwForm' }, preventDefault() {} });
  await new Promise(r => setTimeout(r, 400));
  const relog = await fetch(`${base}/api/auth/login`, { method: 'POST', headers: H, body: JSON.stringify({ email: 'ada@example.com', password: 'an even longer phrase' }) });
  check('changing the password in the UI really changes it', relog.status === 200, relog.status);

  // delete account through the real handler
  env.ctx.MODULES.accountDanger.actions.open();
  $el('del-pw').value = 'an even longer phrase'; $el('del-ok').value = 'DELETE';
  env.ctx.MODULES.accountDanger.on.submit({ target: { id: 'delForm' }, preventDefault() {} });
  await env.until(() => env.location.replaced.some(u => u.includes('deleted=1')));
  check('delete flow sends the person to the landing page', env.location.replaced.some(u => u.includes('deleted=1')), env.location.replaced);
  const gone = await fetch(`${base}/api/auth/login`, { method: 'POST', headers: H, body: JSON.stringify({ email: 'ada@example.com', password: 'an even longer phrase' }) });
  check('after deleting, the account can no longer sign in', gone.status === 401, gone.status);
}

// 3. Hostile profile text is escaped, never rendered as markup.
{
  const evil = '<img src=x onerror=alert(1)>';
  const cookie = await signUp('eve@example.com');
  await fetch(`${base}/api/profile`, { method: 'PUT', headers: { ...H, Cookie: cookie }, body: JSON.stringify({ name: evil, intent: { habit: '<script>alert(2)</script>' } }) });
  await fetch(`${base}/api/challenges/x`, { method: 'PUT', headers: { ...H, Cookie: cookie }, body: JSON.stringify({ name: '<b onmouseover=alert(3)>hi</b>', days: 21, start: '2026-11-01', created: 1, ticks: {}, notes: { 0: '<svg onload=alert(4)>' } }) });
  const env = await boot(cookie);
  const pages = ['home', 'challenges', 'habit', 'insights', 'me', 'account'];
  let all = '';
  for (const p of pages) { env.location.hash = p; env.run('route()'); all += env.els.app.innerHTML; }
  env.location.hash = 'c-x'; env.run('route()'); all += env.els.app.innerHTML + env.els.mechip.innerHTML;
  check('hostile text appears escaped on every page', all.includes('&lt;img') && all.includes('&lt;b onmouseover') );
  check('no raw hostile markup reaches the page', !/<img src=x|<script>alert|<b onmouseover|<svg onload/.test(all), all.match(/<img src=x|<script>alert|<b onmouseover|<svg onload/));
}

const failed = results.filter(r => !r.ok);
console.log(JSON.stringify(results));
process.exit(failed.length ? 1 : 0);
