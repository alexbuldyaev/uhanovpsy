"use strict";

const tg = window.Telegram && window.Telegram.WebApp;
const app = document.getElementById("app");
const LEVEL_COLORS = ["var(--l0)", "var(--l1)", "var(--l2)", "var(--l3)", "var(--l4)"];

let config = null;
const state = {
  screen: "intro",
  selected: [],     // id выбранных тестов
  answers: {},      // { testId: [value, ...] }
  t: 0,             // индекс текущего теста среди выбранных
  q: 0,             // индекс текущего вопроса
};

// ---------- Подсчёт баллов (та же логика продублирована в bot/scoring.py) ----------
const itemOptions = (test, item) => item.options || test.options;

function sumItems(test, answers, indexes) {
  let raw = 0;
  for (const i of indexes) {
    const item = test.items[i];
    const values = itemOptions(test, item).map(o => o.value);
    const v = answers[i];
    raw += item.reverse ? Math.max(...values) + Math.min(...values) - v : v;
  }
  const total = raw * (test.scoring.multiplier || 1);
  return { total, band: test.scoring.bands.find(b => total <= b.max) };
}

function scoreTest(test, answers) {
  const crisis = test.items.some((item, i) => item.crisis && answers[i] > 0);
  const subs = test.scoring.subscales;
  if (subs) {
    const subscales = subs
      .map(s => ({ ...s, ...sumItems(test, answers, s.items) }))
      .sort((a, b) => b.total - a.total);
    return { subscales, band: subscales[0].band, crisis };
  }
  return { ...sumItems(test, answers, test.items.map((_, i) => i)), crisis };
}

// ---------- Рендер ----------
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const selectedTests = () => config.tests.filter(t => state.selected.includes(t.id));

function render() {
  window.scrollTo(0, 0);
  ({ intro: renderIntro, select: renderSelect, quiz: renderQuiz, results: renderResults })[state.screen]();
  updateBackButton();
}

function renderIntro() {
  app.innerHTML = `
    <h1>Психологический чекап</h1>
    <p>Несколько коротких научно обоснованных опросников помогут оценить настроение, тревогу, стресс и общее самочувствие. Это займёт 5–7 минут.</p>
    <div class="card">
      <p><b>Важно:</b> это скрининг, а не диагноз. Результаты помогают понять, стоит ли обратить внимание на своё состояние и обратиться к специалисту.</p>
      <p class="muted">Ответы отправляются только этому боту и хранятся, чтобы вы могли отслеживать динамику. Удалить их можно командой /delete.</p>
    </div>
    <button class="btn" id="start">Начать</button>`;
  document.getElementById("start").onclick = () => {
    state.selected = config.tests.filter(t => !t.optional).map(t => t.id);
    state.screen = "select";
    render();
  };
}

function renderSelect() {
  app.innerHTML = `
    <h1>Что проверим?</h1>
    <p class="muted">Базовый чекап — первые четыре теста. Дополнительные можно отметить по желанию.</p>
    ${config.tests.map(t => `
      <label class="card check">
        <input type="checkbox" value="${t.id}" ${state.selected.includes(t.id) ? "checked" : ""}>
        <span><b>${esc(t.title)}</b> · ${esc(t.name)}<br>
        <span class="muted">${esc(t.description)} · ${t.items.length} вопр.${t.optional ? " · дополнительно" : ""}</span></span>
      </label>`).join("")}
    <div class="footer-actions"><button class="btn" id="go">Перейти к вопросам</button></div>`;
  const go = document.getElementById("go");
  const sync = () => {
    state.selected = [...app.querySelectorAll("input:checked")].map(i => i.value);
    go.disabled = state.selected.length === 0;
    go.style.opacity = go.disabled ? 0.5 : 1;
  };
  app.querySelectorAll("input").forEach(i => (i.onchange = sync));
  go.onclick = () => {
    state.answers = {};
    state.t = 0; state.q = 0;
    state.screen = "quiz";
    render();
  };
}

function renderQuiz() {
  const tests = selectedTests();
  const test = tests[state.t];
  const totalQ = tests.reduce((n, t) => n + t.items.length, 0);
  const doneQ = tests.slice(0, state.t).reduce((n, t) => n + t.items.length, 0) + state.q;
  const current = (state.answers[test.id] || [])[state.q];

  app.innerHTML = `
    <p class="muted">${esc(test.title)} · ${state.q + 1} из ${test.items.length}</p>
    <div class="progress"><div style="width:${(doneQ / totalQ) * 100}%"></div></div>
    <p class="muted">${esc(test.instruction)}</p>
    <div class="question">${esc(test.items[state.q].text)}</div>
    ${itemOptions(test, test.items[state.q]).map(o => `
      <button class="opt ${current === o.value ? "selected" : ""}" data-v="${o.value}">${esc(o.label)}</button>`).join("")}`;

  app.querySelectorAll(".opt").forEach(btn => {
    btn.onclick = () => {
      (state.answers[test.id] ||= [])[state.q] = Number(btn.dataset.v);
      btn.classList.add("selected");
      tg?.HapticFeedback?.selectionChanged();
      setTimeout(next, 150);
    };
  });
}

