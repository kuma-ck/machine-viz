/**
 * Machine Viz - フロントエンドJavaScript
 */

// グローバル状態
const state = {
    searchResults: [],
    selectedMachines: [],
    timeseriesData: null,
    histogramData: null,
    currentView: null, // 'timeseries' or 'histogram'
    // ページネーション
    currentPage: 1,
    itemsPerPage: 20,
};

// Chart.jsのデフォルト設定（ライトモード）
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = 'rgba(0, 0, 0, 0.1)';

// グラフカラーパレット
const CHART_COLORS = [
    'rgba(99, 102, 241, 1)',
    'rgba(236, 72, 153, 1)',
    'rgba(16, 185, 129, 1)',
    'rgba(245, 158, 11, 1)',
    'rgba(139, 92, 246, 1)',
];

const CHART_BG_COLORS = [
    'rgba(99, 102, 241, 0.2)',
    'rgba(236, 72, 153, 0.2)',
    'rgba(16, 185, 129, 0.2)',
    'rgba(245, 158, 11, 0.2)',
    'rgba(139, 92, 246, 0.2)',
];

// ========================================
// API関数
// ========================================
async function fetchAPI(endpoint, options = {}) {
    const response = await fetch(`/api${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
}

async function getSeries() {
    return fetchAPI('/series');
}

async function getModels(series) {
    return fetchAPI(`/models/${encodeURIComponent(series)}`);
}

async function getMachines(model) {
    return fetchAPI(`/machines/${encodeURIComponent(model)}`);
}

async function getCategories() {
    return fetchAPI('/categories');
}

async function getCharacteristics(category) {
    return fetchAPI(`/characteristics/${encodeURIComponent(category)}`);
}

async function getAggregations() {
    return fetchAPI('/aggregations');
}

async function getMonths() {
    return fetchAPI('/months');
}

async function searchMachines(params) {
    return fetchAPI('/search', {
        method: 'POST',
        body: JSON.stringify(params),
    });
}

async function sampleMachines(machineIds, sampleSize) {
    return fetchAPI('/sample', {
        method: 'POST',
        body: JSON.stringify({ machine_ids: machineIds, sample_size: sampleSize }),
    });
}

async function getTimeseries(params) {
    return fetchAPI('/timeseries', {
        method: 'POST',
        body: JSON.stringify(params),
    });
}

async function getHistogram(params) {
    return fetchAPI('/histogram', {
        method: 'POST',
        body: JSON.stringify(params),
    });
}

// ========================================
// ユーティリティ
// ========================================
function populateSelect(selectId, options, placeholder = '選択してください') {
    const select = document.getElementById(selectId);
    if (!select) return;

    const currentValue = select.value;
    select.innerHTML = `<option value="">${placeholder}</option>`;
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = opt;
        select.appendChild(option);
    });

    if (options.includes(currentValue)) {
        select.value = currentValue;
    }
}

function showElement(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = '';
}

function hideElement(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}

// ========================================
// 機番検索ページ
// ========================================
async function initSearchPage() {
    const searchForm = document.getElementById('searchForm');
    const seriesSelect = document.getElementById('series');
    const modelList = document.getElementById('modelList');
    const modelHint = document.getElementById('modelHint');
    const mfgMonthFrom = document.getElementById('manufacture_month_from');
    const mfgMonthTo = document.getElementById('manufacture_month_to');
    const opMonthFrom = document.getElementById('operation_start_month_from');
    const opMonthTo = document.getElementById('operation_start_month_to');
    const clearBtn = document.getElementById('clearBtn');
    const sampleBtn = document.getElementById('sampleBtn');
    const selectAllCheckbox = document.getElementById('selectAll');
    const toTimeseriesBtn = document.getElementById('toTimeseriesBtn');
    const toHistogramBtn = document.getElementById('toHistogramBtn');
    const copySelectedBtn = document.getElementById('copySelectedBtn');
    const searchBtn = document.getElementById('searchBtn');

    // 初期データ読み込み
    const [series, months] = await Promise.all([
        getSeries(),
        getMonths(),
    ]);

    populateSelect('series', series, 'すべて');
    populateSelect('manufacture_month_from', months, '開始月');
    populateSelect('manufacture_month_to', months, '終了月');
    populateSelect('operation_start_month_from', months, '開始月');
    populateSelect('operation_start_month_to', months, '終了月');

    // 機種番号チェックボックスを生成
    function renderModelCheckboxes(models) {
        modelList.innerHTML = '';
        if (models.length === 0) {
            modelHint.textContent = '(シリーズを選択してください)';
            return;
        }
        modelHint.textContent = `(${models.length}件から選択)`;

        models.forEach(model => {
            const item = document.createElement('label');
            item.className = 'multi-select-item';
            item.innerHTML = `<input type="checkbox" value="${model}"> ${model}`;

            const checkbox = item.querySelector('input');
            checkbox.addEventListener('change', () => {
                item.classList.toggle('checked', checkbox.checked);
            });

            modelList.appendChild(item);
        });
    }

    // シリーズ変更時
    seriesSelect.addEventListener('change', async () => {
        if (seriesSelect.value) {
            const models = await getModels(seriesSelect.value);
            renderModelCheckboxes(models);
        } else {
            renderModelCheckboxes([]);
        }
    });

    // 選択された機種番号を取得
    function getSelectedModels() {
        const checkboxes = modelList.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    // ローディング表示切り替え
    function setLoading(loading) {
        const btnText = searchBtn.querySelector('.btn-text');
        const btnIcon = searchBtn.querySelector('.btn-icon');
        const btnLoading = searchBtn.querySelector('.btn-loading');

        if (loading) {
            btnText.style.display = 'none';
            btnIcon.style.display = 'none';
            btnLoading.style.display = 'inline-flex';
            searchBtn.disabled = true;
        } else {
            btnText.style.display = '';
            btnIcon.style.display = '';
            btnLoading.style.display = 'none';
            searchBtn.disabled = false;
        }
    }

    // 選択件数の更新とボタン状態管理
    function updateSelectionState() {
        const selected = getSelectedMachineIds();
        const badge = document.getElementById('selectedCountBadge');

        if (selected.length > 0) {
            badge.textContent = `${selected.length}件選択中`;
            badge.style.display = '';
            copySelectedBtn.disabled = false;
            toTimeseriesBtn.disabled = false;
            toHistogramBtn.disabled = false;
        } else {
            badge.style.display = 'none';
            copySelectedBtn.disabled = true;
            toTimeseriesBtn.disabled = true;
            toHistogramBtn.disabled = true;
        }
    }

    // 検索フォーム送信
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const selectedModels = getSelectedModels();

            const params = {
                series: seriesSelect.value || null,
                models: selectedModels.length > 0 ? selectedModels : null,
                manufacture_month_from: mfgMonthFrom.value || null,
                manufacture_month_to: mfgMonthTo.value || null,
                operation_start_month_from: opMonthFrom.value || null,
                operation_start_month_to: opMonthTo.value || null,
            };

            state.searchResults = await searchMachines(params);
            state.selectedMachines = [];
            renderSearchResults(state.searchResults);

            // 結果件数バッジ更新
            document.getElementById('resultCountBadge').textContent = `${state.searchResults.length}件`;
            updateSelectionState();
        } catch (error) {
            alert('検索中にエラーが発生しました。再度お試しください。');
            console.error(error);
        } finally {
            setLoading(false);
        }
    });

    // クリアボタン
    clearBtn.addEventListener('click', () => {
        searchForm.reset();
        renderModelCheckboxes([]); // 機種番号をリセット
        hideElement('samplingCard');
        hideElement('resultsCard');
        state.searchResults = [];
        state.selectedMachines = [];
    });

    // サンプリングボタン
    sampleBtn.addEventListener('click', async () => {
        const sampleSize = parseInt(document.getElementById('sampleSize').value);
        const machineIds = state.searchResults.map(m => m.machine_id);

        if (sampleSize > 0 && machineIds.length > 0) {
            const sampled = await sampleMachines(machineIds, sampleSize);
            const filtered = state.searchResults.filter(m => sampled.includes(m.machine_id));
            renderSearchResults(filtered, true);
            document.getElementById('resultCountBadge').textContent = `${filtered.length}件`;
        }
    });

    // 全選択チェックボックス
    selectAllCheckbox.addEventListener('change', () => {
        const checkboxes = document.querySelectorAll('#resultsBody input[type="checkbox"]');
        checkboxes.forEach(cb => {
            cb.checked = selectAllCheckbox.checked;
        });
        updateSelectedMachines();
        updateSelectionState();
    });

    // 時系列表示への遷移
    toTimeseriesBtn.addEventListener('click', () => {
        const selected = getSelectedMachineIds();
        if (selected.length === 0) {
            alert('機番を選択してください');
            return;
        }
        if (selected.length > 5) {
            alert('最大5台まで選択できます');
            return;
        }
        sessionStorage.setItem('selectedMachines', JSON.stringify(selected));
        window.location.href = '/timeseries';
    });

    // 断面データ表示への遷移
    toHistogramBtn.addEventListener('click', () => {
        const selected = getSelectedMachineIds();
        sessionStorage.setItem('selectedMachines', JSON.stringify(selected));
        window.location.href = '/histogram';
    });

    // 選択した機番をコピー
    copySelectedBtn.addEventListener('click', () => {
        const selected = getSelectedMachineIds();
        if (selected.length === 0) {
            alert('機番を選択してください');
            return;
        }
        const text = selected.join(', ');
        navigator.clipboard.writeText(text).then(() => {
            alert(`${selected.length}件の機番をコピーしました\n${text}`);
        }).catch(err => {
            // クリップボードAPIが使えない場合のフォールバック
            prompt('以下の機番をコピーしてください:', text);
        });
    });
}

function renderSearchResults(results, isSampled = false, resetPage = true) {
    if (resetPage) {
        state.currentPage = 1;
    }

    const tbody = document.getElementById('resultsBody');
    tbody.innerHTML = '';

    // ページネーション計算
    const totalItems = results.length;
    const totalPages = Math.ceil(totalItems / state.itemsPerPage);
    const startIndex = (state.currentPage - 1) * state.itemsPerPage;
    const endIndex = Math.min(startIndex + state.itemsPerPage, totalItems);
    const pageResults = results.slice(startIndex, endIndex);

    pageResults.forEach(machine => {
        const tr = document.createElement('tr');
        const isChecked = state.selectedMachines.includes(machine.machine_id) ? 'checked' : '';
        tr.innerHTML = `
            <td><input type="checkbox" data-machine-id="${machine.machine_id}" ${isChecked}></td>
            <td>${machine.machine_id}</td>
            <td>${machine.series}</td>
            <td>${machine.model}</td>
            <td>${machine.manufacture_month}</td>
            <td>${machine.operation_start_month}</td>
        `;
        tbody.appendChild(tr);
    });

    // チェックボックスの変更を監視
    tbody.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.addEventListener('change', updateSelectedMachines);
    });

    // UIの表示更新
    showElement('resultsCard');
    showElement('samplingCard');
    document.getElementById('totalCount').textContent = results.length;
    document.getElementById('selectAll').checked = false;

    // ページネーションUIを更新
    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    let paginationContainer = document.getElementById('paginationContainer');

    if (!paginationContainer) {
        // ページネーションコンテナを作成
        paginationContainer = document.createElement('div');
        paginationContainer.id = 'paginationContainer';
        paginationContainer.className = 'pagination-container';
        const tableContainer = document.querySelector('.table-container');
        tableContainer.parentNode.insertBefore(paginationContainer, tableContainer.nextSibling);
    }

    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }

    let paginationHTML = '<div class="pagination">';

    // 前へボタン
    paginationHTML += `<button class="pagination-btn" ${state.currentPage === 1 ? 'disabled' : ''} data-page="${state.currentPage - 1}">← 前へ</button>`;

    // ページ番号
    const maxVisiblePages = 7;
    let startPage = Math.max(1, state.currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    if (startPage > 1) {
        paginationHTML += `<button class="pagination-btn" data-page="1">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="pagination-ellipsis">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === state.currentPage ? 'active' : '';
        paginationHTML += `<button class="pagination-btn ${activeClass}" data-page="${i}">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="pagination-ellipsis">...</span>`;
        }
        paginationHTML += `<button class="pagination-btn" data-page="${totalPages}">${totalPages}</button>`;
    }

    // 次へボタン
    paginationHTML += `<button class="pagination-btn" ${state.currentPage === totalPages ? 'disabled' : ''} data-page="${state.currentPage + 1}">次へ →</button>`;

    paginationHTML += '</div>';
    // 件数選択 + ページ情報
    paginationHTML += `<div class="pagination-info">
        <label>表示件数: 
            <select id="itemsPerPageSelect" class="form-select-sm">
                <option value="20" ${state.itemsPerPage === 20 ? 'selected' : ''}>20件</option>
                <option value="50" ${state.itemsPerPage === 50 ? 'selected' : ''}>50件</option>
                <option value="100" ${state.itemsPerPage === 100 ? 'selected' : ''}>100件</option>
            </select>
        </label>
        <span>${state.currentPage} / ${totalPages} ページ（全 ${state.searchResults.length} 件）</span>
    </div>`;

    paginationContainer.innerHTML = paginationHTML;

    // ページ切り替えイベント
    paginationContainer.querySelectorAll('.pagination-btn:not([disabled])').forEach(btn => {
        btn.addEventListener('click', () => {
            state.currentPage = parseInt(btn.dataset.page);
            renderSearchResults(state.searchResults, false, false);
        });
    });

    // 件数選択イベント
    const itemsPerPageSelect = document.getElementById('itemsPerPageSelect');
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', () => {
            state.itemsPerPage = parseInt(itemsPerPageSelect.value);
            state.currentPage = 1; // ページを1に戻す
            renderSearchResults(state.searchResults, false, true);
        });
    }
}

