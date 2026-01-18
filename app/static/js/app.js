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

// ========================================
// フィルタプリセット管理
// ========================================
const FilterPresetManager = {
    storageKey: 'machine-viz-presets',

    getAll() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.error('Failed to load presets', e);
            return [];
        }
    },

    save(name, page, data) {
        const presets = this.getAll();
        const existing = presets.findIndex(p => p.name === name && p.page === page);
        const preset = {
            name,
            page,
            createdAt: new Date().toISOString(),
            data
        };
        if (existing >= 0) {
            presets[existing] = preset;
        } else {
            presets.push(preset);
        }
        localStorage.setItem(this.storageKey, JSON.stringify(presets));
        return preset;
    },

    delete(name, page) {
        const presets = this.getAll().filter(p => !(p.name === name && p.page === page));
        localStorage.setItem(this.storageKey, JSON.stringify(presets));
    },

    get(name, page) {
        return this.getAll().find(p => p.name === name && p.page === page);
    },

    getByPage(page) {
        return this.getAll().filter(p => p.page === page);
    }
};

// プリセットUIヘルパー
function initPresetUI(page, getCurrentFilters, applyFilters) {
    const presetSelect = document.getElementById('presetSelect');
    const applyBtn = document.getElementById('applyPresetBtn');
    const saveBtn = document.getElementById('savePresetBtn');
    const deleteBtn = document.getElementById('deletePresetBtn');
    const modal = document.getElementById('savePresetModal');
    const presetNameInput = document.getElementById('presetNameInput');
    const confirmSaveBtn = document.getElementById('confirmSaveBtn');
    const cancelSaveBtn = document.getElementById('cancelSaveBtn');

    if (!presetSelect) return; // UIが存在しない場合はスキップ

    // プリセット一覧を更新
    function refreshPresetList() {
        const presets = FilterPresetManager.getByPage(page);
        presetSelect.innerHTML = '<option value="">-- 保存済みプリセット --</option>';
        presets.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.name;
            opt.textContent = p.name;
            presetSelect.appendChild(opt);
        });
    }

    // 適用ボタン
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            const name = presetSelect.value;
            if (!name) return;
            const preset = FilterPresetManager.get(name, page);
            if (preset) {
                applyFilters(preset.data);
            }
        });
    }

    // 保存ボタン → モーダル表示
    if (saveBtn && modal) {
        saveBtn.addEventListener('click', () => {
            modal.style.display = 'flex';
            presetNameInput.value = '';
            presetNameInput.focus();
        });
    }

    // 保存確定
    if (confirmSaveBtn && modal) {
        confirmSaveBtn.addEventListener('click', () => {
            const name = presetNameInput.value.trim();
            if (!name) {
                alert('プリセット名を入力してください');
                return;
            }
            const data = getCurrentFilters();
            FilterPresetManager.save(name, page, data);
            modal.style.display = 'none';
            refreshPresetList();
            presetSelect.value = name;
        });
    }

    // キャンセル
    if (cancelSaveBtn && modal) {
        cancelSaveBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    // 削除ボタン
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const name = presetSelect.value;
            if (!name) return;
            if (confirm(`プリセット「${name}」を削除しますか？`)) {
                FilterPresetManager.delete(name, page);
                refreshPresetList();
            }
        });
    }

    // 初期化
    refreshPresetList();
}

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

    // プリセット機能の初期化
    initPresetUI(
        'search',
        // getCurrentFilters
        () => ({
            series: seriesSelect.value,
            models: Array.from(modelList.querySelectorAll('input:checked')).map(cb => cb.value),
            mfgMonthFrom: mfgMonthFrom.value,
            mfgMonthTo: mfgMonthTo.value,
            opMonthFrom: opMonthFrom.value,
            opMonthTo: opMonthTo.value
        }),
        // applyFilters
        async (data) => {
            if (data.series) {
                seriesSelect.value = data.series;
                const models = await getModels(data.series);
                renderModelCheckboxes(models);
                // 選択状態を復元
                if (data.models && data.models.length > 0) {
                    data.models.forEach(m => {
                        const cb = modelList.querySelector(`input[value="${m}"]`);
                        if (cb) {
                            cb.checked = true;
                            cb.closest('.multi-select-item')?.classList.add('checked');
                        }
                    });
                }
            }
            if (data.mfgMonthFrom) mfgMonthFrom.value = data.mfgMonthFrom;
            if (data.mfgMonthTo) mfgMonthTo.value = data.mfgMonthTo;
            if (data.opMonthFrom) opMonthFrom.value = data.opMonthFrom;
            if (data.opMonthTo) opMonthTo.value = data.opMonthTo;
            // 自動で検索実行
            searchForm.dispatchEvent(new Event('submit'));
        }
    );

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

// ========================================
// EDA型ダッシュボード - 時系列表示 V2
// ========================================
let timeseriesChartV2 = null;
let overviewChartV2 = null;
let timeseriesStateV2 = {
    data: null,
    annotations: [],
    zoomRange: null,
    variables: [],
};