function next() {
  const tests = selectedTests();
  if (state.q < tests[state.t].items.length - 1) state.q++;
  else if (state.t < tests.length - 1) { state.t++; state.q = 0; }
  else state.screen = "results";
  render();
}

function back() {
  const tests = selectedTests();
  if (state.screen === "select") state.screen = "intro";
  else if (state.screen === "quiz") {
    if (state.q > 0) state.q--;
    else if (state.t > 0) { state.t--; state.q = tests[state.t].items.length - 1; }
    else state.screen = "select";
  } else if (state.screen === "results") {
    state.screen = "quiz";
    state.t = tests.length - 1;
    state.q = tests[state.t].items.length - 1;
  }
  render();
}

function renderResults() {
  const results = selectedTests().map(t => ({ test: t, ...scoreTest(t, state.answers[t.id]) }));
  const crisis = results.some(r => r.crisis);
  const worst = Math.max(0, ...results.filter(r => !r.test.excludeFromSummary).map(r => r.band.level));
  const summary = (worst >= 3 || crisis)
    ? "Некоторые показатели говорят о выраженных трудностях. Мы рекомендуем обратиться к специалисту — это нормальный и действенный шаг."
    : worst === 2
      ? "Есть показатели, на которые стоит обратить внимание. Хорошая идея — обсудить своё состояние с психологом."
      : "В целом ваше состояние в пределах нормы. Повторяйте чекап раз в месяц, чтобы следить за динамикой.";

  app.innerHTML = `
    <h1>Ваш чекап</h1>
    ${crisis ? crisisBlock() : ""}
    <div class="card"><p style="margin:0">${summary}</p></div>
    ${results.map(r => {
      if (r.subscales) return subscalesCard(r);
      const s = r.test.scoring;
      const pct = (r.total / s.max) * 100;
      const color = LEVEL_COLORS[r.band.level];
      return `
      <div class="card">
        <div class="result-head"><h2>${esc(r.test.title)}</h2>
          <span class="score">${r.total}${s.unit || ""} / ${s.max}${s.unit || ""}</span></div>
        <div class="bar"><div style="width:${pct}%;background:${color}"></div></div>
        <span class="badge" style="background:${color}">${esc(r.band.label)}</span>
        <p style="margin:0">${esc(r.band.advice)}</p>
        <p class="muted" style="margin:6px 0 0">${esc(r.test.name)} · ${esc(r.test.description)}</p>
      </div>`;
    }).join("")}
    <p class="muted">Результаты скрининга не являются медицинским диагнозом.</p>
    <div class="footer-actions">
      <button class="btn" id="send">${tg?.initData ? "Сохранить и отправить в чат" : "Готово"}</button>
    </div>`;

  document.getElementById("send").onclick = () => {
    const payload = JSON.stringify({ v: config.version, answers: state.answers });
    if (tg && tg.initData) tg.sendData(payload); // закрывает Mini App и передаёт данные боту
    else console.log("payload:", payload);
  };
}

function subscalesCard(r) {
  const s = r.test.scoring;
  return `
    <div class="card">
      <h2>${esc(r.test.title)}</h2>
      <p class="muted">${esc(r.test.name)} · баллы по каждой ловушке от 10 до ${s.max}. 30 и выше — ловушка заметна в вашей жизни.</p>
      ${r.subscales.map(x => {
        const color = LEVEL_COLORS[x.band.level];
        return `
        <div class="sub">
          <div class="result-head"><b>${esc(x.title)}</b><span class="score">${x.total}</span></div>
          <div class="bar"><div style="width:${(x.total / s.max) * 100}%;background:${color}"></div></div>
          ${x.band.level >= 2 ? `<span class="badge" style="background:${color}">${esc(x.band.label)}</span>
          <p class="muted" style="margin:0">${esc(x.description)} ${esc(x.band.advice)}</p>` : ""}
        </div>`;
      }).join("")}
    </div>`;
}

function crisisBlock() {
  const c = config.crisis;
  return `
    <div class="card crisis">
      <h2>${esc(c.title)}</h2>
      <p>${esc(c.text)}</p>
      ${c.contacts.map(x => `<p style="margin:4px 0">${esc(x.label)}: <a href="tel:${esc(x.phone.split("/")[0].trim())}">${esc(x.phone)}</a></p>`).join("")}
    </div>`;
}

function updateBackButton() {
  if (!tg) return;
  state.screen === "intro" ? tg.BackButton.hide() : tg.BackButton.show();
}

// ---------- Старт ----------
(async function init() {
  if (tg) {
    tg.ready();
    tg.expand();
    tg.BackButton.onClick(back);
  }
  try {
    config = await (await fetch("tests.json", { cache: "no-cache" })).json();
    render();
  } catch (e) {
    app.innerHTML = `<p class="center">Не удалось загрузить тесты. Попробуйте позже.</p>`;
  }
})();