function getSelectedMachineIds() {
    const checkboxes = document.querySelectorAll('#resultsBody input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.dataset.machineId);
}

function updateSelectedMachines() {
    const checkboxes = document.querySelectorAll('#resultsBody input[type="checkbox"]:checked');
    state.selectedMachines = Array.from(checkboxes).map(cb => cb.dataset.machineId);

    // 選択件数バッジ更新とボタン有効化
    const badge = document.getElementById('selectedCountBadge');
    const copyBtn = document.getElementById('copySelectedBtn');
    const tsBtn = document.getElementById('toTimeseriesBtn');
    const histBtn = document.getElementById('toHistogramBtn');

    if (state.selectedMachines.length > 0) {
        if (badge) {
            badge.textContent = `${state.selectedMachines.length}件選択中`;
            badge.style.display = '';
        }
        if (copyBtn) copyBtn.disabled = false;
        if (tsBtn) tsBtn.disabled = false;
        if (histBtn) histBtn.disabled = false;
    } else {
        if (badge) badge.style.display = 'none';
        if (copyBtn) copyBtn.disabled = true;
        if (tsBtn) tsBtn.disabled = true;
        if (histBtn) histBtn.disabled = true;
    }
}

// ========================================
// 時系列表示ページ
// ========================================
let timeseriesChart = null;

// テキストエリアから機番IDをパース
function parseMachineIds(text) {
    if (!text || !text.trim()) return [];
    // カンマ、改行、スペースで分割
    return text.split(/[,\n\s]+/)
        .map(s => s.trim())
        .filter(s => s.length > 0);
}

async function initTimeseriesPage() {
    const form = document.getElementById('timeseriesForm');
    const machinesTextarea = document.getElementById('ts-machines');
    const categorySelect = document.getElementById('ts-category');
    const characteristicSelect = document.getElementById('ts-characteristic');
    const aggregationSelect = document.getElementById('ts-aggregation');
    const toTableBtn = document.getElementById('toTableBtn');

    // 初期データ読み込み
    const [categories, aggregations] = await Promise.all([
        getCategories(),
        getAggregations(),
    ]);

    populateSelect('ts-category', categories);
    populateSelect('ts-aggregation', aggregations);

    // カテゴリー変更時
    categorySelect.addEventListener('change', async () => {
        if (categorySelect.value) {
            const chars = await getCharacteristics(categorySelect.value);
            populateSelect('ts-characteristic', chars);
        } else {
            populateSelect('ts-characteristic', []);
        }
    });

    // 検索ページから来た場合の初期設定
    const savedMachines = sessionStorage.getItem('selectedMachines');
    if (savedMachines) {
        const machines = JSON.parse(savedMachines);
        machinesTextarea.value = machines.join(', ');
        sessionStorage.removeItem('selectedMachines');
    }

    // フォーム送信
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const machineIds = parseMachineIds(machinesTextarea.value);
        if (machineIds.length === 0) {
            alert('機番を入力してください');
            return;
        }
        if (machineIds.length > 5) {
            alert('最大5台まで入力できます');
            return;
        }

        const params = {
            machine_ids: machineIds,
            category: categorySelect.value,
            characteristic_id: characteristicSelect.value,
            aggregation: aggregationSelect.value,
        };

        if (!params.category || !params.characteristic_id || !params.aggregation) {
            alert('すべての条件を選択してください');
            return;
        }

        state.timeseriesData = await getTimeseries(params);
        state.currentView = 'timeseries';
        renderTimeseriesChart(state.timeseriesData);
        showElement('chartCard');
    });

    // 表形式表示への遷移
    toTableBtn.addEventListener('click', () => {
        if (state.timeseriesData) {
            sessionStorage.setItem('tableData', JSON.stringify({
                type: 'timeseries',
                data: state.timeseriesData,
            }));
            window.location.href = '/table';
        }
    });
}