async function initTimeseriesPageV2() {
    const form = document.getElementById('timeseriesForm');
    const machinesTextarea = document.getElementById('ts-machines');
    const variableList = document.getElementById('variableList');
    const addVariableBtn = document.getElementById('addVariableBtn');
    const showAnnotations = document.getElementById('showAnnotations');
    const toTableBtn = document.getElementById('toTableBtn');
    const shareUrlBtn = document.getElementById('shareUrlBtn');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const zoomResetBtn = document.getElementById('zoomResetBtn');

    // 日付範囲要素を取得
    const xAxisTimeMonth = document.getElementById('xAxisTimeMonth');
    const xAxisTimeDay = document.getElementById('xAxisTimeDay');
    const xAxisUsage = document.getElementById('xAxisUsage');
    const dayRangeGroup = document.getElementById('dayRangeGroup');
    const dateFromInput = document.getElementById('ts-date-from');
    const dateToInput = document.getElementById('ts-date-to');

    // 日付入力の初期値設定（本日から30日前まで）
    const today = new Date();
    const monthAgo = new Date(today);
    monthAgo.setDate(today.getDate() - 30);
    if (dateFromInput) dateFromInput.value = monthAgo.toISOString().split('T')[0];
    if (dateToInput) dateToInput.value = today.toISOString().split('T')[0];

    // ラジオボタンのイベントハンドラー
    const handleXAxisChange = () => {
        if (xAxisTimeDay.checked) {
            dayRangeGroup.style.display = 'block';
        } else {
            dayRangeGroup.style.display = 'none';
        }
    };

    if (xAxisTimeMonth) xAxisTimeMonth.addEventListener('change', handleXAxisChange);
    if (xAxisTimeDay) xAxisTimeDay.addEventListener('change', handleXAxisChange);
    if (xAxisUsage) xAxisUsage.addEventListener('change', handleXAxisChange);

    // 初期データ読み込み
    const [categories, aggregations] = await Promise.all([
        getCategories(),
        getAggregations(),
    ]);

    // プリセット機能の初期化
    initPresetUI(
        'timeseries',
        // getCurrentFilters
        () => {
            const variables = Array.from(variableList.querySelectorAll('.variable-item')).map(item => ({
                category: item.querySelector('.var-category')?.value,
                characteristic: item.querySelector('.var-characteristic')?.value
            }));
            return {
                machines: machinesTextarea.value,
                xAxisType: document.querySelector('input[name="xAxisType"]:checked')?.value,
                dateFrom: dateFromInput?.value,
                dateTo: dateToInput?.value,
                showAnnotations: showAnnotations?.checked,
                variables
            };
        },
        // applyFilters
        async (data) => {
            if (data.machines) machinesTextarea.value = data.machines;
            if (data.xAxisType) {
                const radio = document.querySelector(`input[name="xAxisType"][value="${data.xAxisType}"]`);
                if (radio) {
                    radio.checked = true;
                    handleXAxisChange();
                }
            }
            if (data.dateFrom && dateFromInput) dateFromInput.value = data.dateFrom;
            if (data.dateTo && dateToInput) dateToInput.value = data.dateTo;
            if (data.showAnnotations !== undefined && showAnnotations) {
                showAnnotations.checked = data.showAnnotations;
            }
            // 変数を復元
            if (data.variables && data.variables.length > 0) {
                variableList.innerHTML = '';
                for (const v of data.variables) {
                    await addVariable();
                    const items = variableList.querySelectorAll('.variable-item');
                    const lastItem = items[items.length - 1];
                    if (v.category) {
                        const catSel = lastItem.querySelector('.var-category');
                        catSel.value = v.category;
                        const chars = await getCharacteristics(v.category);
                        const charSel = lastItem.querySelector('.var-characteristic');
                        charSel.innerHTML = '<option value="">特性値ID</option>' +
                            chars.map(c => `<option value="${c}">${c}</option>`).join('');
                        if (v.characteristic) charSel.value = v.characteristic;
                    }
                }
            }
            // 自動でグラフ表示
            form.dispatchEvent(new Event('submit'));
        }
    );

    // 変数テンプレート
    let variableCounter = 0;

    async function addVariable() {
        const varIndex = variableList.children.length;
        if (varIndex >= 2) {
            alert('変数は最大2つまで追加できます（左軸・右軸各1つ）');
            return;
        }

        // 1つ目は左軸、2つ目は右軸
        const axisValue = varIndex === 0 ? 'left' : 'right';
        const axisLabel = varIndex === 0 ? '左軸' : '右軸';

        const varId = variableCounter++;
        const item = document.createElement('div');
        item.className = 'variable-item';
        item.dataset.varId = varId;
        item.dataset.axis = axisValue;
        item.innerHTML = `
            <select class="form-select var-category" data-var-id="${varId}">
                <option value="">カテゴリー</option>
                ${categories.map(c => `<option value="${c}">${c}</option>`).join('')}
            </select>
            <select class="form-select var-characteristic" data-var-id="${varId}">
                <option value="">特性値ID</option>
            </select>
            <span class="axis-label" style="color: var(--color-text-muted); font-size: var(--font-size-sm); padding: 0 8px;">${axisLabel}</span>
            <button type="button" class="remove-variable-btn" data-var-id="${varId}">✕</button>
        `;

        variableList.appendChild(item);

        // カテゴリー変更時
        const categorySelect = item.querySelector('.var-category');
        const charSelect = item.querySelector('.var-characteristic');
        categorySelect.addEventListener('change', async () => {
            if (categorySelect.value) {
                const chars = await getCharacteristics(categorySelect.value);
                charSelect.innerHTML = '<option value="">特性値ID</option>' +
                    chars.map(c => `<option value="${c}">${c}</option>`).join('');
            } else {
                charSelect.innerHTML = '<option value="">特性値ID</option>';
            }
        });

        // 削除ボタン
        const removeBtn = item.querySelector('.remove-variable-btn');
        removeBtn.addEventListener('click', () => {
            item.remove();
        });
    }

    // 初期変数を1つ追加
    await addVariable();

    // 変数追加ボタン
    addVariableBtn.addEventListener('click', addVariable);

    // 検索ページから来た場合の初期設定
    const savedMachines = sessionStorage.getItem('selectedMachines');
    if (savedMachines) {
        const machines = JSON.parse(savedMachines);
        machinesTextarea.value = machines.join(', ');
        sessionStorage.removeItem('selectedMachines');
    }

    // URLパラメータから状態を復元
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('machines') || urlParams.has('variables')) {
        restoreStateFromURL();

        // 変数の復元と自動グラフ表示
        if (timeseriesStateV2.pendingVariables && timeseriesStateV2.pendingVariables.length > 0) {
            // 少し待ってから変数を設定してグラフ表示
            setTimeout(async () => {
                // 既存の変数をクリア
                variableList.innerHTML = '';

                // URLから復元した変数を設定
                for (const varInfo of timeseriesStateV2.pendingVariables) {
                    const varIndex = variableList.children.length;
                    if (varIndex >= 2) break;

                    const axisValue = varIndex === 0 ? 'left' : 'right';
                    const axisLabel = varIndex === 0 ? '左軸' : '右軸';

                    const varId = variableCounter++;
                    const item = document.createElement('div');
                    item.className = 'variable-item';
                    item.dataset.varId = varId;
                    item.dataset.axis = axisValue;

                    item.innerHTML = `
                        <select class="form-select var-category" data-var-id="${varId}">
                            <option value="">カテゴリー</option>
                            ${categories.map(c => `<option value="${c}" ${c === varInfo.category ? 'selected' : ''}>${c}</option>`).join('')}
                        </select>
                        <select class="form-select var-characteristic" data-var-id="${varId}">
                            <option value="">特性値ID</option>
                        </select>
                        <span class="axis-label" style="color: var(--color-text-muted); font-size: var(--font-size-sm); padding: 0 8px;">${axisLabel}</span>
                        <button type="button" class="remove-variable-btn" data-var-id="${varId}">✕</button>
                    `;

                    variableList.appendChild(item);

                    // 特性値を設定
                    if (varInfo.category) {
                        const chars = await getCharacteristics(varInfo.category);
                        const charSelect = item.querySelector('.var-characteristic');
                        charSelect.innerHTML = '<option value="">特性値ID</option>' +
                            chars.map(c => `<option value="${c}" ${c === varInfo.characteristic_id ? 'selected' : ''}>${c}</option>`).join('');
                    }

                    // 削除ボタン
                    const removeBtn = item.querySelector('.remove-variable-btn');
                    removeBtn.addEventListener('click', () => item.remove());

                    // カテゴリー変更時
                    const categorySelect = item.querySelector('.var-category');
                    const charSelect = item.querySelector('.var-characteristic');
                    categorySelect.addEventListener('change', async () => {
                        if (categorySelect.value) {
                            const chars = await getCharacteristics(categorySelect.value);
                            charSelect.innerHTML = '<option value="">特性値ID</option>' +
                                chars.map(c => `<option value="${c}">${c}</option>`).join('');
                        } else {
                            charSelect.innerHTML = '<option value="">特性値ID</option>';
                        }
                    });
                }

                timeseriesStateV2.pendingVariables = null;

                // グラフ表示
                await loadTimeseriesData();
            }, 500);
        }
    }

    // フォーム送信
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await loadTimeseriesData();
    });

    // ズームリセット
    if (zoomResetBtn) {
        zoomResetBtn.addEventListener('click', () => {
            if (timeseriesChartV2) {
                timeseriesChartV2.resetZoom();
                document.getElementById('zoomInfo').textContent = '全期間表示';
            }
        });
    }

    // URL共有
    if (shareUrlBtn) {
        shareUrlBtn.addEventListener('click', () => {
            copyCurrentURL();
        });
    }

    // 表形式表示への遷移
    toTableBtn.addEventListener('click', () => {
        if (timeseriesStateV2.data) {
            sessionStorage.setItem('tableData', JSON.stringify({
                type: 'timeseries',
                data: timeseriesStateV2.data,
            }));
            window.location.href = '/table';
        }
    });

    async function loadTimeseriesData() {
        const machineIds = parseMachineIds(machinesTextarea.value);
        if (machineIds.length === 0) {
            alert('機番を入力してください');
            return;
        }
        if (machineIds.length > 5) {
            alert('最大5台まで入力できます');
            return;
        }

        // 変数情報を収集
        const variables = [];
        const variableItems = variableList.querySelectorAll('.variable-item');
        variableItems.forEach(item => {
            const category = item.querySelector('.var-category').value;
            const characteristic = item.querySelector('.var-characteristic').value;
            const axis = item.dataset.axis || 'left';

            if (category && characteristic) {
                variables.push({
                    category,
                    characteristic_id: characteristic,
                    axis,
                });
            }
        });

        if (variables.length === 0) {
            alert('少なくとも1つの変数を設定してください');
            return;
        }

        // 集計方法（最初の変数の設定を使用、または平均値をデフォルト）
        const aggregation = '平均値';

        // X軸タイプを取得
        const xAxisType = document.querySelector('input[name="xAxisType"]:checked')?.value || 'time_month';

        // 日単位表示の場合のパラメータ取得とバリデーション
        let dateFrom = null;
        let dateTo = null;

        if (xAxisType === 'time_day') {
            dateFrom = dateFromInput?.value;
            dateTo = dateToInput?.value;

            if (!dateFrom || !dateTo) {
                alert('表示期間を入力してください');
                return;
            }

            const fromDate = new Date(dateFrom);
            const toDate = new Date(dateTo);
            const diffDays = Math.ceil((toDate - fromDate) / (1000 * 60 * 60 * 24));

            if (diffDays < 0) {
                alert('終了日は開始日以降に設定してください');
                return;
            }

            if (diffDays > 60) {
                alert('日単位表示は最大60日間までです');
                return;
            }
        }

        try {
            // 多変量時系列データを取得
            const [multiData, annotationsData] = await Promise.all([
                fetchAPI('/timeseries/multi', {
                    method: 'POST',
                    body: JSON.stringify({
                        machine_ids: machineIds,
                        variables: variables,
                        aggregation: aggregation,
                        x_axis_type: xAxisType,
                        date_from: dateFrom,
                        date_to: dateTo,
                    }),
                }),
                // 使用回数モード以外ではアノテーション（日付ベース）を表示
                (showAnnotations.checked && xAxisType !== 'usage') ? fetchAPI('/annotations', {
                    method: 'POST',
                    body: JSON.stringify({
                        machine_ids: machineIds,
                        months: 12,
                        date_from: dateFrom,
                        date_to: dateTo,
                    }),
                }) : Promise.resolve([]),
            ]);

            timeseriesStateV2.data = multiData;
            timeseriesStateV2.annotations = annotationsData;
            timeseriesStateV2.variables = variables;

            renderTimeseriesChartV2(multiData, annotationsData);
            showElement('chartCard');

            // URLパラメータを更新
            updateURLState({
                machines: machineIds.join(','),
                variables: JSON.stringify(variables),
            });
        } catch (error) {
            console.error('Error loading timeseries data:', error);
            alert('データの取得に失敗しました');
        }
    }
}

