// 线上 e2e：页面能开、视频能播、图能载、字体能载、不横向溢出。
// 跑法：NODE_PATH=<某处的 node_modules> node scripts/e2e_online.cjs [url]
const { chromium } = require('playwright-core');

const URL = process.argv[2] || 'https://hkmpn9s6dh-commits.github.io/hackathon-2026-thirtysnows/';
const EXEC = process.env.CHROME_PATH ||
  (process.env.HOME + '/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe');

(async () => {
  const browser = await chromium.launch({ executablePath: EXEC, args: ['--no-sandbox'] });
  let fails = 0;
  const check = (ok, msg) => { console.log((ok ? '  PASS  ' : '  FAIL  ') + msg); if (!ok) fails++; };

  for (const vp of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport: vp });
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto(URL, { waitUntil: 'load', timeout: 60000 });
    await page.waitForTimeout(1500);

    const r = await page.evaluate(async () => {
      const v = document.querySelector('video');
      const imgs = [...document.querySelectorAll('img')];
      try { await document.fonts.ready; } catch (e) {}
      return {
        title: document.title,
        h1: document.querySelector('h1')?.innerText || '',
        videoDur: v ? v.duration : 0,
        videoReady: v ? v.readyState : 0,
        videoSrc: v?.currentSrc?.split('/').pop() || '',
        imgs: imgs.map(i => ({ src: i.src.split('/').pop(), w: i.naturalWidth })),
        fontOk: document.fonts.check('16px NotoSerifSC'),
        overflow: document.documentElement.scrollWidth - window.innerWidth,
        body: document.body.innerText.length,
      };
    });

    check(r.title.includes('Thirty Years'), `[${vp.width}] 标题 ${r.title.slice(0, 40)}`);
    check(r.h1.includes('Thirty Years'), `[${vp.width}] h1 存在`);
    check(Math.abs(r.videoDur - 30) < 0.2, `[${vp.width}] 视频时长 ${r.videoDur.toFixed(2)}s`);
    check(r.videoSrc.includes('thirty-years.mp4'), `[${vp.width}] 视频源 ${r.videoSrc}`);
    check(r.imgs.length >= 4 && r.imgs.every(i => i.w > 0), `[${vp.width}] ${r.imgs.length} 张图全部加载`);
    check(r.fontOk, `[${vp.width}] 子集字体已加载`);
    check(r.overflow <= 1, `[${vp.width}] 无横向溢出（${r.overflow}px）`);
    check(r.body > 1200, `[${vp.width}] 正文长度 ${r.body}`);
    check(errors.length === 0, `[${vp.width}] 无 JS 报错`);

    if (vp.width === 1440) {
      await page.screenshot({ path: 'proof/ui/online-desktop.png', fullPage: false });
      await page.evaluate(() => window.scrollTo(0, 900));
      await page.waitForTimeout(400);
      await page.screenshot({ path: 'proof/ui/online-idea.png' });
    } else {
      await page.screenshot({ path: 'proof/ui/online-mobile.png' });
    }
    await page.close();
  }

  await browser.close();
  console.log(fails === 0 ? '\n线上 e2e 全部通过' : `\n${fails} 项未通过`);
  process.exit(fails === 0 ? 0 : 1);
})();