function renderMachineCheckboxes(containerId, machines, maxSelect = null) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (machines.length === 0) {
        container.innerHTML = '<p class="placeholder-text">機種番号を選択してください</p>';
        return;
    }

    container.innerHTML = machines.map(m => `
        <div class="checkbox-item">
            <input type="checkbox" id="machine-${m}" value="${m}">
            <label for="machine-${m}">${m}</label>
        </div>
    `).join('');

    // 最大選択数の制限
    if (maxSelect) {
        container.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', () => {
                const checked = container.querySelectorAll('input:checked').length;
                if (checked > maxSelect) {
                    cb.checked = false;
                    alert(`最大${maxSelect}台まで選択できます`);
                }
            });
        });
    }
}

function getCheckedMachines(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    const checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function renderTimeseriesChart(data) {
    const ctx = document.getElementById('timeseriesChart');
    if (!ctx) return;

    if (timeseriesChart) {
        timeseriesChart.destroy();
    }

    const datasets = data.datasets.map((ds, i) => ({
        label: `機番: ${ds.machine_id}`,
        data: ds.data,
        borderColor: CHART_COLORS[i % CHART_COLORS.length],
        backgroundColor: CHART_BG_COLORS[i % CHART_BG_COLORS.length],
        borderWidth: 2,
        tension: 0.3,
        fill: false,
    }));

    timeseriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false,
                },
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                    },
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                    },
                },
            },
        },
    });
}