function renderTimeseriesChartV2(data, annotations = []) {
    const ctx = document.getElementById('timeseriesChart');
    const overviewCtx = document.getElementById('overviewChart');
    if (!ctx) return;

    if (timeseriesChartV2) {
        timeseriesChartV2.destroy();
    }
    if (overviewChartV2) {
        overviewChartV2.destroy();
    }

    // データセットを構築
    const datasets = data.datasets.map((ds, i) => {
        const colorIndex = i % CHART_COLORS.length;
        return {
            label: `${ds.machine_id} - ${ds.variable.characteristic_id}`,
            data: ds.data,
            borderColor: CHART_COLORS[colorIndex],
            backgroundColor: CHART_BG_COLORS[colorIndex],
            borderWidth: 2,
            tension: 0.3,
            fill: false,
            yAxisID: ds.axis === 'right' ? 'y1' : 'y',
        };
    });

    // アノテーション設定
    const annotationConfig = {};
    if (annotations.length > 0) {
        annotations.forEach((ann, i) => {
            annotationConfig[`line${i}`] = {
                type: 'line',
                xMin: ann.xMin,
                xMax: ann.xMax,
                borderColor: ann.borderColor,
                borderWidth: ann.borderWidth,
                borderDash: ann.borderDash || [],
                label: {
                    display: true,
                    content: ann.label.content,
                    position: 'start',
                    backgroundColor: ann.borderColor,
                    font: { size: 9 },
                },
            };
        });
    }

    // スケール設定
    const scales = {
        x: {
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
        },
        y: {
            type: 'linear',
            display: true,
            position: 'left',
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
            title: {
                display: true,
                text: data.scales?.left?.label || '',
            },
        },
    };

    if (data.scales?.right) {
        scales.y1 = {
            type: 'linear',
            display: true,
            position: 'right',
            grid: { drawOnChartArea: false },
            title: {
                display: true,
                text: data.scales.right.label,
            },
        };
    }

    // メインチャート
    timeseriesChartV2 = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { position: 'top' },
                annotation: {
                    annotations: annotationConfig,
                },
                zoom: {
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'x',
                        onZoomComplete: ({ chart }) => {
                            updateZoomInfo(chart);
                        },
                    },
                    pan: {
                        enabled: true,
                        mode: 'x',
                    },
                },
            },
            scales: scales,
        },
    });

    // 概要チャート（Brush用）
    if (overviewCtx) {
        overviewChartV2 = new Chart(overviewCtx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: datasets.map(ds => ({
                    ...ds,
                    borderWidth: 1,
                    pointRadius: 0,
                })),
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    annotation: { annotations: {} },
                },
                scales: {
                    x: { display: false },
                    y: { display: false },
                    y1: { display: false },
                },
            },
        });
    }
}

