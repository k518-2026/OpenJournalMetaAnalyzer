/**
 * OpenJournalMetaAnalyzer Front-end Client Logic
 * PRISMA 2020 Compliant Workflow & Interactive Forest Plot
 */

const state = {
  keyword: "",
  papers: [],
  searchResponse: null,
  metaResult: null,
  forestPlotSpec: null,
  prismaCounts: {
    records_identified: 0,
    duplicates_removed: 0,
    records_screened: 0,
    records_excluded_screening: 0,
    full_text_assessed: 0,
    full_text_excluded: 0,
    studies_included_qualitative: 0,
    studies_included_quantitative: 0
  },
  geminiApiKey: localStorage.getItem("gemini_api_key") || ""
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupSearch();
  setupScreeningControls();
  setupMetaAnalysis();
  setupSynthesis();
  setupExports();
  setupSettingsModal();
});

// --- Tab Navigation ---
function setupTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-tab");
      switchTab(targetId);
    });
  });

  document.getElementById("btn-goto-screening")?.addEventListener("click", () => switchTab("tab-screening"));
  document.getElementById("btn-goto-meta")?.addEventListener("click", () => switchTab("tab-meta"));
}

function switchTab(tabId) {
  document.querySelectorAll(".nav-tab").forEach(t => {
    if (t.getAttribute("data-tab") === tabId) {
      t.classList.add("active", "text-blue-600");
      t.classList.remove("text-slate-600");
    } else {
      t.classList.remove("active", "text-blue-600");
      t.classList.add("text-slate-600");
    }
  });

  document.querySelectorAll(".tab-pane").forEach(pane => {
    if (pane.id === tabId) {
      pane.classList.remove("hidden");
    } else {
      pane.classList.add("hidden");
    }
  });

  lucide.createIcons();

  if (tabId === "tab-meta" && state.metaResult) {
    // Re-layout plotly if switching to meta tab
    setTimeout(() => {
      const plotEl = document.getElementById("plotly-forest-plot");
      if (plotEl && plotEl.data) {
        Plotly.Plots.resize(plotEl);
      }
    }, 100);
  }
}

// --- Search & Identification ---
function setupSearch() {
  const btnSearch = document.getElementById("btn-search");
  const inputKeyword = document.getElementById("search-keyword");

  btnSearch.addEventListener("click", () => executeSearch());
  inputKeyword.addEventListener("keypress", (e) => {
    if (e.key === "Enter") executeSearch();
  });

  document.querySelectorAll(".quick-tag").forEach(tag => {
    tag.addEventListener("click", () => {
      inputKeyword.value = tag.getAttribute("data-kw");
      executeSearch();
    });
  });
}

async function executeSearch() {
  const kw = document.getElementById("search-keyword").value.trim();
  if (!kw) {
    alert("検索キーワードを入力してください。");
    return;
  }
  state.keyword = kw;

  const yearStart = parseInt(document.getElementById("opt-year-start").value) || null;
  const yearEnd = parseInt(document.getElementById("opt-year-end").value) || null;
  const maxResults = parseInt(document.getElementById("opt-max-results").value) || 20;
  const sortBy = document.getElementById("opt-sort-by").value || "relevance";

  const loadingEl = document.getElementById("search-loading");
  const summaryEl = document.getElementById("ident-summary-card");
  const resultsContainer = document.getElementById("search-results-container");

  loadingEl.classList.remove("hidden");
  summaryEl.classList.add("hidden");
  resultsContainer.innerHTML = "";

  try {
    const res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        keyword: kw,
        year_start: yearStart,
        year_end: yearEnd,
        max_results: maxResults,
        sources: ["openalex", "europe_pmc"],
        sort_by: sortBy
      })
    });

    if (!res.ok) {
      throw new Error(`API error: ${res.statusText}`);
    }

    const data = await res.json();
    state.searchResponse = data;
    state.papers = data.papers || [];

    // Render summary
    document.getElementById("stat-total-ident").innerText = data.prisma_identification.total_records_identified;
    document.getElementById("stat-dup-removed").innerText = data.prisma_identification.duplicate_records_removed;
    document.getElementById("stat-unique-screened").innerText = data.prisma_identification.unique_records_screened;
    summaryEl.classList.remove("hidden");

    document.getElementById("badge-ident-count").innerText = data.prisma_identification.total_records_identified;
    document.getElementById("badge-ident-count").classList.remove("hidden");

    renderSearchResults(state.papers);
    updatePrismaCounts();
    renderScreeningList();
    renderMetaDataMatrix();
  } catch (err) {
    alert("検索エラーが発生しました: " + err.message);
  } finally {
    loadingEl.classList.add("hidden");
  }
}