// ========================================
// 断面データ表示ページ
// ========================================
let histogramChart = null;

async function initHistogramPage() {
    const form = document.getElementById('histogramForm');
    const seriesSelect = document.getElementById('hist-series');
    const modelSelect = document.getElementById('hist-model');
    const monthSelect = document.getElementById('hist-month');
    const categorySelect = document.getElementById('hist-category');
    const characteristicSelect = document.getElementById('hist-characteristic');
    const aggregationSelect = document.getElementById('hist-aggregation');
    const machinesTextarea = document.getElementById('hist-machines');
    const toTableBtn = document.getElementById('histToTableBtn');

    // 初期データ読み込み
    const [series, categories, aggregations, months] = await Promise.all([
        getSeries(),
        getCategories(),
        getAggregations(),
        getMonths(),
    ]);

    populateSelect('hist-series', series);
    populateSelect('hist-category', categories);
    populateSelect('hist-aggregation', aggregations);
    populateSelect('hist-month', months);

    // シリーズ変更時
    seriesSelect.addEventListener('change', async () => {
        if (seriesSelect.value) {
            const models = await getModels(seriesSelect.value);
            populateSelect('hist-model', models);
        } else {
            populateSelect('hist-model', []);
        }
    });

    // カテゴリー変更時
    categorySelect.addEventListener('change', async () => {
        if (categorySelect.value) {
            const chars = await getCharacteristics(categorySelect.value);
            populateSelect('hist-characteristic', chars);
        } else {
            populateSelect('hist-characteristic', []);
        }
    });

    // 検索ページから来た場合
    const savedMachines = sessionStorage.getItem('selectedMachines');
    if (savedMachines) {
        const machines = JSON.parse(savedMachines);
        machinesTextarea.value = machines.join(', ');
        sessionStorage.removeItem('selectedMachines');
    }

    // フォーム送信
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const selectedMachines = parseMachineIds(machinesTextarea.value);

        const params = {
            model: modelSelect.value,
            category: categorySelect.value,
            characteristic_id: characteristicSelect.value,
            aggregation: aggregationSelect.value,
            target_month: monthSelect.value,
            selected_machine_ids: selectedMachines.length > 0 ? selectedMachines : null,
        };

        if (!params.model || !params.category || !params.characteristic_id ||
            !params.aggregation || !params.target_month) {
            alert('必須条件をすべて選択してください');
            return;
        }

        state.histogramData = await getHistogram(params);
        state.currentView = 'histogram';
        renderHistogramChart(state.histogramData);
        showElement('histogramCard');
    });

    // 表形式表示への遷移
    toTableBtn.addEventListener('click', () => {
        if (state.histogramData) {
            sessionStorage.setItem('tableData', JSON.stringify({
                type: 'histogram',
                data: state.histogramData,
            }));
            window.location.href = '/table';
        }
    });
}