function updateZoomInfo(chart) {
    const zoomInfo = document.getElementById('zoomInfo');
    if (!zoomInfo) return;

    const xScale = chart.scales.x;
    if (xScale) {
        const min = xScale.min;
        const max = xScale.max;
        const labels = chart.data.labels;
        if (min === 0 && max === labels.length - 1) {
            zoomInfo.textContent = '全期間表示';
        } else {
            const minLabel = labels[Math.max(0, Math.floor(min))] || '';
            const maxLabel = labels[Math.min(labels.length - 1, Math.ceil(max))] || '';
            zoomInfo.textContent = `${minLabel} 〜 ${maxLabel}`;
        }
    }
}


// ========================================
// EDA型ダッシュボード - 断面データ表示 V2
// ========================================
let distributionChartV2 = null;
let distributionStateV2 = {
    data: null,
    chartType: 'histogram',
    scatterData: null,
    boxplotData: null,
    distributionData: null,
    linechartData: null,
};

async function initHistogramPageV2() {
    const form = document.getElementById('histogramForm');
    const seriesSelect = document.getElementById('hist-series');
    const modelSelect = document.getElementById('hist-model');
    const dateFromInput = document.getElementById('hist-date-from');
    const dateToInput = document.getElementById('hist-date-to');
    const categorySelect = document.getElementById('hist-category');
    const characteristicSelect = document.getElementById('hist-characteristic');
    const aggregationSelect = document.getElementById('hist-aggregation');
    const machinesTextarea = document.getElementById('hist-machines');
    const toTableBtn = document.getElementById('histToTableBtn');
    const shareUrlBtn = document.getElementById('shareUrlBtn');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const chartTypeTabs = document.querySelectorAll('.chart-type-tab');
    const scatterSettings = document.getElementById('scatterSettings');
    const scatterXCategory = document.getElementById('scatter-x-category');
    const scatterXCharacteristic = document.getElementById('scatter-x-characteristic');

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

    // 日付入力の初期値設定（本日から7日前まで）
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(today.getDate() - 7);
    if (dateFromInput) dateFromInput.value = weekAgo.toISOString().split('T')[0];
    if (dateToInput) dateToInput.value = today.toISOString().split('T')[0];

    // プリセット機能の初期化
    initPresetUI(
        'histogram',
        // getCurrentFilters: 現在のフォーム値を取得
        () => ({
            series: seriesSelect.value,
            model: modelSelect.value,
            dateFrom: dateFromInput?.value,
            dateTo: dateToInput?.value,
            category: categorySelect.value,
            characteristic: characteristicSelect.value,
            aggregation: aggregationSelect.value,
            machines: machinesTextarea?.value || '',
            chartType: distributionStateV2.chartType
        }),
        // applyFilters: プリセットをフォームに適用
        async (data) => {
            if (data.series) {
                seriesSelect.value = data.series;
                const models = await getModels(data.series);
                populateSelect('hist-model', models);
            }
            if (data.model) modelSelect.value = data.model;
            if (data.dateFrom && dateFromInput) dateFromInput.value = data.dateFrom;
            if (data.dateTo && dateToInput) dateToInput.value = data.dateTo;
            if (data.category) {
                categorySelect.value = data.category;
                const chars = await getCharacteristics(data.category);
                populateSelect('hist-characteristic', chars);
            }
            if (data.characteristic) characteristicSelect.value = data.characteristic;
            if (data.aggregation) aggregationSelect.value = data.aggregation;
            if (data.machines && machinesTextarea) machinesTextarea.value = data.machines;
            if (data.chartType) {
                distributionStateV2.chartType = data.chartType;
                const tab = document.querySelector(`.chart-type-tab[data-chart-type="${data.chartType}"]`);
                if (tab) {
                    chartTypeTabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                }
            }
            // 自動でグラフ表示
            await loadDistributionData();
        }
    );

    // 散布図用のカテゴリー
    if (scatterXCategory) {
        populateSelect('scatter-x-category', categories);
    }

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

    // 散布図X軸カテゴリー変更時
    if (scatterXCategory) {
        scatterXCategory.addEventListener('change', async () => {
            if (scatterXCategory.value) {
                const chars = await getCharacteristics(scatterXCategory.value);
                populateSelect('scatter-x-characteristic', chars);
            } else {
                populateSelect('scatter-x-characteristic', []);
            }
        });
    }

    // 箱ひげ図設定要素
    const boxplotSettings = document.getElementById('boxplotSettings');
    const boxplotBinWidthGroup = document.getElementById('boxplotBinWidthGroup');

    // 折れ線グラフ設定要素
    const linechartSettings = document.getElementById('linechartSettings');
    const linechartBinWidthGroup = document.getElementById('linechartBinWidthGroup');

    // 箱ひげ図X軸タイプ変更時（使用回数の場合のみビン幅設定を表示）
    document.querySelectorAll('input[name="boxplot-x-axis-type"]').forEach(radio => {
        radio.addEventListener('change', () => {
            const isUsage = radio.value === 'usage' && radio.checked;
            if (boxplotBinWidthGroup) boxplotBinWidthGroup.style.display = isUsage ? 'block' : 'none';
        });
    });

    // 折れ線グラフX軸タイプ変更時（製造月の場合はビン幅設定を非表示）
    document.querySelectorAll('input[name="linechart-x-axis-type"]').forEach(radio => {
        radio.addEventListener('change', () => {
            const isMfgMonth = radio.value === 'mfg_month' && radio.checked;
            if (linechartBinWidthGroup) linechartBinWidthGroup.style.display = isMfgMonth ? 'none' : 'block';
        });
    });

    // チャート種別タブ
    chartTypeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            chartTypeTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            distributionStateV2.chartType = tab.dataset.chartType;

            // 散布図設定の表示/非表示
            if (scatterSettings) {
                scatterSettings.style.display = distributionStateV2.chartType === 'scatter' ? 'block' : 'none';
            }

            // 箱ひげ図設定の表示/非表示
            if (boxplotSettings) {
                boxplotSettings.style.display = distributionStateV2.chartType === 'boxplot' ? 'block' : 'none';
            }

            // 折れ線グラフ設定の表示/非表示
            if (linechartSettings) {
                linechartSettings.style.display = distributionStateV2.chartType === 'linechart' ? 'block' : 'none';
            }

            // データがあれば再描画
            if (distributionStateV2.data) {
                renderDistributionChart();
            }
        });
    });

    // 検索ページから来た場合
    const savedMachines = sessionStorage.getItem('selectedMachines');
    if (savedMachines) {
        const machines = JSON.parse(savedMachines);
        machinesTextarea.value = machines.join(', ');
        sessionStorage.removeItem('selectedMachines');
    }

    // URLパラメータから状態を復元し、パラメータがあれば自動でグラフ表示
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('model') || urlParams.has('category')) {
        const model = urlParams.get('model');
        const category = urlParams.get('category');
        const characteristic = urlParams.get('characteristic');
        const aggregation = urlParams.get('aggregation');
        const month = urlParams.get('month');
        const machines = urlParams.get('machines');
        const chartType = urlParams.get('chartType');

        // 機番を復元
        if (machines && machinesTextarea) {
            machinesTextarea.value = machines.replace(/,/g, ', ');
        }

        // シリーズを復元（モデルから推測）
        if (model) {
            const prefix = model.charAt(0);
            const seriesMap = { 'A': 'SERIES-1', 'B': 'SERIES-2', 'C': 'SERIES-3' };
            const series = seriesMap[prefix] || 'SERIES-1';

            const seriesSelect = document.getElementById('hist-series');
            if (seriesSelect) {
                seriesSelect.value = series;
                // モデルリストを取得して設定
                getModels(series).then(models => {
                    populateSelect('hist-model', models);
                    const modelSelect = document.getElementById('hist-model');
                    if (modelSelect) {
                        modelSelect.value = model;
                    }
                });
            }
        }

        // カテゴリーと特性値を復元
        if (category) {
            const categorySelect = document.getElementById('hist-category');
            if (categorySelect) {
                categorySelect.value = category;
                // 特性値リストを取得して設定
                getCharacteristics(category).then(chars => {
                    populateSelect('hist-characteristic', chars);
                    if (characteristic) {
                        const charSelect = document.getElementById('hist-characteristic');
                        if (charSelect) {
                            charSelect.value = characteristic;
                        }
                    }
                });
            }
        }

        // 集計方法と月を復元
        if (aggregation) {
            const aggSelect = document.getElementById('hist-aggregation');
            if (aggSelect) aggSelect.value = aggregation;
        }
        if (month) {
            const monthSelect = document.getElementById('hist-month');
            if (monthSelect) monthSelect.value = month;
        }

        // チャート種別を復元
        if (chartType) {
            distributionStateV2.chartType = chartType;
            const tab = document.querySelector(`.chart-type-tab[data-chart-type="${chartType}"]`);
            if (tab) {
                document.querySelectorAll('.chart-type-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
            }
            // 散布図設定の表示/非表示
            if (scatterSettings) {
                scatterSettings.style.display = chartType === 'scatter' ? 'block' : 'none';
            }
        }

        // 少し待ってからグラフ表示（ドロップダウンの読み込み完了を待つ）
        setTimeout(async () => {
            await loadDistributionData();
        }, 800);
    }

    // フォーム送信
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await loadDistributionData();
    });

    // URL共有
    if (shareUrlBtn) {
        shareUrlBtn.addEventListener('click', () => {
            copyCurrentURL();
        });
    }

    // 表形式表示への遷移
    toTableBtn.addEventListener('click', () => {
        if (distributionStateV2.data) {
            sessionStorage.setItem('tableData', JSON.stringify({
                type: 'histogram',
                data: distributionStateV2.data,
            }));
            window.location.href = '/table';
        }
    });

    // 詳細テーブル管理初期化
    DetailTableManager.init();

    async function loadDistributionData() {
        const selectedMachines = parseMachineIds(machinesTextarea.value);

        const dateFrom = dateFromInput?.value;
        const dateTo = dateToInput?.value;

        // 日付範囲のバリデーション
        if (!dateFrom || !dateTo) {
            alert('対象期間を入力してください');
            return;
        }

        const fromDate = new Date(dateFrom);
        const toDate = new Date(dateTo);
        const diffDays = Math.ceil((toDate - fromDate) / (1000 * 60 * 60 * 24));

        if (diffDays < 0) {
            alert('終了日は開始日以降に設定してください');
            return;
        }

        if (diffDays > 31) {
            alert('対象期間は最大31日間までです');
            return;
        }

        const baseParams = {
            model: modelSelect.value,
            category: categorySelect.value,
            characteristic_id: characteristicSelect.value,
            aggregation: aggregationSelect.value,
            target_date_from: dateFrom,
            target_date_to: dateTo,
        };

        if (!baseParams.model || !baseParams.category || !baseParams.characteristic_id ||
            !baseParams.aggregation) {
            alert('必須条件をすべて選択してください');
            return;
        }

        try {
            // ヒストグラムデータを取得
            const histogramData = await fetchAPI('/histogram', {
                method: 'POST',
                body: JSON.stringify({
                    ...baseParams,
                    selected_machine_ids: selectedMachines.length > 0 ? selectedMachines : null,
                }),
            });

            distributionStateV2.data = histogramData;

            // 日付範囲の終了日から月を算出（散布図・箱ひげ図用）
            const targetMonth = baseParams.target_date_to.substring(0, 7);  // "YYYY-MM" 形式

            // 散布図データを取得（散布図タブ用）
            if (scatterXCategory?.value && scatterXCharacteristic?.value) {
                const scatterData = await fetchAPI('/scatter', {
                    method: 'POST',
                    body: JSON.stringify({
                        model: baseParams.model,
                        x_category: scatterXCategory.value,
                        x_characteristic_id: scatterXCharacteristic.value,
                        y_category: baseParams.category,
                        y_characteristic_id: baseParams.characteristic_id,
                        aggregation: baseParams.aggregation,
                        target_month: targetMonth,
                        selected_machine_ids: selectedMachines.length > 0 ? selectedMachines : null,
                    }),
                });
                distributionStateV2.scatterData = scatterData;
            }

            // 箱ひげ図データを取得
            const allModels = await getModels(seriesSelect.value);
            if (allModels.length > 0) {
                const boxplotData = await fetchAPI('/boxplot', {
                    method: 'POST',
                    body: JSON.stringify({
                        models: allModels,
                        category: baseParams.category,
                        characteristic_id: baseParams.characteristic_id,
                        aggregation: baseParams.aggregation,
                        target_month: targetMonth,
                    }),
                });
                distributionStateV2.boxplotData = boxplotData;
            }

            // 箱ひげ図の分布傾向データを取得（X軸が使用回数または製造月の場合）
            const boxplotXAxisType = document.querySelector('input[name="boxplot-x-axis-type"]:checked')?.value || 'model';
            if (boxplotXAxisType !== 'model') {
                const boxplotBinWidth = parseInt(document.getElementById('boxplot-bin-width')?.value || '50000');

                const boxplotDistData = await fetchAPI('/distribution-boxplot', {
                    method: 'POST',
                    body: JSON.stringify({
                        model: baseParams.model,
                        x_axis_type: boxplotXAxisType,
                        bin_width: boxplotBinWidth,
                        category: baseParams.category,
                        characteristic_id: baseParams.characteristic_id,
                        aggregation: baseParams.aggregation,
                        selected_machine_ids: selectedMachines.length > 0 ? selectedMachines : null,
                        chart_type: 'boxplot',
                    }),
                });
                distributionStateV2.distributionData = boxplotDistData;
            }

            // 折れ線グラフのデータを取得
            const linechartXAxisType = document.querySelector('input[name="linechart-x-axis-type"]:checked')?.value || 'usage';
            const linechartBinWidth = parseInt(document.getElementById('linechart-bin-width')?.value || '50000');

            const linechartData = await fetchAPI('/distribution-boxplot', {
                method: 'POST',
                body: JSON.stringify({
                    model: baseParams.model,
                    x_axis_type: linechartXAxisType,
                    bin_width: linechartBinWidth,
                    category: baseParams.category,
                    characteristic_id: baseParams.characteristic_id,
                    aggregation: baseParams.aggregation,
                    selected_machine_ids: selectedMachines.length > 0 ? selectedMachines : null,
                    chart_type: 'line',
                }),
            });

            // 折れ線グラフ用データを保存（箱ひげ図用データがない場合はこちらも使用）
            if (boxplotXAxisType === 'model') {
                distributionStateV2.distributionData = linechartData;
            }
            distributionStateV2.linechartData = linechartData;

            renderDistributionChart();
            showElement('chartCard');

            // URLパラメータを更新
            updateURLState({
                model: baseParams.model,
                category: baseParams.category,
                characteristic: baseParams.characteristic_id,
                aggregation: baseParams.aggregation,
                month: baseParams.target_month,
                machines: selectedMachines.join(','),
                chartType: distributionStateV2.chartType,
            });
        } catch (error) {
            console.error('Error loading distribution data:', error);
            alert('データの取得に失敗しました');
        }
    }
}