function renderSearchResults(papers) {
  const container = document.getElementById("search-results-container");
  container.innerHTML = "";

  if (!papers || papers.length === 0) {
    container.innerHTML = `<div class="p-8 text-center text-slate-500 bg-white rounded-lg border">該当するオープンアクセス論文が見つかりませんでした。別のキーワードをお試しください。</div>`;
    return;
  }

  papers.forEach((p, idx) => {
    const authorsStr = p.authors.slice(0, 4).join(", ") + (p.authors.length > 4 ? " et al." : "");
    const card = document.createElement("div");
    card.className = "glass-card p-5 bg-white border border-slate-200 hover:border-blue-300 transition space-y-2";
    card.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center space-x-2 flex-wrap gap-y-1">
            <span class="text-xs px-2 py-0.5 rounded font-bold badge-source">${p.source}</span>
            <span class="text-xs px-2 py-0.5 rounded font-bold badge-oa">Open Access (${p.open_access_status || 'OA'})</span>
            <span class="text-xs text-slate-500 font-medium">${p.year || '出版年不明'}</span>
            <span class="text-xs text-slate-500 font-medium">被引用: ${p.citations}回</span>
          </div>
          <h3 class="text-base font-bold text-slate-900 leading-snug">
            <span class="text-blue-600 font-bold mr-1">#${idx + 1}</span> ${escapeHtml(p.title)}
          </h3>
          <p class="text-xs text-slate-600">${escapeHtml(authorsStr)} - <i class="text-slate-500">${escapeHtml(p.journal || '')}</i></p>
        </div>
      </div>

      <p class="text-xs text-slate-700 line-clamp-3 leading-relaxed mt-2 bg-slate-50 p-2.5 rounded border border-slate-100">
        ${escapeHtml(p.abstract || "抄録データなし")}
      </p>

      <div class="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
        <div class="flex items-center space-x-3">
          ${p.doi ? `<a href="https://doi.org/${p.doi}" target="_blank" class="text-blue-600 hover:underline flex items-center space-x-1"><i data-lucide="external-link" class="w-3.5 h-3.5"></i><span>DOI</span></a>` : ''}
          ${p.oa_url ? `<a href="${p.oa_url}" target="_blank" class="text-emerald-700 hover:underline flex items-center space-x-1"><i data-lucide="globe" class="w-3.5 h-3.5"></i><span>OAページ</span></a>` : ''}
          ${p.pdf_url ? `<a href="${p.pdf_url}" target="_blank" class="text-red-600 hover:underline flex items-center space-x-1"><i data-lucide="file-text" class="w-3.5 h-3.5"></i><span>PDF</span></a>` : ''}
        </div>
        <div class="text-slate-500 font-medium">
          自動抽出指標: <b class="text-slate-800">${p.effect_type}: ${p.effect_size ? p.effect_size.toFixed(2) : '要調整'}</b> (N=${p.sample_size || 'N/A'})
        </div>
      </div>
    `;
    container.appendChild(card);
  });

  lucide.createIcons();
}

// --- PRISMA Screening & Flow Diagram ---
function setupScreeningControls() {
  document.getElementById("btn-select-all")?.addEventListener("click", () => {
    state.papers.forEach(p => {
      p.is_included_screening = true;
      p.is_included_eligibility = true;
      p.is_included_synthesis = true;
      p.exclusion_reason = null;
    });
    updatePrismaCounts();
    renderScreeningList();
    renderMetaDataMatrix();
  });
}

async function updatePrismaCounts() {
  if (!state.papers || state.papers.length === 0) return;

  const dupCount = state.searchResponse?.prisma_identification?.duplicate_records_removed || 0;
  try {
    const res = await fetch(`/api/prisma/counts?duplicates_removed=${dupCount}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.papers)
    });
    if (res.ok) {
      const counts = await res.json();
      state.prismaCounts = counts;
      
      // Update Flow Diagram
      document.getElementById("flow-ident").innerText = counts.records_identified;
      document.getElementById("flow-dup").innerText = counts.duplicates_removed;
      document.getElementById("flow-screened").innerText = counts.records_screened;
      document.getElementById("flow-excluded-screen").innerText = counts.records_excluded_screening;
      document.getElementById("flow-eligibility").innerText = counts.full_text_assessed;
      document.getElementById("flow-excluded-elig").innerText = counts.full_text_excluded;
      document.getElementById("flow-included").innerText = counts.studies_included_qualitative;
      document.getElementById("flow-included-quant").innerText = counts.studies_included_quantitative;

      document.getElementById("badge-screen-count").innerText = counts.studies_included_qualitative;
      document.getElementById("badge-screen-count").classList.remove("hidden");
    }
  } catch (err) {
    console.error("Prisma count error:", err);
  }
}