function renderHistogramChart(data) {
    const ctx = document.getElementById('histogramChart');
    if (!ctx) return;

    if (histogramChart) {
        histogramChart.destroy();
    }

    // ビンのラベル作成
    const labels = [];
    for (let i = 0; i < data.bins.length - 1; i++) {
        labels.push(`${data.bins[i]}-${data.bins[i + 1]}`);
    }

    // 度数を相対頻度（パーセンテージ）に変換
    const toRelativeFrequency = (counts) => {
        const total = counts.reduce((sum, c) => sum + c, 0);
        if (total === 0) return counts.map(() => 0);
        return counts.map(c => (c / total) * 100);
    };

    const datasets = [];

    if (data.selected_group && data.other_group) {
        datasets.push({
            label: `${data.selected_group.label}（相対頻度）`,
            data: toRelativeFrequency(data.selected_group.counts),
            backgroundColor: CHART_COLORS[0],
            borderColor: CHART_COLORS[0],
            borderWidth: 1,
        });
        datasets.push({
            label: `${data.other_group.label}（相対頻度）`,
            data: toRelativeFrequency(data.other_group.counts),
            backgroundColor: CHART_COLORS[1],
            borderColor: CHART_COLORS[1],
            borderWidth: 1,
        });
    } else if (data.all_group) {
        datasets.push({
            label: `${data.all_group.label}（相対頻度）`,
            data: toRelativeFrequency(data.all_group.counts),
            backgroundColor: CHART_COLORS[0],
            borderColor: CHART_COLORS[0],
            borderWidth: 1,
        });
    }

    histogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const value = context.raw.toFixed(1);
                            return `${context.dataset.label}: ${value}%`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '値の範囲',
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: '相対頻度（%）',
                    },
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                    ticks: {
                        callback: (value) => `${value}%`,
                    },
                },
            },
        },
    });
}