function renderDistributionChart() {
    const ctx = document.getElementById('distributionChart');
    if (!ctx) return;

    if (distributionChartV2) {
        distributionChartV2.destroy();
    }

    const chartType = distributionStateV2.chartType;

    if (chartType === 'histogram') {
        renderHistogramChartV2(ctx, distributionStateV2.data);
    } else if (chartType === 'scatter') {
        renderScatterChartV2(ctx, distributionStateV2.scatterData || distributionStateV2.data);
    } else if (chartType === 'boxplot') {
        // 箱ひげ図: X軸タイプに応じて切替
        const boxplotXAxisType = document.querySelector('input[name="boxplot-x-axis-type"]:checked')?.value || 'model';
        if (boxplotXAxisType === 'model') {
            renderBoxplotChartV2(ctx, distributionStateV2.boxplotData);
        } else {
            renderDistributionBoxplotChart(ctx, distributionStateV2.distributionData);
        }
    } else if (chartType === 'linechart') {
        renderDistributionBoxplotChart(ctx, distributionStateV2.linechartData || distributionStateV2.distributionData);
    }
}

function renderHistogramChartV2(ctx, data) {
    if (!data) return;

    const labels = [];
    for (let i = 0; i < data.bins.length - 1; i++) {
        labels.push(`${data.bins[i]}-${data.bins[i + 1]}`);
    }

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

    distributionChartV2 = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.dataset.label}: ${context.raw.toFixed(1)}%`,
                    },
                },
            },
            scales: {
                x: { title: { display: true, text: '値の範囲' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                y: { title: { display: true, text: '相対頻度（%）' }, beginAtZero: true, max: 100, grid: { color: 'rgba(0, 0, 0, 0.05)' }, ticks: { callback: (v) => `${v}%` } },
            },
            onClick: (event, elements) => {
                if (elements.length === 0) return;

                const clickedIndex = elements[0].index;
                const bins = data.bins;
                const minValue = bins[clickedIndex];
                const maxValue = bins[clickedIndex + 1];

                // 選択されたビン範囲のデータを抽出
                const rawData = data.raw_data || [];
                const filteredData = rawData.filter(d => d.value >= minValue && d.value < maxValue);

                // 詳細テーブルにデータを表示
                showHistogramDetailTable(filteredData, minValue, maxValue);
            },
        },
    });
}

/* ========================================
   詳細データテーブル管理
   ======================================== */
const DetailTableManager = {
    data: [],
    currentPage: 1,
    pageSize: 20,
    sortState: { column: 'value', direction: 'desc' },
    title: '',

    init() {
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        const pageSizeSelect = document.getElementById('pageSizeSelect');
        const pageJumpInput = document.getElementById('pageJumpInput');
        const dlBtn = document.getElementById('downloadDataBtn');
        const closeBtn = document.getElementById('closeDetailBtn');

        if (prevBtn) prevBtn.addEventListener('click', () => this.changePage(-1));
        if (nextBtn) nextBtn.addEventListener('click', () => this.changePage(1));
        if (pageSizeSelect) pageSizeSelect.addEventListener('change', (e) => this.setPageSize(Number(e.target.value)));
        if (pageJumpInput) {
            pageJumpInput.addEventListener('change', (e) => this.jumpToPage(Number(e.target.value)));
            pageJumpInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.jumpToPage(Number(e.target.value));
            });
        }
        if (dlBtn) dlBtn.addEventListener('click', () => this.downloadCSV());
        if (closeBtn) closeBtn.addEventListener('click', () => {
            const area = document.getElementById('dataGridArea');
            if (area) area.style.display = 'none';
        });

        // ソートヘッダー
        document.querySelectorAll('.sortable-header').forEach(th => {
            th.addEventListener('click', () => {
                const column = th.dataset.column;
                if (column) this.toggleSort(column);
            });
        });
    },

    setData(data, title) {
        this.data = [...data]; // ソート用にコピー
        this.title = title || '詳細データ';
        this.currentPage = 1;
        // デフォルトソート（値の降順）
        this.sortState = { column: 'value', direction: 'desc' };
        this.applySort();
        this.render();
    },

    setPageSize(size) {
        this.pageSize = size;
        this.currentPage = 1;
        this.render();
    },

    changePage(delta) {
        const totalPages = Math.ceil(this.data.length / this.pageSize) || 1;
        const newPage = this.currentPage + delta;
        if (newPage >= 1 && newPage <= totalPages) {
            this.currentPage = newPage;
            this.render();
        }
    },

    jumpToPage(page) {
        const totalPages = Math.ceil(this.data.length / this.pageSize) || 1;
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.render();
        } else {
            // 無効な入力の場合は現在のページに戻して再描画
            this.render();
        }
    },

    toggleSort(column) {
        if (this.sortState.column === column) {
            this.sortState.direction = this.sortState.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortState.column = column;
            this.sortState.direction = 'desc'; // 新しい列は降順から
        }
        this.applySort();
        this.render();
    },

    applySort() {
        const { column, direction } = this.sortState;
        this.data.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];

            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();

            if (valA < valB) return direction === 'asc' ? -1 : 1;
            if (valA > valB) return direction === 'asc' ? 1 : -1;
            return 0;
        });
    },

    render() {
        const dataGridArea = document.getElementById('dataGridArea');
        const detailTableBody = document.getElementById('detailTableBody');
        const cardTitle = dataGridArea?.querySelector('.card-title');
        const detailDataCount = document.getElementById('detailDataCount');
        const pageInfo = document.getElementById('pageInfo');
        const pageJumpInput = document.getElementById('pageJumpInput');
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        const paginationArea = document.getElementById('detailPagination');

        if (!dataGridArea || !detailTableBody) return;

        // タイトルと件数更新
        if (cardTitle) cardTitle.textContent = this.title;
        if (detailDataCount) detailDataCount.textContent = `${this.data.length.toLocaleString()}件`;

        // ヘッダーのソート状態表示更新
        document.querySelectorAll('.sortable-header').forEach(th => {
            th.classList.remove('asc', 'desc');
            if (th.dataset.column === this.sortState.column) {
                th.classList.add(this.sortState.direction);
            }
        });

        // データがない場合
        if (this.data.length === 0) {
            detailTableBody.innerHTML = '<tr><td colspan="2" class="text-center">該当するデータがありません</td></tr>';
            if (paginationArea) paginationArea.style.display = 'none';
            dataGridArea.style.display = '';
            return;
        }

        // ページネーション計算
        const totalItems = this.data.length;
        const totalPages = Math.ceil(totalItems / this.pageSize);
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = Math.min(startIndex + this.pageSize, totalItems);
        const paginatedData = this.data.slice(startIndex, endIndex);

        // テーブル更新
        detailTableBody.innerHTML = '';
        paginatedData.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.machine_id}</td>
                <td>${item.value.toFixed(2)}</td>
            `;
            detailTableBody.appendChild(tr);
        });

        // ページネーションUI更新
        if (paginationArea) paginationArea.style.display = 'flex';
        if (pageInfo) pageInfo.textContent = `${this.currentPage} / ${totalPages} ページ`;

        if (pageJumpInput) {
            pageJumpInput.max = totalPages;
            pageJumpInput.value = this.currentPage;
        }

        if (prevBtn) prevBtn.disabled = this.currentPage === 1;
        if (nextBtn) nextBtn.disabled = this.currentPage === totalPages;

        // エリア表示
        dataGridArea.style.display = '';
    },

    downloadCSV() {
        const headers = ['機番', '値'];
        const rows = this.data.map(item => `${item.machine_id},${item.value}`);
        const csvContent = [headers.join(','), ...rows].join('\n');

        const blob = new Blob([new Uint8Array([0xEF, 0xBB, 0xBF]), csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `data_export_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};

// ヒストグラム詳細テーブル表示（互換性のため）
function showHistogramDetailTable(data, minValue, maxValue) {
    DetailTableManager.setData(data, `選択データ詳細（${minValue} ～ ${maxValue}）`);
}

// 折れ線グラフ詳細テーブル表示（互換性のため）
function showLinechartDetailTable(data, label) {
    DetailTableManager.setData(data, `選択データ詳細（${label}）`);
}

function renderScatterChartV2(ctx, data) {
    if (!data || !data.data) {
        // ヒストグラムデータから散布図を生成
        if (distributionStateV2.data?.raw_data) {
            const rawData = distributionStateV2.data.raw_data;
            const scatterData = rawData.map((d, i) => ({
                x: i,
                y: d.value,
                machine_id: d.machine_id,
            }));

            distributionChartV2 = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: '機番別値',
                        data: scatterData,
                        backgroundColor: CHART_COLORS[0],
                        pointRadius: 4,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: (context) => `機番: ${context.raw.machine_id}, 値: ${context.raw.y}`,
                            },
                        },
                    },
                    scales: {
                        x: { title: { display: true, text: 'インデックス' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                        y: { title: { display: true, text: '値' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                    },
                },
            });
        }
        return;
    }

    const scatterData = data.data.map(d => ({
        x: d.x,
        y: d.y,
        machine_id: d.machine_id,
        selected: d.selected,
    }));

    const selectedData = scatterData.filter(d => d.selected);
    const otherData = scatterData.filter(d => !d.selected);

    const datasets = [];
    if (selectedData.length > 0) {
        datasets.push({
            label: '選択機番',
            data: selectedData,
            backgroundColor: CHART_COLORS[0],
            pointRadius: 6,
        });
    }
    datasets.push({
        label: selectedData.length > 0 ? 'その他' : '全機番',
        data: selectedData.length > 0 ? otherData : scatterData,
        backgroundColor: selectedData.length > 0 ? CHART_COLORS[1] : CHART_COLORS[0],
        pointRadius: 4,
    });

    distributionChartV2 = new Chart(ctx, {
        type: 'scatter',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: (context) => `機番: ${context.raw.machine_id}, X: ${context.raw.x}, Y: ${context.raw.y}`,
                    },
                },
                title: {
                    display: true,
                    text: `相関係数: ${data.correlation}`,
                },
            },
            scales: {
                x: { title: { display: true, text: data.x_label || 'X軸' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                y: { title: { display: true, text: data.y_label || 'Y軸' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
            },
        },
    });
}

function renderBoxplotChartV2(ctx, data) {
    if (!data) return;

    // Chart.js boxplot plugin format
    const boxplotData = data.datasets[0].data.map(d => ({
        min: d.min,
        q1: d.q1,
        median: d.median,
        q3: d.q3,
        max: d.max,
        outliers: d.outliers || [],
    }));

    distributionChartV2 = new Chart(ctx, {
        type: 'boxplot',
        data: {
            labels: data.labels,
            datasets: [{
                label: data.datasets[0].label,
                data: boxplotData,
                backgroundColor: CHART_BG_COLORS[0],
                borderColor: CHART_COLORS[0],
                borderWidth: 2,
                outlierBackgroundColor: CHART_COLORS[2],
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
            },
            scales: {
                x: { title: { display: true, text: '機種番号' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                y: { title: { display: true, text: '値' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
            },
        },
    });
}


function renderDistributionBoxplotChart(ctx, data) {
    if (!data || !data.datasets || data.datasets.length === 0) return;

    const chartType = data.chart_type || 'boxplot';

    if (chartType === 'line') {
        // リボンプロット（平均線＋95%パーセンタイル帯）
        const datasets = [];

        data.datasets.forEach((ds, idx) => {
            const means = ds.data.map(d => d.mean);
            const upperBound = ds.data.map(d => d.p97_5 || d.mean + d.std);  // 97.5パーセンタイル
            const lowerBound = ds.data.map(d => d.p2_5 || d.mean - d.std);   // 2.5パーセンタイル

            const color = ds.group === 'selected' ? CHART_COLORS[0] :
                ds.group === 'other' ? CHART_COLORS[1] : CHART_COLORS[idx];
            const bgColor = ds.group === 'selected' ? 'rgba(99, 102, 241, 0.2)' :
                ds.group === 'other' ? 'rgba(236, 72, 153, 0.2)' : 'rgba(99, 102, 241, 0.2)';

            // 上限ライン（97.5パーセンタイル）
            datasets.push({
                label: `${ds.label} P97.5`,
                data: upperBound,
                borderColor: color,
                borderWidth: 1,
                borderDash: [2, 2],
                pointRadius: 0,
                fill: false,
            });

            // 平均ライン
            datasets.push({
                label: ds.label,
                data: means,
                borderColor: color,
                backgroundColor: color,
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: color,
                fill: false,
                tension: 0.1,
            });

            // 下限ライン（2.5パーセンタイル、上限との間を塗りつぶし）
            datasets.push({
                label: `${ds.label} P2.5`,
                data: lowerBound,
                borderColor: color,
                borderWidth: 1,
                borderDash: [2, 2],
                pointRadius: 0,
                fill: '-2',  // 2つ前のデータセット（上限）との間を塗りつぶし
                backgroundColor: bgColor,
            });
        });

        distributionChartV2 = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: datasets.filter(ds => !ds.hidden),
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            filter: (legendItem, chartData) => {
                                // 上限・下限ラインは凡例から除外
                                return !legendItem.text.includes('P97.5') && !legendItem.text.includes('P2.5');
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const dsIndex = Math.floor(context.datasetIndex / 3);  // 3データセットで1グループ
                                const origDs = data.datasets[dsIndex >= data.datasets.length ? data.datasets.length - 1 : dsIndex];
                                if (origDs && origDs.data[context.dataIndex]) {
                                    const d = origDs.data[context.dataIndex];
                                    return `95%区間: ${d.p2_5} - ${d.p97_5}, データ数: ${d.count}`;
                                }
                                return '';
                            },
                        },
                    },
                    subtitle: {
                        display: true,
                        text: '実線: 平均値 ／ 帯: 95%パーセンタイル区間 (P2.5 - P97.5)',
                        color: '#666',
                        font: { size: 12 },
                        padding: { bottom: 10 },
                    },
                },
                scales: {
                    x: { title: { display: true, text: data.x_axis_label || 'X軸' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                    y: { title: { display: true, text: '値' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                },
                onClick: (event, elements) => {
                    if (elements.length === 0) return;

                    const clickedIndex = elements[0].index;
                    const label = data.labels[clickedIndex];

                    // raw_data_by_binからクリックされたビンのデータを取得
                    const rawDataByBin = data.raw_data_by_bin || [];
                    const binData = rawDataByBin[clickedIndex] || [];

                    // 詳細テーブルにデータを表示
                    showLinechartDetailTable(binData, label);
                },
            },
        });
    } else {
        // 箱ひげ図
        const datasets = data.datasets.map((ds, idx) => {
            const color = ds.group === 'selected' ? CHART_COLORS[0] :
                ds.group === 'other' ? CHART_COLORS[1] : CHART_COLORS[idx];
            const bgColor = ds.group === 'selected' ? CHART_BG_COLORS[0] :
                ds.group === 'other' ? CHART_BG_COLORS[1] : CHART_BG_COLORS[idx];

            return {
                label: ds.label,
                data: ds.data.map(d => ({
                    min: d.min,
                    q1: d.q1,
                    median: d.median,
                    q3: d.q3,
                    max: d.max,
                    outliers: d.outliers || [],
                })),
                backgroundColor: bgColor,
                borderColor: color,
                borderWidth: 2,
                outlierBackgroundColor: CHART_COLORS[2],
            };
        });

        distributionChartV2 = new Chart(ctx, {
            type: 'boxplot',
            data: {
                labels: data.labels,
                datasets: datasets,
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const ds = data.datasets[context.datasetIndex];
                                if (ds && ds.data[context.dataIndex]) {
                                    const d = ds.data[context.dataIndex];
                                    return d.count ? `データ数: ${d.count}` : '';
                                }
                                return '';
                            },
                        },
                    },
                },
                scales: {
                    x: { title: { display: true, text: data.x_axis_label || 'X軸' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                    y: { title: { display: true, text: '値' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                },
            },
        });
    }
}

// ========================================
// URL状態管理
// ========================================
function updateURLState(params) {
    const url = new URL(window.location);
    Object.keys(params).forEach(key => {
        if (params[key]) {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    window.history.replaceState({}, '', url);
}

function restoreStateFromURL() {
    const params = new URLSearchParams(window.location.search);

    // 機番の復元
    const machines = params.get('machines');
    if (machines) {
        const machinesInput = document.getElementById('ts-machines') || document.getElementById('hist-machines');
        if (machinesInput) {
            machinesInput.value = machines.replace(/,/g, ', ');
        }
    }

    // シリーズの復元（モデルから推測も可能）
    let series = params.get('series');
    const model = params.get('model');
    if (!series && model) {
        // モデルからシリーズを推測（A-1 → SERIES-1, B-1 → SERIES-2, C-1 → SERIES-3）
        const prefix = model.charAt(0);
        const seriesMap = { 'A': 'SERIES-1', 'B': 'SERIES-2', 'C': 'SERIES-3' };
        series = seriesMap[prefix] || 'SERIES-1';
    }
    if (series) {
        const seriesEl = document.getElementById('hist-series');
        if (seriesEl) {
            seriesEl.value = series;
            seriesEl.dispatchEvent(new Event('change'));
        }
    }

    // フォーム要素の復元
    const mappings = {
        'model': 'hist-model',
        'category': 'hist-category',
        'characteristic': 'hist-characteristic',
        'aggregation': 'hist-aggregation',
        'month': 'hist-month',
        'chartType': null,
    };

    Object.keys(mappings).forEach(key => {
        const value = params.get(key);
        if (value && mappings[key]) {
            const el = document.getElementById(mappings[key]);
            if (el) {
                el.value = value;
                el.dispatchEvent(new Event('change'));
            }
        }
    });

    // チャート種別の復元
    const chartType = params.get('chartType');
    if (chartType) {
        distributionStateV2.chartType = chartType;
        const tab = document.querySelector(`.chart-type-tab[data-chart-type="${chartType}"]`);
        if (tab) {
            document.querySelectorAll('.chart-type-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
        }
    }

    // 時系列用変数の復元
    const variablesParam = params.get('variables');
    if (variablesParam) {
        try {
            const variables = JSON.parse(variablesParam);
            // 時系列の変数復元は別途実行（initTimeseriesV2で処理）
            timeseriesStateV2.pendingVariables = variables;
        } catch (e) {
            console.error('Failed to parse variables from URL:', e);
        }
    }
}

function copyCurrentURL() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        const btn = document.getElementById('shareUrlBtn');
        if (btn) {
            const originalText = btn.textContent;
            btn.textContent = '✓ コピーしました';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('copied');
            }, 2000);
        }
    }).catch(() => {
        prompt('以下のURLをコピーしてください:', url);
    });
}