function renderScreeningList() {
  const container = document.getElementById("screening-papers-list");
  if (!container) return;
  container.innerHTML = "";

  state.papers.forEach((p, idx) => {
    const item = document.createElement("div");
    const isIncluded = p.is_included_screening && p.is_included_eligibility;
    item.className = `p-4 rounded-lg border transition ${isIncluded ? 'bg-white border-slate-200' : 'bg-slate-100 border-slate-300 opacity-70'}`;
    
    item.innerHTML = `
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-start space-x-3 flex-1">
          <input type="checkbox" id="chk-include-${idx}" class="mt-1 w-4 h-4 text-blue-600 rounded cursor-pointer" ${isIncluded ? 'checked' : ''} />
          <div>
            <div class="text-sm font-bold text-slate-900">${idx + 1}. ${escapeHtml(p.title)}</div>
            <div class="text-xs text-slate-500">${escapeHtml(p.journal || '')} (${p.year || ''}) | 著者: ${escapeHtml(p.authors.slice(0, 2).join(", "))}</div>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <label class="text-xs text-slate-500 whitespace-nowrap">除外理由:</label>
          <select id="sel-reason-${idx}" class="text-xs p-1.5 border border-slate-300 rounded bg-white" ${isIncluded ? 'disabled' : ''}>
            <option value="" ${!p.exclusion_reason ? 'selected' : ''}>-- 理由を選択 --</option>
            <option value="対象集団の不一致 (Wrong population)" ${p.exclusion_reason === '対象集団の不一致 (Wrong population)' ? 'selected' : ''}>対象集団の不一致</option>
            <option value="介入または対照群の欠如 (No control group)" ${p.exclusion_reason === '介入または対照群の欠如 (No control group)' ? 'selected' : ''}>介入・対照群の欠如</option>
            <option value="非原著論文・総説 (Review/Non-original)" ${p.exclusion_reason === '非原著論文・総説 (Review/Non-original)' ? 'selected' : ''}>非原著論文・総説</option>
            <option value="統計数値データの不足 (Insufficient data)" ${p.exclusion_reason === '統計数値データの不足 (Insufficient data)' ? 'selected' : ''}>統計数値データの不足</option>
          </select>
        </div>
      </div>
    `;

    const chk = item.querySelector(`#chk-include-${idx}`);
    const sel = item.querySelector(`#sel-reason-${idx}`);

    chk.addEventListener("change", () => {
      const checked = chk.checked;
      p.is_included_screening = checked;
      p.is_included_eligibility = checked;
      p.is_included_synthesis = checked;
      if (checked) {
        p.exclusion_reason = null;
        sel.disabled = true;
        sel.value = "";
      } else {
        sel.disabled = false;
        if (!sel.value) sel.value = "対象集団の不一致 (Wrong population)";
        p.exclusion_reason = sel.value;
      }
      updatePrismaCounts();
      renderScreeningList();
      renderMetaDataMatrix();
    });

    sel.addEventListener("change", () => {
      p.exclusion_reason = sel.value;
      updatePrismaCounts();
    });

    container.appendChild(item);
  });

  lucide.createIcons();
}