// ========================================
// 表形式表示ページ
// ========================================
let tablePageState = {
    data: null,
    currentPage: 1,
    itemsPerPage: 50,
};

function initTablePage() {
    const tableDataStr = sessionStorage.getItem('tableData');
    const infoDiv = document.getElementById('dataInfo');
    const tableCard = document.getElementById('tableCard');
    const tableTitle = document.getElementById('tableTitle');
    const tableHead = document.getElementById('tableHead');
    const exportBtn = document.getElementById('exportCsvBtn');

    if (!tableDataStr) {
        return;
    }

    tablePageState.data = JSON.parse(tableDataStr);
    const tableData = tablePageState.data;

    if (tableData.type === 'timeseries') {
        infoDiv.innerHTML = '<p>時系列データを表示しています</p>';
        tableTitle.textContent = '時系列データ';

        // ヘッダー
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>月</th>' +
            tableData.data.datasets.map(ds => `<th>${ds.machine_id}</th>`).join('');
        tableHead.appendChild(headerRow);

    } else if (tableData.type === 'histogram') {
        infoDiv.innerHTML = '<p>断面データを表示しています</p>';
        tableTitle.textContent = '断面データ（機番別）';

        // ヘッダー
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>機番</th><th>値</th>';
        tableHead.appendChild(headerRow);
    }

    // テーブル行をレンダリング
    renderTableRows();

    showElement('tableCard');

    // CSV出力
    exportBtn.addEventListener('click', () => {
        exportTableToCSV(tableData);
    });
}

