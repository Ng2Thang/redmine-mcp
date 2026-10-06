// Verify an authenticated attachment link with the installed Edge browser.
// Credentials are read privately from an ignored file, never command arguments or output.
import {readFile, mkdir} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
import {resolve} from 'node:path';

const input = JSON.parse(await readFile(process.argv[2], 'utf8'));
const url = new URL(input.url);
if (url.origin !== 'http://127.0.0.1:3001' || !url.pathname.startsWith('/attachments/download/')) {
  throw new Error('Refusing an unowned attachment URL');
}
const probe = createServer();
await new Promise(resolve => probe.listen(0, '127.0.0.1', resolve));
const port = probe.address().port;
await new Promise(resolve => probe.close(resolve));
const directory = resolve('.local/testing-e2e/browser-downloads');
await mkdir(directory, {recursive: true});
const browser = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', [
  '--headless=new', '--no-first-run', '--disable-background-networking',
  `--user-data-dir=${resolve('.local/testing-e2e/browser-profile')}`,
  `--remote-debugging-port=${port}`, '--remote-debugging-address=127.0.0.1', 'about:blank',
], {windowsHide: true, stdio: 'ignore'});
let socket;
try {
  let version;
  for (let attempt = 0; attempt < 100; attempt++) {
    try {
      version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
      break;
    } catch {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  if (!version) throw new Error('Owned browser did not start');
  socket = new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, {once:true});
    socket.addEventListener('error', reject, {once:true});
  });
  let next = 0;
  const pending = new Map();
  let completed;
  let guid;
  const downloaded = new Promise(resolve => {completed = resolve;});
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const callback = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) callback.reject(new Error('Browser command failed'));
      else callback.resolve(message.result);
    }
    if (message.method === 'Browser.downloadWillBegin') guid = message.params.guid;
    if (message.method === 'Browser.downloadProgress' && message.params.guid === guid && message.params.state === 'completed') {
      completed(message.params);
    }
  });
  const command = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = ++next;
    pending.set(id, {resolve, reject});
    socket.send(JSON.stringify({id, method, params, ...(sessionId ? {sessionId} : {})}));
  });
  await command('Browser.setDownloadBehavior', {behavior:'allowAndName',downloadPath:directory,eventsEnabled:true});
  const {targetId} = await command('Target.createTarget', {url:'about:blank'});
  const {sessionId} = await command('Target.attachToTarget', {targetId,flatten:true});
  await command('Network.enable', {}, sessionId);
  await command('Network.setExtraHTTPHeaders', {headers:{'X-Redmine-API-Key':input.key}}, sessionId);
  const timeout = setTimeout(() => completed(null), 15000);
  await command('Page.navigate', {url:input.url}, sessionId);
  const event = await downloaded;
  clearTimeout(timeout);
  if (!event) throw new Error('Authenticated browser download timed out');
  const content = await readFile(resolve(directory, guid));
  if (content.toString('utf8') !== 'hello') throw new Error('Browser attachment content mismatch');
  process.stdout.write(JSON.stringify({status:'passed',bytes:content.length}));
} finally {
  socket?.close();
  if (browser.pid) {
    const killer = spawn('taskkill', ['/PID',String(browser.pid),'/T','/F'], {windowsHide:true,stdio:'ignore'});
    await new Promise(resolve => killer.on('exit', resolve));
  }
}