// --- Quantitative Meta-Analysis ---
function setupMetaAnalysis() {
  document.getElementById("btn-run-meta")?.addEventListener("click", () => runMetaAnalysis());
  document.getElementById("btn-download-plot")?.addEventListener("click", () => {
    const plotEl = document.getElementById("plotly-forest-plot");
    if (plotEl) {
      Plotly.downloadImage(plotEl, {
        format: "png",
        width: 1000,
        height: Math.max(500, state.papers.filter(p => p.is_included_synthesis).length * 50 + 200),
        filename: `forest_plot_${state.keyword.replace(/\s+/g, '_')}`
      });
    }
  });
}

function renderMetaDataMatrix() {
  const tbody = document.getElementById("meta-data-matrix-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  const included = state.papers.filter(p => p.is_included_synthesis);
  if (included.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="p-6 text-center text-slate-500">スクリーニングで採択された研究がありません。タブ2で論文を採用してください。</td></tr>`;
    return;
  }

  included.forEach((p, idx) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";
    const authorShort = (p.authors[0] || "Author") + (p.year ? ` (${p.year})` : "");
    tr.innerHTML = `
      <td class="p-2.5 border border-slate-200 text-center">
        <span class="inline-block w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>
      </td>
      <td class="p-2.5 border border-slate-200 font-semibold text-slate-800" title="${escapeHtml(p.title)}">
        ${escapeHtml(authorShort)}
      </td>
      <td class="p-2.5 border border-slate-200 text-slate-600 truncate max-w-[150px]">
        ${escapeHtml(p.journal || 'Open Access')}
      </td>
      <td class="p-2 border border-slate-200">
        <input type="number" step="0.01" class="w-24 p-1 border rounded text-right font-medium" value="${p.effect_size || 1.2}" id="matrix-es-${idx}" />
      </td>
      <td class="p-2 border border-slate-200">
        <input type="number" step="0.01" class="w-24 p-1 border rounded text-right text-slate-600" value="${p.ci_lower || 0.9}" id="matrix-low-${idx}" />
      </td>
      <td class="p-2 border border-slate-200">
        <input type="number" step="0.01" class="w-24 p-1 border rounded text-right text-slate-600" value="${p.ci_upper || 1.6}" id="matrix-high-${idx}" />
      </td>
      <td class="p-2 border border-slate-200">
        <input type="number" step="1" class="w-24 p-1 border rounded text-right text-slate-600" value="${p.sample_size || 200}" id="matrix-n-${idx}" />
      </td>
    `;

    // Bind inputs to paper object
    tr.querySelector(`#matrix-es-${idx}`).addEventListener("input", (e) => {
      p.effect_size = parseFloat(e.target.value) || 0;
    });
    tr.querySelector(`#matrix-low-${idx}`).addEventListener("input", (e) => {
      p.ci_lower = parseFloat(e.target.value) || 0;
    });
    tr.querySelector(`#matrix-high-${idx}`).addEventListener("input", (e) => {
      p.ci_upper = parseFloat(e.target.value) || 0;
    });
    tr.querySelector(`#matrix-n-${idx}`).addEventListener("input", (e) => {
      p.sample_size = parseInt(e.target.value) || 0;
    });

    tbody.appendChild(tr);
  });
}