function renderTableRows() {
    const tableBody = document.getElementById('tableBody');
    const tableData = tablePageState.data;

    if (!tableData) return;

    tableBody.innerHTML = '';

    let allRows = [];

    if (tableData.type === 'timeseries') {
        // 時系列データの行を作成
        tableData.data.labels.forEach((label, i) => {
            allRows.push({
                cells: [label, ...tableData.data.datasets.map(ds => ds.data[i])]
            });
        });
    } else if (tableData.type === 'histogram' && tableData.data.raw_data) {
        // 断面データの行を作成
        tableData.data.raw_data.forEach(item => {
            allRows.push({
                cells: [item.machine_id, item.value]
            });
        });
    }

    // ページネーション計算
    const totalItems = allRows.length;
    const totalPages = Math.ceil(totalItems / tablePageState.itemsPerPage);
    const startIndex = (tablePageState.currentPage - 1) * tablePageState.itemsPerPage;
    const endIndex = Math.min(startIndex + tablePageState.itemsPerPage, totalItems);
    const pageRows = allRows.slice(startIndex, endIndex);

    // データ行を描画
    pageRows.forEach(rowData => {
        const row = document.createElement('tr');
        row.innerHTML = rowData.cells.map(cell => `<td>${cell}</td>`).join('');
        tableBody.appendChild(row);
    });

    // ページネーションUIを更新
    renderTablePagination(totalPages, totalItems);
}

function renderTablePagination(totalPages, totalItems) {
    let paginationContainer = document.getElementById('tablePaginationContainer');

    if (!paginationContainer) {
        paginationContainer = document.createElement('div');
        paginationContainer.id = 'tablePaginationContainer';
        paginationContainer.className = 'pagination-container';
        const tableContainer = document.querySelector('#tableCard .table-container');
        if (tableContainer) {
            tableContainer.parentNode.insertBefore(paginationContainer, tableContainer.nextSibling);
        }
    }

    if (totalPages <= 1) {
        paginationContainer.innerHTML = `<div class="pagination-info">全 ${totalItems} 件</div>`;
        return;
    }

    let paginationHTML = '<div class="pagination">';

    // 前へボタン
    paginationHTML += `<button class="pagination-btn" ${tablePageState.currentPage === 1 ? 'disabled' : ''} data-page="${tablePageState.currentPage - 1}">← 前へ</button>`;

    // ページ番号
    const maxVisiblePages = 7;
    let startPage = Math.max(1, tablePageState.currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    if (startPage > 1) {
        paginationHTML += `<button class="pagination-btn" data-page="1">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="pagination-ellipsis">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === tablePageState.currentPage ? 'active' : '';
        paginationHTML += `<button class="pagination-btn ${activeClass}" data-page="${i}">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="pagination-ellipsis">...</span>`;
        }
        paginationHTML += `<button class="pagination-btn" data-page="${totalPages}">${totalPages}</button>`;
    }

    // 次へボタン
    paginationHTML += `<button class="pagination-btn" ${tablePageState.currentPage === totalPages ? 'disabled' : ''} data-page="${tablePageState.currentPage + 1}">次へ →</button>`;

    paginationHTML += '</div>';
    paginationHTML += `<div class="pagination-info">${tablePageState.currentPage} / ${totalPages} ページ（全 ${totalItems} 件）</div>`;

    paginationContainer.innerHTML = paginationHTML;

    // ページ切り替えイベント
    paginationContainer.querySelectorAll('.pagination-btn:not([disabled])').forEach(btn => {
        btn.addEventListener('click', () => {
            tablePageState.currentPage = parseInt(btn.dataset.page);
            renderTableRows();
        });
    });
}

function exportTableToCSV(tableData) {
    let csv = '';

    if (tableData.type === 'timeseries') {
        // ヘッダー
        csv += '月,' + tableData.data.datasets.map(ds => ds.machine_id).join(',') + '\n';
        // データ
        tableData.data.labels.forEach((label, i) => {
            csv += label + ',' + tableData.data.datasets.map(ds => ds.data[i]).join(',') + '\n';
        });
    } else if (tableData.type === 'histogram' && tableData.data.raw_data) {
        csv += '機番,値\n';
        tableData.data.raw_data.forEach(item => {
            csv += `${item.machine_id},${item.value}\n`;
        });
    }

    // ダウンロード
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `machine_viz_${tableData.type}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
}
