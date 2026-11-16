const stagesByLanguage = {zh: [
  {
    user:'我想做个收藏工具，保存网页和笔记。还没想清楚，先帮我看看整体怎么设计。',
    reply:'可以先看三个部分：<strong>内容收集、分类检索、数据保存</strong>。先把核心使用流程串起来，再决定第一版做到哪里。<div class="topic-tags"><span>内容收集</span><span>分类检索</span><span>数据保存</span></div><small>这些是讨论起点，你可以选最关心的部分。</small>',
    description:'先给一张可以修改的地图。议题是导航，顺序由你选择。',
    status:'尚未写入', next:'看看如何讨论', title:'先聊想法，不急着定案', subtitle:'当前框架仍是草案。<br>还没有需要写入的已确认决定。'
  },
  {
    user:'先聊数据保存吧。第一版一定要做多端同步吗？我想简单一点，主要自己在电脑上用。',
    reply:'按这个场景，我建议<strong>第一版先做本地保存</strong>，减少服务器和同步逻辑的维护成本。<small>取舍是：暂时不能跨设备查看收藏。备份与迁移也值得接着讨论。</small>',
    description:'AI 给建议、讲取舍。留在当前话题，让你继续追问或修改。',
    status:'等待你的判断', next:'看看如何沉淀', title:'建议，留在讨论里', subtitle:'“本地保存”目前是 AI 的建议。<br>在你明确拍板前，不写成正式需求。'
  },
  {
    user:'就先做本地保存，多端同步以后再设计。具体存储方案还没想好，先把这个方向记下来。',
    reply:'好，示例中的设计文档会记录<strong>已定方向、理由和暂缓事项</strong>。具体存储选型继续留待讨论，不替你补成决定。',
    description:'只沉淀你明确认可的范围。记录决定，也保留还没想清楚的部分。',
    status:'已确认 · 示例', next:'重新看一遍'
  }
],
en: [
 {user:'I want to build a bookmarking tool for web pages and notes. I am still figuring it out. Help me see the big picture first.',reply:'We can start with three parts: <strong>capturing content, organizing and finding it, and storing it</strong>. Let’s understand the core flow before deciding what belongs in v1.<div class="topic-tags"><span>Capture</span><span>Find</span><span>Store</span></div><small>These are starting points. Choose the part you care about most.</small>',description:'Start with a map you can change. Topics are navigation; you choose the route.',status:'Not recorded',next:'Explore the trade-offs',title:'Explore before deciding',subtitle:'The framework is still a draft.<br>No decisions are ready to be recorded.'},
 {user:'Let’s talk about storage. Does the first version need sync? I would like to keep it simple and mostly use it on my own computer.',reply:'For that situation, I would start with <strong>local storage for v1</strong>. It means less server maintenance and no sync logic to manage.<small>The trade-off: no access from other devices yet. Backup and migration are worth discussing next.</small>',description:'AI recommends and explains the trade-offs. You have room to question or revise.',status:'Your decision to make',next:'See the resulting plan',title:'A suggestion, still in discussion',subtitle:'Local storage is currently an AI recommendation.<br>It is not a requirement until you approve it.'},
 {user:'Let’s use local storage first and design sync later. I have not chosen the storage implementation yet. Record this direction for now.',reply:'The example design document records <strong>the approved direction, the reasoning, and what is deferred</strong>. The storage implementation stays open for discussion.',description:'Document only what you approve, with room for questions you have left open.',status:'Approved · Example',next:'Play it again'}
]};
let language='en';
let currentStage=0;
const tabs=[...document.querySelectorAll('[data-step]')];
const localeText=window.localeText;
const staticText=[];
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
let textNode;
while((textNode=walker.nextNode())){
  if(textNode.parentElement.closest('script,style,[data-copy],#file-status,#next-step,#step-description,#conversation-content,#document-content,.language-switch'))continue;
  const key=textNode.textContent.trim();
  if(Object.prototype.hasOwnProperty.call(localeText,key))staticText.push({node:textNode,en:textNode.textContent,zh:textNode.textContent.replace(key,localeText[key])});
}
const staticAttributes=[];
document.querySelectorAll('[aria-label],meta[content]').forEach(el=>{
  const attr=el.hasAttribute('aria-label')?'aria-label':'content';
  const en=el.getAttribute(attr);
  if(localeText[en])staticAttributes.push({el,attr,en,zh:localeText[en]});
});
const englishTitle=document.title;
const promptText={en:'$talk-to-plan I want to build a bookmarking tool. Help me see the big picture first. Let’s discuss it piece by piece and document decisions once I explicitly approve them.',zh:'$talk-to-plan 我想做一个收藏工具，先帮我梳理整体框架。我们逐块讨论，我明确拍板后，再把结论整理到文档中。'};
const installCommand='npx skills add WT006/talk-to-plan-skill --skill talk-to-plan';
function setStage(index,focus=false){
  currentStage=index;const s=stagesByLanguage[language][index];
  tabs.forEach((t,i)=>{t.setAttribute('aria-selected',String(i===index));t.tabIndex=i===index?0:-1});
  document.getElementById('demo-panel').setAttribute('aria-labelledby',`step-${index}`);
  document.getElementById('conversation-content').innerHTML=`<div class="message user"><span class="avatar">${language==='en'?'You':'你'}</span><p>${s.user}</p></div><div class="message assistant"><span class="avatar">↳</span><div class="reply-text">${s.reply}</div></div>`;
  document.getElementById('file-status').textContent=s.status;
  document.getElementById('step-description').textContent=s.description;
  document.getElementById('next-step').innerHTML=`${s.next} <span aria-hidden="true">${index===2?'↺':'→'}</span>`;
  const saved={en:'<div class="saved-doc"><span>BOOKMARKING TOOL / FIRST VERSION</span><h3>Start with local storage</h3><p><b>✓ Approved direction</b>Store content locally in v1 for use on one device.</p><p><b>The reasoning</b>Keep the first version focused and reduce sync and server maintenance.</p><p class="pending">For later: cross-device sync and the storage implementation.</p></div>',zh:'<div class="saved-doc"><span>收藏工具 / FIRST VERSION</span><h3>从本地使用开始</h3><p><b>✓ 已确认的方向</b>第一版只做本地保存，满足单设备使用。</p><p><b>为什么这样做</b>控制第一版范围，减少同步与服务器维护成本。</p><p class="pending">后续议题：多端同步、具体存储方案。</p></div>'};
  document.getElementById('document-content').innerHTML=index===2?saved[language]:`<div class="empty-doc"><svg viewBox="0 0 40 46" fill="none" aria-hidden="true"><path d="M8 3h16l9 9v31H8zM24 3v10h9M14 23h13M14 29h10M14 35h7" stroke-width="1.2"/></svg><h3>${s.title}</h3><p>${s.subtitle}</p></div>`;
  if(focus)tabs[index].focus();
}
const copyTimers=new Map();
function resetCopyButton(button){button.innerHTML=`${language==='en'?'Copy':'复制'} <span aria-hidden="true">▢</span>`;}
function setLanguage(next){
  language=next==='zh'?'zh':'en';
  document.documentElement.lang=language==='zh'?'zh-CN':'en';
  staticText.forEach(item=>item.node.textContent=item[language]);
  staticAttributes.forEach(item=>item.el.setAttribute(item.attr,item[language]));
  document.title=language==='en'?englishTitle:localeText[englishTitle];
  document.querySelectorAll('[data-lang]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lang===language)));
  document.querySelector('.footer-top a[href*="README"]').href=`https://github.com/WT006/talk-to-plan-skill/blob/main/README${language==='zh'?'.zh-CN':''}.md`;
  document.querySelectorAll('[data-copy]').forEach(b=>{clearTimeout(copyTimers.get(b));resetCopyButton(b)});
  clearTimeout(toastTimeout);document.getElementById('toast').classList.remove('show');document.getElementById('toast').textContent='';
  setStage(currentStage);
}
document.querySelectorAll('[data-lang]').forEach(b=>b.addEventListener('click',()=>setLanguage(b.dataset.lang)));
tabs.forEach((tab,i)=>{tab.addEventListener('click',()=>setStage(i));tab.addEventListener('keydown',event=>{let index=i;if(event.key==='ArrowRight')index=(i+1)%3;else if(event.key==='ArrowLeft')index=(i+2)%3;else if(event.key==='Home')index=0;else if(event.key==='End')index=2;else return;event.preventDefault();setStage(index,true)})});
document.getElementById('next-step').addEventListener('click',()=>setStage((currentStage+1)%3));
let toastTimeout;
function notify(message){const toast=document.getElementById('toast');toast.textContent=message;toast.classList.add('show');clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>toast.classList.remove('show'),2600)}
async function copy(value){try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(value);return true}}catch{}const field=document.createElement('textarea');field.value=value;field.style.cssText='position:fixed;opacity:0;left:-9999px';document.body.appendChild(field);field.select();let ok=false;try{ok=document.execCommand('copy')}finally{field.remove()}return ok}
document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
  const isInstall=button.dataset.copy==='install';
  const ok=await copy(isInstall?installCommand:promptText[language]);
  if(ok){button.textContent=language==='en'?'Copied ✓':'已复制 ✓';notify(language==='en'?(isInstall?'Installation command copied. Paste it into your terminal.':'Starter prompt copied. Paste it into Codex.'):(isInstall?'安装命令已复制，粘贴到终端即可。':'开场提示词已复制，粘贴到 Codex 开始讨论。'));clearTimeout(copyTimers.get(button));copyTimers.set(button,setTimeout(()=>resetCopyButton(button),2200));}
  else notify(language==='en'?'Could not copy. Please select and copy the text manually.':'未能复制，请选中命令后手动复制。');
}));
setLanguage('en');