async function runMetaAnalysis() {
  const included = state.papers.filter(p => p.is_included_synthesis);
  if (included.length === 0) {
    alert("メタ分析に採用する研究を1件以上選択してください。");
    return;
  }

  const metric = document.getElementById("meta-effect-metric").value;

  const studiesData = included.map(p => ({
    study_id: p.id,
    study_label: `${p.authors[0] || 'Unknown'} (${p.year || 'n.d.'})`,
    effect_size: p.effect_size,
    ci_lower: p.ci_lower,
    ci_upper: p.ci_upper,
    sample_size: p.sample_size
  }));

  try {
    const res = await fetch("/api/meta-analysis/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        studies: studiesData,
        effect_metric: metric
      })
    });

    if (!res.ok) {
      const errJson = await res.json();
      throw new Error(errJson.detail || "メタ分析計算エラー");
    }

    const data = await res.json();
    state.metaResult = data.statistics;
    state.forestPlotSpec = data.forest_plot_spec;

    renderMetaSummary(data.statistics);
    renderForestPlot(data.forest_plot_spec);
  } catch (err) {
    alert("メタ分析実行エラー: " + err.message);
  }
}

function renderMetaSummary(stats) {
  document.getElementById("meta-results-summary").classList.remove("hidden");
  document.getElementById("forest-plot-card").classList.remove("hidden");

  // Random-effects
  document.getElementById("res-rand-effect").innerText = `${stats.effect_metric} = ${stats.random_effects.pooled_effect.toFixed(2)}`;
  document.getElementById("res-rand-ci").innerText = `[${stats.random_effects.ci_lower.toFixed(2)}, ${stats.random_effects.ci_upper.toFixed(2)}]`;
  document.getElementById("res-rand-z").innerText = stats.random_effects.z_value.toFixed(2);
  document.getElementById("res-rand-p").innerText = stats.random_effects.p_value < 0.0001 ? "< 0.0001" : stats.random_effects.p_value.toFixed(4);

  // Fixed-effect
  document.getElementById("res-fix-effect").innerText = `${stats.effect_metric} = ${stats.fixed_effect.pooled_effect.toFixed(2)}`;
  document.getElementById("res-fix-ci").innerText = `[${stats.fixed_effect.ci_lower.toFixed(2)}, ${stats.fixed_effect.ci_upper.toFixed(2)}]`;
  document.getElementById("res-fix-z").innerText = stats.fixed_effect.z_value.toFixed(2);
  document.getElementById("res-fix-p").innerText = stats.fixed_effect.p_value < 0.0001 ? "< 0.0001" : stats.fixed_effect.p_value.toFixed(4);

  // Heterogeneity
  document.getElementById("res-i2").innerText = `I² = ${stats.heterogeneity.i_squared.toFixed(1)}%`;
  document.getElementById("res-q").innerText = `${stats.heterogeneity.q_value.toFixed(2)} (df=${stats.heterogeneity.df})`;
  document.getElementById("res-qp").innerText = stats.heterogeneity.p_value < 0.0001 ? "< 0.0001" : stats.heterogeneity.p_value.toFixed(4);
  document.getElementById("res-i2-interp").innerText = stats.heterogeneity.interpretation;
}

function renderForestPlot(spec) {
  const plotDiv = document.getElementById("plotly-forest-plot");
  Plotly.newPlot(plotDiv, spec.data, spec.layout, {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  });
}

// --- Qualitative Evidence Synthesis ---
function setupSynthesis() {
  document.getElementById("btn-generate-synthesis")?.addEventListener("click", () => generateSynthesis());
  document.getElementById("btn-copy-synthesis")?.addEventListener("click", () => {
    const rawMd = state.currentReportMarkdown || "";
    if (!rawMd) {
      alert("コピーするレポートがありません。");
      return;
    }
    navigator.clipboard.writeText(rawMd).then(() => {
      alert("PRISMAレポートのMarkdownをクリップボードにコピーしました。");
    });
  });
}

