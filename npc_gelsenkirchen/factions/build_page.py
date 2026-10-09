# Сборка страницы «Фракции Гельзенкирхена» из JSON агентов + обзорного JSON.
# python3 build_page.py -> factions.html (данные встроены; ответы автора — в db артефакта, коллекция "reviews")
import json, os, glob, html

HERE = os.path.dirname(os.path.abspath(__file__))
data = {"factions": []}
for f in sorted(glob.glob(os.path.join(HERE, "data", "[A-Z]_*.json"))):
	data["factions"] += json.load(open(f, encoding="utf-8"))["factions"]
ORDER = ["smoke_cult", "shut_ins", "traders", "bandits", "liquidators", "greys"]
data["factions"].sort(key=lambda x: ORDER.index(x["id"]) if x["id"] in ORDER else 99)
data["overview"] = json.load(open(os.path.join(HERE, "data", "overview.json"), encoding="utf-8"))
_rp = os.path.join(HERE, "data", "romance.json")
data["romance"] = json.load(open(_rp, encoding="utf-8")) if os.path.exists(_rp) else None
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

PAGE = r"""<title>Фракции Гельзенкирхена</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Narrow:wght@500;700&family=Archivo:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: дело-досье — слева реестр фракций (как список домов в «Плане»), справа раскрытая папка фракции; у каждой карточки штамп решения и поле замечания */
:root {
  --paper: #e8ebe8; --sheet: #f6f7f5; --ink: #1f2624; --muted: #5d6764; --line: #c9cfcb; --brick: #a8482b; --focus: #d9871f;
  --ok: #2f7d4f; --chg: #b7791f; --no: #b23a3a;
  --f-love: #b4436c; --f-smoke: #7d68a8; --f-shut: #3f8061; --f-trade: #b8801f; --f-band: #b23a3a; --f-liq: #b89a12; --f-grey: #6b787c;
  --display: "Archivo Narrow", "Arial Narrow", sans-serif;
  --body: "Archivo", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: #161b1a; --sheet: #1e2422; --ink: #e3e8e5; --muted: #98a39f; --line: #333b38; --brick: #d2694a; --focus: #f0a43c;
  --ok: #5fb07f; --chg: #e0a646; --no: #e06a5e;
  --f-love: #e07a9e; --f-smoke: #a993d6; --f-shut: #6bb38f; --f-trade: #e0a84a; --f-band: #e06a5e; --f-liq: #e2c440; --f-grey: #9aa7ab; color-scheme: dark } }
:root[data-theme="dark"] {
  --paper: #161b1a; --sheet: #1e2422; --ink: #e3e8e5; --muted: #98a39f; --line: #333b38; --brick: #d2694a; --focus: #f0a43c;
  --ok: #5fb07f; --chg: #e0a646; --no: #e06a5e;
  --f-love: #e07a9e; --f-smoke: #a993d6; --f-shut: #6bb38f; --f-trade: #e0a84a; --f-band: #e06a5e; --f-liq: #e2c440; --f-grey: #9aa7ab; color-scheme: dark }
* { box-sizing: border-box }
body { background: var(--paper); color: var(--ink); font: 15px/1.5 var(--body); margin: 0; padding-inline: 16px; padding-block: 14px 40px }
.wrap { max-width: 1240px; margin: 0 auto; display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px }
.wrap > * { min-width: 0 }
header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 18px }
h1 { font: 700 28px/1.1 var(--display); margin: 0; text-wrap: balance }
.stat { font: 500 12.5px var(--mono); color: var(--muted); font-variant-numeric: tabular-nums }
.stat b { color: var(--brick); font-weight: 500 }
.lead { margin: 0; color: var(--muted); max-width: 80ch; font-size: 14px }
.tools { display: flex; flex-wrap: wrap; gap: 8px; align-items: center }
.seg { display: inline-flex; border: 1px solid var(--line); border-radius: 4px; overflow: hidden }
.seg button { border: 0; border-radius: 0; background: var(--sheet); padding: 6px 12px; font: 500 13px var(--body); color: var(--ink); cursor: pointer }
.seg button[aria-pressed="true"] { background: var(--ink); color: var(--sheet) }
button, textarea, input { font: inherit; color: var(--ink) }
button:focus-visible, textarea:focus-visible { outline: 2px solid var(--focus); outline-offset: 1px }
main { display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 14px; align-items: start }
nav { position: sticky; top: calc(env(safe-area-inset-top, 0px) + 8px); display: grid; gap: 4px; background: var(--sheet); border: 1px solid var(--line); border-radius: 6px; padding: 8px }
nav button { display: grid; grid-template-columns: 10px 1fr auto; gap: 8px; align-items: center; text-align: left; background: none; border: 0; border-radius: 4px; padding: 8px; cursor: pointer; color: var(--ink) }
nav button[aria-current="true"] { background: var(--paper) }
nav .sw { width: 10px; height: 26px; border-radius: 2px }
nav .nm { font: 700 15px/1.15 var(--display) }
nav .sub { display: block; font: 400 11.5px var(--mono); color: var(--muted) }
nav .pc { font: 500 11.5px var(--mono); color: var(--muted); font-variant-numeric: tabular-nums }
.sheet { display: grid; gap: 14px; min-width: 0 }
.fhead { border-left: 6px solid var(--fc); padding: 4px 0 4px 14px; display: grid; gap: 4px }
.eyebrow { font: 500 11px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted) }
.fhead h2 { font: 700 30px/1.05 var(--display); margin: 0; text-wrap: balance }
section { display: grid; gap: 10px }
section > h3 { font: 700 19px/1.2 var(--display); margin: 8px 0 0; display: flex; gap: 10px; align-items: baseline }
section > h3 .n { font: 500 12px var(--mono); color: var(--muted) }
.card { background: var(--sheet); border: 1px solid var(--line); border-radius: 6px; padding: 14px; display: grid; gap: 10px; min-width: 0 }
.card[data-st="ok"] { border-color: color-mix(in srgb, var(--ok) 55%, var(--line)) }
.card[data-st="chg"] { border-color: color-mix(in srgb, var(--chg) 65%, var(--line)) }
.card[data-st="no"] { border-color: color-mix(in srgb, var(--no) 60%, var(--line)); opacity: .82 }
.card h4 { font: 700 17px/1.2 var(--display); margin: 0 }
.card .meta { font: 400 12.5px var(--mono); color: var(--muted) }
.card p { margin: 0; max-width: 75ch }
.quote { border-left: 3px solid var(--fc); padding: 2px 0 2px 12px; font-style: italic }
.grid2 { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 10px; align-items: start }
dl.kv { display: grid; grid-template-columns: minmax(0, max-content) minmax(0, 1fr); gap: 4px 12px; margin: 0; font-size: 14px }
dl.kv dt { color: var(--muted); font: 400 12.5px var(--mono); padding-top: 2px }
dl.kv dd { margin: 0; min-width: 0 }
.lines { margin: 0; padding: 0; list-style: none; display: grid; gap: 4px }
.lines li { padding-left: 14px; position: relative }
.lines li::before { content: "»"; position: absolute; left: 0; color: var(--fc) }
.script { display: grid; gap: 6px; font-size: 14px }
.script .who { font: 500 12px var(--mono); color: var(--fc); text-transform: uppercase; letter-spacing: .05em }
.choices { display: grid; gap: 6px; border-top: 1px dashed var(--line); padding-top: 8px }
.choices div { display: grid; grid-template-columns: auto 1fr; gap: 8px }
.choices .k { font: 500 12px var(--mono); color: var(--muted) }
ol.steps { margin: 0; padding-left: 22px; display: grid; gap: 3px }
.tag { display: inline-block; font: 500 11px var(--mono); border: 1px solid var(--line); border-radius: 3px; padding: 1px 6px; color: var(--muted) }
.tag.new { border-color: var(--brick); color: var(--brick) }
table.items { width: 100%; border-collapse: collapse; font-size: 14px }
table.items th { text-align: left; font: 500 11px var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--line); padding: 6px 8px }
table.items td { border-bottom: 1px solid var(--line); padding: 8px; vertical-align: top }
table.items td code { font: 400 12px var(--mono); color: var(--muted) }
.tblwrap { overflow-x: auto }
.rel { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 8px }
.rel div { border-left: 4px solid var(--rc); padding: 4px 10px; font-size: 14px; background: var(--paper); border-radius: 0 4px 4px 0 }
.rel b { font: 700 14px var(--display); display: block }
.review { display: grid; gap: 8px; border-top: 1px solid var(--line); padding-top: 10px }
.stamps { display: flex; flex-wrap: wrap; gap: 6px; align-items: center }
.stamps button { background: transparent; border: 1.5px solid var(--line); border-radius: 3px; padding: 4px 10px; font: 600 12px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); cursor: pointer }
.stamps button[data-v="ok"][aria-pressed="true"] { border-color: var(--ok); color: var(--ok); background: color-mix(in srgb, var(--ok) 10%, transparent) }
.stamps button[data-v="chg"][aria-pressed="true"] { border-color: var(--chg); color: var(--chg); background: color-mix(in srgb, var(--chg) 12%, transparent) }
.stamps button[data-v="no"][aria-pressed="true"] { border-color: var(--no); color: var(--no); background: color-mix(in srgb, var(--no) 10%, transparent) }
.stamps .who { font: 400 12px var(--mono); color: var(--muted); margin-left: auto }
.review textarea { width: 100%; min-height: 54px; resize: vertical; background: var(--paper); border: 1px solid var(--line); border-radius: 4px; padding: 7px 9px; font-size: 14px }
.review .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap }
.review .save { background: var(--brick); border: 1px solid var(--brick); color: #fff; border-radius: 4px; padding: 5px 12px; font: 600 13px var(--body); cursor: pointer }
.review .msg { font: 400 12px var(--mono); color: var(--muted) }
.q .qtext { font-weight: 600 }
.banner { font: 400 13px var(--mono); color: var(--muted); background: var(--sheet); border: 1px dashed var(--line); border-radius: 6px; padding: 8px 12px }
.matrix { border-collapse: collapse; font-size: 13px; min-width: 640px }
.matrix th, .matrix td { border: 1px solid var(--line); padding: 6px 8px; vertical-align: top; text-align: left }
.matrix th { font: 700 13px var(--display); background: var(--sheet) }
.matrix td.self { background: var(--paper) }
@media (max-width: 860px) { main { grid-template-columns: minmax(0, 1fr) } nav { position: static; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)) } }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto } }
</style>

<div class="wrap">
  <header>
    <h1>Фракции Гельзенкирхена</h1>
    <span class="stat" id="stat"></span>
  </header>
  <p class="lead">Концепции шести групп «Оставшихся»: почему люди остались в закрытом городе, где живут, кто они, что носят и какие задания дают. У каждого пункта — штамп решения и поле замечания; у открытых вопросов — поле ответа. Всё сохраняется сразу и видно мне.</p>
  <div class="tools">
    <div class="seg" role="group" aria-label="Фильтр карточек">
      <button type="button" id="fAll" aria-pressed="true">все</button>
      <button type="button" id="fOpen" aria-pressed="false">без решения</button>
      <button type="button" id="fChg" aria-pressed="false">к изменению</button>
    </div>
    <span class="banner" id="dbstate">Загружаю сохранённые решения…</span>
  </div>
  <main>
    <nav id="nav" aria-label="Фракции"></nav>
    <div class="sheet" id="sheet"></div>
  </main>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById("data").textContent);
const COLORS = { smoke_cult: "--f-smoke", shut_ins: "--f-shut", traders: "--f-trade", bandits: "--f-band", liquidators: "--f-liq", greys: "--f-grey" };
const NAMES = Object.fromEntries(D.factions.map(f => [f.id, f.title]));
const reviews = {};          // key -> {status, note, by, at}
let db = null, me = null, canWrite = true, filter = "all";
let current = "overview";
try { const h = location.hash.slice(1); if (h) current = h; } catch (e) {}

const qh = q => { let h = 5381; for (const c of String(q)) h = ((h << 5) + h + c.codePointAt(0)) >>> 0; return h.toString(36); };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const col = id => `var(${COLORS[id] || "--muted"})`;

// --- все ключи карточек (для счётчиков) ---
function keysOf(f) {
  const k = [`${f.id}.concept`, `${f.id}.why`, `${f.id}.role`, `${f.id}.relations`];
  (f.places || []).forEach(x => k.push(`${f.id}.place.${x.id}`));
  (f.characters || []).forEach(x => k.push(`${f.id}.char.${x.id}`));
  if ((f.items || []).length) k.push(`${f.id}.items`);
  (f.dialogues || []).forEach(x => k.push(`${f.id}.dlg.${x.id}`));
  (f.missions || []).forEach(x => k.push(`${f.id}.mis.${x.id}`));
  (f.open_questions || []).forEach((q, i) => k.push(`${f.id}.q.${qh(q)}`));
  return k;
}
function romanceKeys() {
  const r = D.romance; if (!r) return [];
  const k = Object.keys(r.system || {}).map(x => `rom.sys.${x}`);
  (r.romances || []).forEach(x => { k.push(`rom.${x.id}.line`, `rom.${x.id}.quests`, `rom.${x.id}.space`, `rom.${x.id}.visit`); (x.dialogues || []).forEach(d => k.push(`rom.${x.id}.dlg.${d.id}`)); (x.open_questions || []).forEach((q, i) => k.push(`rom.${x.id}.q.${qh(q)}`)); });
  (r.friendships || []).forEach(x => { k.push(`fr.${x.id}`); (x.open_questions || []).forEach((q, i) => k.push(`fr.${x.id}.q.${qh(q)}`)); });
  (r.open_questions || []).forEach((q, i) => k.push(`rom.q.${qh(q)}`));
  return k;
}
function overviewKeys() {
  const o = D.overview, k = ["ov.why", "ov.matrix"];
  (o.cross_missions || []).forEach(m => k.push(`ov.cross.${m.id}`));
  (o.questions || []).forEach((q, i) => k.push(`ov.q.${qh(q)}`));
  return k;
}
const done = key => reviews[key] && (reviews[key].status || (reviews[key].note || "").trim());

function renderStat() {
  const all = overviewKeys().concat(romanceKeys(), ...D.factions.map(keysOf));
  const n = all.filter(done).length;
  document.getElementById("stat").innerHTML = `${all.length} пунктов · <b>${n}</b> с решением · ${D.factions.length} фракций`;
}

function renderNav() {
  const nav = document.getElementById("nav");
  const items = [{ id: "overview", title: "Общая концепция", sub: "почему остались · связи", keys: overviewKeys(), c: "var(--brick)" }]
    .concat(D.factions.map(f => ({ id: f.id, title: f.title.split(/[«(—]/)[0].trim(), sub: (f.title.match(/«[^»]+»|\([^)]+\)/) || [""])[0], keys: keysOf(f), c: col(f.id) })))
    .concat(D.romance ? [{ id: "romance", title: "Отношения", sub: "любовные линии · личные задания · гости", keys: romanceKeys(), c: "var(--f-love)" }] : []);
  nav.innerHTML = items.map(it => `<button type="button" data-id="${it.id}" aria-current="${it.id === current}">
      <span class="sw" style="background:${it.c}"></span>
      <span><span class="nm">${esc(it.title)}</span><span class="sub">${esc(it.sub)}</span></span>
      <span class="pc">${it.keys.filter(done).length}/${it.keys.length}</span></button>`).join("");
  nav.querySelectorAll("button").forEach(b => b.onclick = () => { current = b.dataset.id; try { history.replaceState(null, "", "#" + current); } catch (e) {} render(); window.scrollTo({ top: 0 }); });
}

// --- блок решения под карточкой ---
function reviewBox(key, opts = {}) {
  const r = reviews[key] || {};
  const label = opts.question ? "Ответ" : "Замечание";
  const ph = opts.question ? "Ваш ответ на вопрос" : "Что поменять, что оставить, идеи";
  return `<div class="review" data-key="${key}">
    ${opts.question ? "" : `<div class="stamps" role="group" aria-label="Решение">
      <button type="button" data-v="ok" aria-pressed="${r.status === "ok"}">да</button>
      <button type="button" data-v="chg" aria-pressed="${r.status === "chg"}">изменить</button>
      <button type="button" data-v="no" aria-pressed="${r.status === "no"}">нет</button>
      <span class="who" data-who></span></div>`}
    <label class="eyebrow" for="t_${key}">${label}</label>
    <textarea id="t_${key}" placeholder="${ph}">${esc(r.note || "")}</textarea>
    <div class="row"><button type="button" class="save">Сохранить</button><span class="msg" role="status">сохраняется само при наборе</span></div>
  </div>`;
}
function card(key, inner, extraClass = "") {
  const st = (reviews[key] || {}).status || "";
  return `<div class="card ${extraClass}" data-card="${key}" data-st="${st}">${inner}${reviewBox(key, { question: extraClass.includes("q") })}</div>`;
}

function renderOverview() {
  const o = D.overview;
  let h = `<div class="fhead" style="--fc:var(--brick)"><span class="eyebrow">Общая концепция</span><h2>${esc(o.title)}</h2></div>`;
  h += `<section><h3>Почему люди остались</h3>` + card("ov.why", `<p>${esc(o.why_stayed)}</p>` +
    `<dl class="kv">${D.factions.map(f => `<dt style="color:${col(f.id)}">${esc(f.title.split(/[«(—]/)[0].trim())}</dt><dd>${esc(f.why_stayed)}</dd>`).join("")}</dl>`) + `</section>`;
  h += `<section><h3>Кто с кем <span class="n">отношения фракций (строка → как относится к столбцу)</span></h3>` + card("ov.matrix",
    `<div class="tblwrap"><table class="matrix"><thead><tr><th></th>${D.factions.map(f => `<th style="color:${col(f.id)}">${esc(f.title.split(/[«(—]/)[0].trim())}</th>`).join("")}</tr></thead><tbody>` +
    D.factions.map(a => `<tr><th style="color:${col(a.id)}">${esc(a.title.split(/[«(—]/)[0].trim())}</th>` + D.factions.map(b => a.id === b.id ? `<td class="self">—</td>` : `<td>${esc((a.relations || {})[b.id] || "")}</td>`).join("") + `</tr>`).join("") +
    `</tbody></table></div>`) + `</section>`;
  if ((o.decisions || []).length) h += `<section><h3>Принятые решения автора <span class="n">${o.decisions.length}</span></h3><div class="card"><ol class="steps">${o.decisions.map(d => `<li>${esc(d)}</li>`).join("")}</ol></div></section>`;
  if ((o.cross_missions || []).length) h += `<section style="--fc:var(--brick)"><h3>Сквозные расследования <span class="n">через родственников в разных фракциях</span></h3><div class="grid2">${o.cross_missions.map(m => card(`ov.cross.${m.id}`, missionHTML(m))).join("")}</div></section>`;
  if ((o.notes || []).length) h += `<section><h3>Как это ложится на игру</h3><div class="card"><ul class="lines" style="--fc:var(--brick)">${o.notes.map(n => `<li>${esc(n)}</li>`).join("")}</ul></div></section>`;
  if ((o.questions || []).length) h += `<section><h3>Общие вопросы <span class="n">${o.questions.length}</span></h3>` + o.questions.map((q, i) => card(`ov.q.${qh(q)}`, `<p class="qtext">${esc(q)}</p>`, "q")).join("") + `</section>`;
  return h;
}

function missionHTML(m) {
  return `<h4>${esc(m.title)}</h4><span class="meta">${esc(m.type || "")}${m.giver ? " · даёт: " + esc(m.giver) : ""}</span> ${m.new_mechanic ? `<span class="tag new">новая механика</span>` : ""}
      <p>${esc(m.summary)}</p>${(m.steps || []).length ? `<ol class="steps">${m.steps.map(s => `<li>${esc(s)}</li>`).join("")}</ol>` : ""}
      <dl class="kv">${m.rewards ? `<dt>награда</dt><dd>${esc(m.rewards)}</dd>` : ""}${m.consequences ? `<dt>последствия</dt><dd>${esc(m.consequences)}</dd>` : ""}${m.unlocks ? `<dt>открывает</dt><dd>${esc(m.unlocks)}</dd>` : ""}</dl>`;
}
function dlgHTML(d) {
  return `<h4>${esc(d.title)}</h4><span class="meta">${esc(d.situation || "")}</span>
      <div class="script">${(d.lines || []).map(l => `<div><div class="who">${esc(l.who)}</div>${esc(l.text)}</div>`).join("")}</div>
      ${(d.choices || []).length ? `<div class="choices">${d.choices.map((c, i) => `<div><span class="k">${i + 1}.</span><span>${esc(c.text)} <span class="meta">→ ${esc(c.result)}</span></span></div>`).join("")}</div>` : ""}`;
}
const SYS_NAMES = { affinity: "Близость", personal_space: "Личное пространство", invites: "Приглашение домой", online: "Онлайн и кооператив", content_rules: "Рамки контента 16+ / 18+" };
function renderRomance() {
  const r = D.romance, fc = "var(--f-love)";
  let h = `<div class="fhead" style="--fc:${fc}"><span class="eyebrow">Личные линии</span><h2>Отношения, личные задания и гости</h2></div>`;
  h += `<section style="--fc:${fc}"><h3>Как устроено</h3><div class="grid2">${Object.entries(r.system || {}).map(([k, v]) => card(`rom.sys.${k}`, `<h4>${esc(SYS_NAMES[k] || k)}</h4><p>${esc(v)}</p>`)).join("")}</div></section>`;
  (r.romances || []).forEach(x => {
    h += `<section style="--fc:${fc}"><h3>${esc(x.npc)} <span class="n">${esc(x.faction)} · ${esc(x.age)} · ${esc(x.for_heroes)}</span></h3>`;
    h += card(`rom.${x.id}.line`, `<h4>Линия</h4><p>${esc(x.why_them)}</p>${x.prerequisites ? `<dl class="kv"><dt>условия</dt><dd>${esc(x.prerequisites)}</dd></dl>` : ""}
      <ol class="steps">${(x.stages || []).map(st => `<li><b>${esc(st.name)}.</b> ${esc(st.what_happens)}${st.unlocks ? ` <span class="meta">→ ${esc(st.unlocks)}</span>` : ""}</li>`).join("")}</ol>
      <dl class="kv"><dt>риски и финалы</dt><dd>${esc(x.risks_and_endings)}</dd>${(x.mature_slots || []).length ? `<dt>слоты 18+</dt><dd>${x.mature_slots.map(m => `<code>${esc(m)}</code>`).join("<br>")}</dd>` : ""}</dl>`);
    h += `<div class="grid2">` + card(`rom.${x.id}.quests`, `<h4>Личные задания</h4>` + (x.personal_quests || []).map(m => `<div class="card" style="padding:10px">${missionHTML(m)}</div>`).join("")) +
      `<div style="display:grid;gap:10px">` + card(`rom.${x.id}.space`, `<h4>Личное пространство: ${esc((x.personal_space || {}).name)}</h4><span class="meta">${esc((x.personal_space || {}).location)}</span><p>${esc((x.personal_space || {}).description)}</p>${((x.personal_space || {}).activities || []).length ? `<ul class="lines">${x.personal_space.activities.map(a => `<li>${esc(a)}</li>`).join("")}</ul>` : ""}`) +
      card(`rom.${x.id}.visit`, (() => { const v = x.home_visit || {}; return `<h4>В гостях на базе</h4><dl class="kv"><dt>как позвать</dt><dd>${esc(v.how_to_invite)}</dd><dt>прибытие</dt><dd>${esc(v.arrival)}</dd><dt>ночь (16+)</dt><dd>${esc(v.overnight_16)}</dd><dt>бонус</dt><dd>${esc(v.bonus)}</dd><dt>онлайн</dt><dd>${esc(v.online)}</dd></dl>${(v.activities || []).length ? `<ul class="lines">${v.activities.map(a => `<li>${esc(a)}</li>`).join("")}</ul>` : ""}`; })()) + `</div></div>`;
    if ((x.dialogues || []).length) h += `<div class="grid2">${x.dialogues.map(d => card(`rom.${x.id}.dlg.${d.id}`, dlgHTML(d))).join("")}</div>`;
    (x.open_questions || []).forEach((q, i) => { h += card(`rom.${x.id}.q.${qh(q)}`, `<p class="qtext">${esc(q)}</p>`, "q"); });
    h += `</section>`;
  });
  if ((r.friendships || []).length) {
    h += `<section style="--fc:${fc}"><h3>Дружба и личные пространства <span class="n">${r.friendships.length}</span></h3><div class="grid2">`;
    r.friendships.forEach(x => {
      const ps = x.personal_space || {}, v = x.home_visit;
      h += card(`fr.${x.id}`, `<h4>${esc(x.npc)}</h4><span class="meta">${esc(x.faction)}</span><p>${esc(x.why)}</p>
        ${(x.personal_quests || []).map(m => `<div class="card" style="padding:10px">${missionHTML(m)}</div>`).join("")}
        <dl class="kv"><dt>пространство</dt><dd><b>${esc(ps.name)}</b> — ${esc(ps.location)}. ${esc(ps.description)}</dd>
        <dt>в гости</dt><dd>${typeof v === "string" ? esc(v) : v ? esc(v.cannot_visit || [v.how_to_invite, v.arrival, (v.activities || []).join("; "), v.bonus].filter(Boolean).join(" · ")) : ""}</dd>
        ${x.rewards ? `<dt>награда</dt><dd>${esc(x.rewards)}</dd>` : ""}</dl>`);
    });
    h += `</div>`;
    r.friendships.forEach(x => (x.open_questions || []).forEach((q, i) => { h += card(`fr.${x.id}.q.${qh(q)}`, `<p class="qtext"><span class="meta">${esc(x.npc)}:</span> ${esc(q)}</p>`, "q"); }));
    h += `</section>`;
  }
  if ((r.open_questions || []).length) h += `<section style="--fc:${fc}"><h3>Общие вопросы <span class="n">${r.open_questions.length}</span></h3>` + r.open_questions.map((q, i) => card(`rom.q.${qh(q)}`, `<p class="qtext">${esc(q)}</p>`, "q")).join("") + `</section>`;
  return h;
}

function renderFaction(f) {
  const fc = col(f.id);
  let h = `<div class="fhead" style="--fc:${fc}"><span class="eyebrow">Фракция</span><h2>${esc(f.title)}</h2></div>`;
  h += `<section style="--fc:${fc}"><h3>Концепция</h3>` + card(`${f.id}.concept`,
    `<p class="quote"><span class="eyebrow">Идея автора</span><br>${esc(f.author_idea)}</p><p>${esc(f.concept)}</p>${f.look_and_mood ? `<dl class="kv"><dt>облик</dt><dd>${esc(f.look_and_mood)}</dd></dl>` : ""}`) +
    card(`${f.id}.why`, `<h4>Почему остались</h4><p>${esc(f.why_stayed)}</p>`) +
    card(`${f.id}.role`, `<h4>Роль в игре</h4><p>${esc(f.gameplay_role)}</p>`) +
    card(`${f.id}.relations`, `<h4>Отношения</h4><div class="rel">${Object.entries(f.relations || {}).map(([k, v]) => `<div style="--rc:${col(k)}"><b>${esc((NAMES[k] || k).split(/[«(—]/)[0].trim())}</b>${esc(v)}</div>`).join("")}</div>`) + `</section>`;
  const sec = (title, list, fn, cls = "grid2") => list && list.length ? `<section style="--fc:${fc}"><h3>${title} <span class="n">${list.length}</span></h3><div class="${cls}">${list.map(fn).join("")}</div></section>` : "";
  h += sec("Места", f.places, p => card(`${f.id}.place.${p.id}`, `<h4>${esc(p.name)}</h4><span class="meta">${esc(p.location)}</span><p>${esc(p.description)}</p>${p.implementation ? `<dl class="kv"><dt>в игре</dt><dd>${esc(p.implementation)}</dd></dl>` : ""}`));
  h += sec("Персонажи", f.characters, c => card(`${f.id}.char.${c.id}`, `<h4>${esc(c.name)}</h4><span class="meta">${esc(c.role)}${c.where ? " · " + esc(c.where) : ""}</span>
      <dl class="kv"><dt>облик</dt><dd>${esc(c.look)}</dd><dt>характер</dt><dd>${esc(c.personality)}</dd><dt>речь</dt><dd>${esc(c.speech)}</dd></dl>
      ${(c.lines || []).length ? `<ul class="lines">${c.lines.map(l => `<li>${esc(l)}</li>`).join("")}</ul>` : ""}`));
  if ((f.items || []).length) h += `<section style="--fc:${fc}"><h3>Предметы <span class="n">${f.items.length}</span></h3>` + card(`${f.id}.items`,
    `<div class="tblwrap"><table class="items"><thead><tr><th>Предмет</th><th>Тип</th><th>Описание</th><th>Зачем</th></tr></thead><tbody>${f.items.map(it => `<tr><td><b>${esc(it.name)}</b><br><code>${esc(it.id)}</code></td><td>${esc(it.type)}</td><td>${esc(it.description)}</td><td>${esc(it.use)}</td></tr>`).join("")}</tbody></table></div>`) + `</section>`;
  h += sec("Диалоги", f.dialogues, d => card(`${f.id}.dlg.${d.id}`, `<h4>${esc(d.title)}</h4><span class="meta">${esc(d.situation)}</span>
      <div class="script">${(d.lines || []).map(l => `<div><div class="who">${esc(l.who)}</div>${esc(l.text)}</div>`).join("")}</div>
      ${(d.choices || []).length ? `<div class="choices">${d.choices.map((c, i) => `<div><span class="k">${i + 1}.</span><span>${esc(c.text)} <span class="meta">→ ${esc(c.result)}</span></span></div>`).join("")}</div>` : ""}`), "grid2");
  h += sec("Задания", f.missions, m => card(`${f.id}.mis.${m.id}`, missionHTML(m)), "grid2");
  if ((f.open_questions || []).length) h += `<section style="--fc:${fc}"><h3>Вопросы автору <span class="n">${f.open_questions.length}</span></h3>` +
    f.open_questions.map((q, i) => card(`${f.id}.q.${qh(q)}`, `<p class="qtext">${esc(q)}</p>`, "q")).join("") + `</section>`;
  return h;
}

function applyFilter() {
  document.querySelectorAll("[data-card]").forEach(c => {
    const r = reviews[c.dataset.card] || {};
    c.hidden = filter === "open" ? !!done(c.dataset.card) : filter === "chg" ? r.status !== "chg" : false;
  });
}

function render() {
  const sheet = document.getElementById("sheet");
  const f = D.factions.find(x => x.id === current);
  sheet.innerHTML = f ? renderFaction(f) : (current === "romance" && D.romance) ? renderRomance() : renderOverview();
  wire(sheet);
  renderNav(); renderStat(); applyFilter(); paintWho();
}

async function paintWho() {
  if (!user) return;
  const ids = [...new Set(Object.values(reviews).map(r => r.by).filter(Boolean))];
  let ps = {};
  try { ps = await user.profiles(ids); } catch (e) {}
  document.querySelectorAll(".review").forEach(box => {
    const r = reviews[box.dataset.key]; const w = box.querySelector("[data-who]");
    if (w) w.textContent = r && r.by ? ((ps[r.by] && ps[r.by].name) || "сохранено") + (r.at ? " · " + new Date(r.at).toLocaleDateString("ru-RU") : "") : "";
  });
}

async function save(key, patch, msgEl) {
  const prev = reviews[key] || {};
  const next = { status: prev.status || "", note: prev.note || "", ...patch, by: me, at: Date.now() };
  reviews[key] = next;
  renderNav(); renderStat();
  const cardEl = document.querySelector(`[data-card="${CSS.escape(key)}"]`);
  if (cardEl) cardEl.dataset.st = next.status || "";
  if (!db) { if (msgEl) msgEl.textContent = "База недоступна — решение не сохранено."; return; }
  try { await db.collection("reviews").doc(key.replace(/\//g, "_")).set({ key, ...next }); if (msgEl) msgEl.textContent = "Сохранено"; }
  catch (e) { if (msgEl) msgEl.textContent = e && e.code === "permission_denied" ? "Нет прав на запись." : "Не сохранилось: " + ((e && e.message) || "ошибка"); }
}

function wire(root) {
  root.querySelectorAll(".review").forEach(box => {
    const key = box.dataset.key, msg = box.querySelector(".msg"), ta = box.querySelector("textarea");
    box.querySelectorAll(".stamps button").forEach(b => b.onclick = () => {
      const v = (reviews[key] || {}).status === b.dataset.v ? "" : b.dataset.v;
      box.querySelectorAll(".stamps button").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.v === v)));
      save(key, { status: v, note: ta.value }, msg);
    });
    box.querySelector(".save").onclick = () => save(key, { note: ta.value }, msg);
    let timer = null;
    ta.addEventListener("input", () => { msg.textContent = "…"; clearTimeout(timer); timer = setTimeout(() => save(key, { note: ta.value }, msg), 900); });
    ta.addEventListener("blur", () => { if (ta.value !== ((reviews[key] || {}).note || "")) { clearTimeout(timer); save(key, { note: ta.value }, msg); } });
  });
}

for (const [id, v] of [["fAll", "all"], ["fOpen", "open"], ["fChg", "chg"]]) document.getElementById(id).onclick = () => {
  filter = v; ["fAll", "fOpen", "fChg"].forEach(x => document.getElementById(x).setAttribute("aria-pressed", String(x === id))); applyFilter();
};

let user = null;
render();
(async () => {
  const st = document.getElementById("dbstate");
  try {
    [db, user] = await Promise.all([claude.use("db"), claude.use("user")]);
  } catch (e) { db = null; }
  if (!db) { st.textContent = "Решения не сохраняются: откройте страницу, войдя в claude.ai."; return; }
  try { me = user ? await user.id() : null; } catch (e) {}
  st.textContent = "Штампы и текст сохраняются сами; кнопка «Сохранить» — на всякий случай.";
  db.collection("reviews").onSnapshot(snap => {
    snap.docs.forEach(d => { const v = d.data(); if (v && v.key) reviews[v.key] = v; });
    // не перерисовываем поле, в котором сейчас печатают
    const active = document.activeElement && document.activeElement.tagName === "TEXTAREA" ? document.activeElement.id : null;
    document.querySelectorAll(".review").forEach(box => {
      const r = reviews[box.dataset.key]; if (!r) return;
      box.querySelectorAll(".stamps button").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.v === r.status)));
      const ta = box.querySelector("textarea"); if (ta.id !== active && ta.value !== (r.note || "")) ta.value = r.note || "";
      const c = box.closest("[data-card]"); if (c) c.dataset.st = r.status || "";
    });
    renderNav(); renderStat(); applyFilter(); paintWho();
  }, () => { st.textContent = "Связь с базой потеряна — обновите страницу."; });
})();
</script>
"""
out = PAGE.replace("__DATA__", payload)
open(os.path.join(HERE, "factions.html"), "w", encoding="utf-8").write(out)
print("ok", len(out) // 1024, "KB")