/* ---------- Motion layer ---------- */
(()=>{
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const langBox=document.querySelector('.language-switch');
  const tabBox=document.querySelector('.demo-tabs');
  function placeIndicators(){
    const lang=langBox.querySelector('[aria-pressed=true]');
    if(lang){langBox.style.setProperty('--pill-x',lang.offsetLeft+'px');langBox.style.setProperty('--pill-w',lang.offsetWidth+'px');langBox.classList.add('ready')}
    const tab=tabBox.querySelector('[aria-selected=true]');
    if(tab){tabBox.style.setProperty('--tab-x',tab.offsetLeft+'px');tabBox.style.setProperty('--tab-w',tab.offsetWidth+'px');tabBox.classList.add('ready')}
  }
  const mo=new MutationObserver(placeIndicators);
  mo.observe(langBox,{attributes:true,subtree:true,attributeFilter:['aria-pressed']});
  mo.observe(tabBox,{attributes:true,subtree:true,attributeFilter:['aria-selected']});
  new MutationObserver(()=>requestAnimationFrame(placeIndicators)).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
  addEventListener('resize',placeIndicators);
  (document.fonts?document.fonts.ready:Promise.resolve()).then(placeIndicators);
  placeIndicators();

  const bar=document.createElement('div');bar.className='scroll-progress';bar.setAttribute('aria-hidden','true');document.body.prepend(bar);
  let ticking=false;
  function onScroll(){if(ticking)return;ticking=true;requestAnimationFrame(()=>{const max=document.documentElement.scrollHeight-innerHeight;bar.style.setProperty('--p',max>0?(scrollY/max).toFixed(4):0);ticking=false})}
  addEventListener('scroll',onScroll,{passive:true});onScroll();

  if(reduce)return;

  const groups=[['.promise-strip'],['.section-heading'],['.demo-shell'],['.principle-list article',true],['.boundary'],['.install-intro'],['.install-step',true],['.faq > div:first-child'],['.faq-list details',true],['.footer']];
  const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{rootMargin:'0px 0px -8% 0px',threshold:.12});
  groups.forEach(([sel,stagger])=>document.querySelectorAll(sel).forEach((el,i)=>{el.classList.add('reveal');if(stagger)el.style.setProperty('--d',(i*0.08)+'s');io.observe(el)}));

  const art=document.querySelector('.hero-art');
  if(art&&matchMedia('(pointer:fine)').matches){
    const hero=document.querySelector('.hero');
    hero.addEventListener('pointermove',e=>{const r=hero.getBoundingClientRect();art.style.setProperty('--mx',((e.clientX-r.left)/r.width-.5).toFixed(3));art.style.setProperty('--my',((e.clientY-r.top)/r.height-.5).toFixed(3))});
    hero.addEventListener('pointerleave',()=>{art.style.setProperty('--mx',0);art.style.setProperty('--my',0)});
  }
})();