async function generateSynthesis() {
  const included = state.papers.filter(p => p.is_included_synthesis);
  if (included.length === 0) {
    alert("メタ分析に採用する研究を1件以上選択してください。");
    return;
  }

  const loadingEl = document.getElementById("synthesis-loading");
  const reportContainer = document.getElementById("synthesis-report-container");

  loadingEl.classList.remove("hidden");
  reportContainer.innerHTML = "";

  try {
    const res = await fetch("/api/meta-analysis/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        keyword: state.keyword,
        papers: included,
        meta_result: state.metaResult,
        gemini_api_key: state.geminiApiKey || null
      })
    });

    if (!res.ok) throw new Error("レポート生成エラー");
    const data = await res.json();
    state.currentReportMarkdown = data.report_markdown;
    reportContainer.innerHTML = marked.parse(data.report_markdown);
  } catch (err) {
    alert("エラー: " + err.message);
  } finally {
    loadingEl.classList.add("hidden");
  }
}

// --- Exports ---
function setupExports() {
  document.getElementById("btn-export-csv")?.addEventListener("click", async () => {
    const included = state.papers.filter(p => p.is_included_synthesis);
    if (included.length === 0) return alert("対象研究がありません。");

    const res = await fetch("/api/export/csv", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(included)
    });
    const blob = await res.blob();
    downloadBlob(blob, `meta_analysis_papers_${state.keyword || 'export'}.csv`);
  });

  document.getElementById("btn-export-bibtex")?.addEventListener("click", async () => {
    const included = state.papers.filter(p => p.is_included_synthesis);
    if (included.length === 0) return alert("対象研究がありません。");

    const res = await fetch("/api/export/bibtex", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(included)
    });
    const blob = await res.blob();
    downloadBlob(blob, `open_journal_references_${state.keyword || 'export'}.bib`);
  });

  document.getElementById("btn-export-prisma-txt")?.addEventListener("click", () => {
    const c = state.prismaCounts;
    const txt = `PRISMA 2020 Flow Diagram Summary for Keyword: "${state.keyword}"
============================================================
1. Identification:
   - Records identified from databases (OpenAlex & Europe PMC): ${c.records_identified}
   - Duplicate records removed: ${c.duplicates_removed}

2. Screening:
   - Records screened: ${c.records_screened}
   - Records excluded: ${c.records_excluded_screening}

3. Eligibility:
   - Full-text articles assessed for eligibility: ${c.full_text_assessed}
   - Full-text articles excluded: ${c.full_text_excluded}

4. Included:
   - Studies included in qualitative synthesis: ${c.studies_included_qualitative}
   - Studies included in quantitative meta-analysis (Forest plot): ${c.studies_included_quantitative}

Exclusion Reasons breakdown:
${Object.entries(c.exclusion_reasons || {}).map(([r, n]) => ` - ${r}: ${n} studies`).join("\n") || " None recorded"}
`;
    const blob = new Blob([txt], { type: "text/plain;charset=utf-8" });
    downloadBlob(blob, `prisma_2020_flow_summary.txt`);
  });
}

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// --- Settings Modal ---
function setupSettingsModal() {
  const modal = document.getElementById("settings-modal");
  const btnOpen = document.getElementById("btn-open-settings");
  const btnClose = document.getElementById("btn-close-settings");
  const btnSave = document.getElementById("btn-save-settings");
  const inputKey = document.getElementById("input-gemini-key");

  if (state.geminiApiKey) {
    inputKey.value = state.geminiApiKey;
  }

  btnOpen.addEventListener("click", () => {
    modal.classList.remove("hidden");
    lucide.createIcons();
  });
  btnClose.addEventListener("click", () => modal.classList.add("hidden"));
  btnSave.addEventListener("click", () => {
    const key = inputKey.value.trim();
    state.geminiApiKey = key;
    localStorage.setItem("gemini_api_key", key);
    modal.classList.add("hidden");
    alert("Gemini APIキーを保存しました。");
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  }[tag] || tag));
}
