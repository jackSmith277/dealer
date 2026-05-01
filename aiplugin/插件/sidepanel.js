// ========== 配置区域 ==========
const API_CONFIG = {
    apiUrl: 'https://aihubmix.com/v1/chat/completions',
    apiKey: 'sk-gvlleYSWqm5LRvfQ8e6744F1802d4d9b8aEf1d400800443d',
    model: 'Qwen/Qwen2.5-7B-Instruct',
    systemPrompt: `你是一名专业的 4S 店汽车销售顾问。你的任务是协助销售人员进行客户接待、车型介绍、价格计算和邀约试驾。
核心能力：
熟悉店内所有车型的配置、价格、优惠政策。
能够根据客户需求（预算、用途、家庭情况）推荐合适车型。
能够处理常见的异议（如价格太高、竞品对比）。
在对话结束时，提醒销售顾问尝试获取客户联系方式或邀约到店。
注意事项：
回答要热情、专业、简洁。
如果用户发送了文件或图片（如车型手册、竞品参数），请根据内容提供帮助。
涉及价格问题时，请务必参考知识库中的最新价格表，如果没有则提示咨询店长。
始终使用中文回答。`,
    maxContextMessages: 10,
    temperature: 0.3,
    max_tokens: 2000,
    ragEnabled: true,
    ragTopK: 3,
    knowledgeBase: [],
    supportMultimodal: false
};
const EXCEL_BACKEND_CONFIG = {
    baseUrl: '',
    uploadEndpoint: '/api/excel-report'
};
const CRAWL_BACKEND_CONFIG = {
    analyzeEndpoint: '/api/analyze'
};
const INSIGHT_BACKEND_CONFIG = {
    baseUrl: '',
    analyzeEndpoint: '/api/insight-analyze',
    reportEndpoint: '/api/insight-report'
};
const FILE_CONFIG = {
    maxFileSize: 10 * 1024 * 1024,
    allowedTypes: {
        image: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        document: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/markdown'],
        excel: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'],
        audio: ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/aac', 'audio/flac']
    },
    maxAttachments: 5
};
const DEBUG_MODE = true;
let messages = [];
let searchIndex = {};

const StorageUtil = {
    get: function (keys) {
        return new Promise((resolve) => {
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                chrome.storage.local.get(keys, resolve);
            } else {
                const result = {};
                keys.forEach(key => {
                    const value = localStorage.getItem(key);
                    try {
                        result[key] = value ? JSON.parse(value) : null;
                    } catch {
                        result[key] = value;
                    }
                });
                resolve(result);
            }
        });
    },
    set: function (data) {
        return new Promise((resolve) => {
            if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
                chrome.storage.local.set(data, resolve);
            } else {
                Object.keys(data).forEach(key => {
                    localStorage.setItem(key, JSON.stringify(data[key]));
                });
                resolve();
            }
        });
    }
};
let domElements = {};
let currentAttachments = [];
let selectedExcelFile = null;
// 服务洞察相关变量 - 新增
let selectedInsightAudioFile = null;
let currentInsightInputType = 'text';
let currentCrawlResult = null;

// ========== 文件处理工具函数 ==========
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(type) {
    if (type.startsWith('image/')) return '🖼️';
    if (type.includes('pdf')) return '📄';
    if (type.includes('word')) return '📝';
    if (type.includes('text')) return '📃';
    if (type.includes('excel') || type.includes('spreadsheet')) return '📊';
    if (type.includes('audio')) return '🎵';
    return '📎';
}

function getFileType(file) {
    if (FILE_CONFIG.allowedTypes.image.includes(file.type)) return 'image';
    if (FILE_CONFIG.allowedTypes.document.includes(file.type)) return 'document';
    if (FILE_CONFIG.allowedTypes.excel.includes(file.type) || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) return 'excel';
    if (FILE_CONFIG.allowedTypes.audio.includes(file.type) || file.name.endsWith('.mp3') || file.name.endsWith('.wav') || file.name.endsWith('.m4a')) return 'audio';
    return 'other';
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

async function addAttachments(files) {
    const validFiles = [];
    for (const file of files) {
        if (file.size > FILE_CONFIG.maxFileSize) {
            alert(`⚠️ 文件 "${file.name}" 超过 10MB 限制`);
            continue;
        }

        const fileType = getFileType(file);
        if (fileType === 'other') {
            alert(`⚠️ 不支持的文件类型：${file.name}`);
            continue;
        }

        if (fileType === 'excel') {
            alert(`⚠️ Excel 文件请在"Excel 分析"标签页上传`);
            continue;
        }

        if (fileType === 'audio') {
            alert(`⚠️ 音频文件请在"服务洞察"标签页上传`);
            continue;
        }

        if (currentAttachments.length + validFiles.length >= FILE_CONFIG.maxAttachments) {
            alert(`⚠️ 最多只能添加 ${FILE_CONFIG.maxAttachments} 个附件`);
            break;
        }

        let content = null;

        if (fileType === 'image') {
            try {
                content = await fileToBase64(file);
            } catch (e) {
                alert(`⚠️ 图片处理失败：${file.name}`);
                continue;
            }
        }

        if (fileType === 'document') {
            try {
                content = await parseDocumentFile(file);
            } catch (e) {
                alert(`⚠️ 文档解析失败：${file.name}`);
                console.error(e);
                continue;
            }
        }

        validFiles.push({
            file: file,
            name: file.name,
            size: file.size,
            type: fileType,
            mimeType: file.type,
            content: content,
            id: Date.now() + Math.random()
        });
    }

    currentAttachments = [...currentAttachments, ...validFiles];
    renderFilePreview();

    if (DEBUG_MODE) {
        console.log('📎 附件列表:', currentAttachments);
    }
}

async function parseDocumentFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = async function (event) {
            try {
                const arrayBuffer = event.target.result;

                if (file.type.includes('word') || file.name.endsWith('.docx')) {
                    if (typeof mammoth !== 'undefined') {
                        const result = await mammoth.extractRawText({ arrayBuffer: arrayBuffer });
                        resolve(result.value || '无法解析文档内容');
                    } else {
                        resolve('⚠️ 未加载 mammoth.js，无法解析 Word 文档');
                    }
                }
                else if (file.type.includes('pdf')) {
                    resolve('📄 PDF 文件已上传，但需要后端支持才能解析内容');
                }
                else if (file.type.includes('text')) {
                    const text = new TextDecoder('utf-8').decode(arrayBuffer);
                    resolve(text.substring(0, 50000));
                }
                else {
                    resolve('文件已上传');
                }
            } catch (err) {
                reject(err);
            }
        };

        reader.onerror = () => reject(new Error('文件读取失败'));
        reader.readAsArrayBuffer(file);
    });
}

function renderFilePreview() {
    const container = domElements.filePreviewContainer;
    if (!container) return;

    if (currentAttachments.length === 0) {
        container.classList.remove('active');
        container.innerHTML = '';
        return;
    }

    container.classList.add('active');
    container.innerHTML = currentAttachments.map(att => `
        <div class="file-preview-item" data-id="${att.id}">
            ${att.type === 'image'
            ? `<img src="${att.content}" alt="${att.name}">`
            : `<div class="file-icon" style="font-size: 24px; margin-right: 10px;">${getFileIcon(att.mimeType)}</div>`
        }
            <div class="file-info">
                <div class="file-name">${att.name}</div>
                <div class="file-size">${formatFileSize(att.size)}</div>
            </div>
            <button class="remove-file" onclick="removeAttachment('${att.id}')">×</button>
        </div>
    `).join('');
}

function removeAttachment(id) {
    currentAttachments = currentAttachments.filter(att => att.id != id);
    renderFilePreview();
}

// ========== Excel 文件处理 ==========
function handleExcelFileSelect(file) {
    if (!file) return;

    if (file.size > FILE_CONFIG.maxFileSize) {
        showExcelStatus(`⚠️ 文件 "${file.name}" 超过 10MB 限制`, 'error');
        return;
    }

    const fileType = getFileType(file);
    if (fileType !== 'excel') {
        showExcelStatus(`⚠️ 请选择 Excel 文件 (.xlsx/.xls)`, 'error');
        return;
    }

    selectedExcelFile = file;

    const fileInfo = document.getElementById('selectedFileInfo');
    const fileName = document.getElementById('selectedFileName');
    const uploadBtn = document.getElementById('uploadExcelBtn');

    if (fileInfo && fileName && uploadBtn) {
        fileInfo.classList.add('active');
        fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
        uploadBtn.disabled = false;
    }

    showExcelStatus(`✅ 已选择：${file.name}`, 'info');
}

async function uploadExcelForAnalysis() {
    if (!selectedExcelFile) {
        showExcelStatus('⚠️ 请先选择 Excel 文件', 'error');
        return;
    }

    const uploadBtn = document.getElementById('uploadExcelBtn');
    const resultDiv = document.getElementById('excelResult');
    const markdownReportDiv = document.getElementById('markdownReport');

    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ 分析中...';
    showExcelStatus('🔄 正在上传并分析 Excel 文件...', 'info');

    if (resultDiv) resultDiv.classList.remove('active');
    if (markdownReportDiv) markdownReportDiv.innerHTML = '';

    const formData = new FormData();
    formData.append('excel_file', selectedExcelFile);

    try {
        const response = await fetch(`${EXCEL_BACKEND_CONFIG.baseUrl}${EXCEL_BACKEND_CONFIG.uploadEndpoint}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
        }

        const result = await response.json();

        if (result.ok) {
            showExcelStatus('✅ 分析完成！', 'success');

            if (resultDiv && markdownReportDiv) {
                resultDiv.classList.add('active');

                let htmlContent = result.markdown_report || '无报告内容';
                htmlContent = htmlContent
                    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/\n/g, '<br>');

                markdownReportDiv.innerHTML = htmlContent;

                if (result.echarts) {
                    console.log('📊 ECharts 代码:', result.echarts);
                }
            }
        } else {
            showExcelStatus(`❌ 分析失败：${result.error || '未知错误'}`, 'error');
        }

    } catch (error) {
        console.error('❌ Excel 上传失败:', error);
        showExcelStatus(`❌ 上传失败：${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '🚀 上传并分析';
    }
}

function showExcelStatus(message, type) {
    const statusDiv = document.getElementById('excelStatus');
    if (!statusDiv) return;

    statusDiv.textContent = message;
    statusDiv.className = type;
    statusDiv.style.display = 'block';

    if (type !== 'info') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

function clearExcelResult() {
    selectedExcelFile = null;

    const fileInfo = document.getElementById('selectedFileInfo');
    const fileName = document.getElementById('selectedFileName');
    const uploadBtn = document.getElementById('uploadExcelBtn');
    const resultDiv = document.getElementById('excelResult');
    const markdownReportDiv = document.getElementById('markdownReport');
    const fileInput = document.getElementById('excelFileInput');

    if (fileInfo) fileInfo.classList.remove('active');
    if (fileName) fileName.textContent = '';
    if (uploadBtn) uploadBtn.disabled = true;
    if (resultDiv) resultDiv.classList.remove('active');
    if (markdownReportDiv) markdownReportDiv.innerHTML = '';
    if (fileInput) fileInput.value = '';

    showExcelStatus('🗑️ 结果已清空', 'info');
}

// ========== 服务洞察功能 - 新增 ==========
function showInsightStatus(message, type) {
    const statusDiv = document.getElementById('insightStatus');
    if (!statusDiv) return;

    statusDiv.textContent = message;
    statusDiv.className = type;
    statusDiv.style.display = 'block';

    if (type !== 'info') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

function handleInsightInputTypeSwitch(type) {
    currentInsightInputType = type;

    const textTab = document.querySelector('.insight-input-tab[data-input-type="text"]');
    const fileTab = document.querySelector('.insight-input-tab[data-input-type="file"]');
    const textSection = document.getElementById('insightTextSection');
    const fileSection = document.getElementById('insightFileSection');

    if (type === 'text') {
        if (textTab) textTab.classList.add('active');
        if (fileTab) fileTab.classList.remove('active');
        if (textSection) textSection.style.display = 'block';
        if (fileSection) fileSection.style.display = 'none';
    } else {
        if (textTab) textTab.classList.remove('active');
        if (fileTab) fileTab.classList.add('active');
        if (textSection) textSection.style.display = 'none';
        if (fileSection) fileSection.style.display = 'block';
    }
}

function handleInsightAudioFileSelect(file) {
    if (!file) return;

    if (file.size > FILE_CONFIG.maxFileSize) {
        showInsightStatus(`⚠️ 文件 "${file.name}" 超过 10MB 限制`, 'error');
        return;
    }

    const fileType = getFileType(file);
    if (fileType !== 'audio') {
        showInsightStatus(`⚠️ 请选择音频文件 (.mp3/.wav/.m4a)`, 'error');
        return;
    }

    selectedInsightAudioFile = file;

    const selectedFileDiv = document.getElementById('insightSelectedFile');
    const selectedFileName = document.getElementById('insightSelectedFileName');
    const analyzeBtn = document.getElementById('analyzeInsightBtn');

    if (selectedFileDiv && selectedFileName) {
        selectedFileDiv.style.display = 'block';
        selectedFileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
    }

    if (analyzeBtn) analyzeBtn.disabled = false;

    showInsightStatus(`✅ 已选择：${file.name}`, 'info');
}

function clearInsightAudioFile() {
    selectedInsightAudioFile = null;

    const selectedFileDiv = document.getElementById('insightSelectedFile');
    const selectedFileName = document.getElementById('insightSelectedFileName');
    const analyzeBtn = document.getElementById('analyzeInsightBtn');
    const fileInput = document.getElementById('insightAudioInput');

    if (selectedFileDiv) selectedFileDiv.style.display = 'none';
    if (selectedFileName) selectedFileName.textContent = '';
    if (analyzeBtn) analyzeBtn.disabled = false;
    if (fileInput) fileInput.value = '';

    showInsightStatus('🗑️ 已清空音频文件', 'info');
}

async function analyzeInsight() {
    const analyzeBtn = document.getElementById('analyzeInsightBtn');
    const resultDiv = document.getElementById('insightResult');
    const reportDiv = document.getElementById('insightReport');

    // 验证输入
    if (currentInsightInputType === 'text') {
        const textInput = document.getElementById('insightTextInput');
        if (!textInput || !textInput.value.trim()) {
            showInsightStatus('⚠️ 请输入对话文本内容', 'error');
            return;
        }
    } else {
        if (!selectedInsightAudioFile) {
            showInsightStatus('⚠️ 请先选择音频文件', 'error');
            return;
        }
    }

    // 禁用按钮，显示加载状态
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '⏳ 分析中...';
    showInsightStatus('🔄 正在分析，请稍候...', 'info');

    if (resultDiv) resultDiv.classList.remove('active');
    if (reportDiv) reportDiv.innerHTML = '';

    const formData = new FormData();

    if (currentInsightInputType === 'text') {
        const textInput = document.getElementById('insightTextInput');
        formData.append('input_type', 'text');
        formData.append('text_content', textInput.value.trim());
    } else {
        formData.append('input_type', 'file');
        formData.append('audio_file', selectedInsightAudioFile);
    }

    try {
        const response = await fetch(`${INSIGHT_BACKEND_CONFIG.baseUrl}${INSIGHT_BACKEND_CONFIG.analyzeEndpoint}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
        }

        const result = await response.json();

        if (result.ok || result.success) {
            showInsightStatus('✅ 分析完成！', 'success');

            if (resultDiv && reportDiv) {
                resultDiv.classList.add('active');

                // 更新统计信息
                if (result.summary) {
                    document.getElementById('insightTotalItems').textContent = result.summary.total_items || 0;
                    document.getElementById('insightMatched').textContent = result.summary.matched || 0;
                    document.getElementById('insightUnmatched').textContent = result.summary.unmatched || 0;
                    document.getElementById('insightHitRate').textContent = result.summary.hit_rate || '0%';
                }

                // 显示报告内容
                let htmlContent = result.markdown_report || result.report || '无报告内容';
                htmlContent = htmlContent
                    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/\n/g, '<br>');

                reportDiv.innerHTML = htmlContent;

                if (result.markdown_report) {
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
                    const filename = `服务质检报告_${timestamp}.md`;
                    reportDiv.innerHTML += `<div style="margin-top: 15px; padding: 10px; background: #f0f4ff; border-radius: 6px; text-align: center;">
                        <a href="javascript:void(0)" onclick="downloadInsightReport()" style="color: #667eea; text-decoration: none; font-weight: 600;">📥 下载完整报告</a>
                    </div>`;
                    window._insightReportContent = result.markdown_report;
                    window._insightReportFilename = filename;
                }
            }
        } else {
            showInsightStatus(`❌ 分析失败：${result.error || '未知错误'}`, 'error');
        }

    } catch (error) {
        console.error('❌ 服务洞察分析失败:', error);
        showInsightStatus(`❌ 分析失败：${error.message}`, 'error');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '🚀 开始分析';
    }
}

function clearInsightResult() {
    // 清空文本输入
    const textInput = document.getElementById('insightTextInput');
    if (textInput) textInput.value = '';

    // 清空音频文件
    clearInsightAudioFile();

    // 清空结果
    const resultDiv = document.getElementById('insightResult');
    const reportDiv = document.getElementById('insightReport');

    if (resultDiv) resultDiv.classList.remove('active');
    if (reportDiv) reportDiv.innerHTML = '';

    // 重置统计
    document.getElementById('insightTotalItems').textContent = '0';
    document.getElementById('insightMatched').textContent = '0';
    document.getElementById('insightUnmatched').textContent = '0';
    document.getElementById('insightHitRate').textContent = '0%';

    showInsightStatus('🗑️ 结果已清空', 'info');
}

function downloadInsightReport() {
    const content = window._insightReportContent;
    const filename = window._insightReportFilename || '服务质检报告.md';

    if (!content) {
        alert('报告内容不存在，请重新分析');
        return;
    }

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ========== 核心优化：中文分词 ==========
function showCrawlStatus(message, type) {
    const statusDiv = document.getElementById('crawlStatus');
    if (!statusDiv) return;

    statusDiv.textContent = message;
    statusDiv.className = `crawl-status ${type}`;
    statusDiv.style.display = 'block';

    if (type !== 'info') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

function escapeHtml(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function showCrawlSection(section) {
    const commentsOutput = document.getElementById('crawlCommentsOutput');
    const reportOutput = document.getElementById('crawlReportOutput');

    if (commentsOutput) commentsOutput.classList.remove('active');
    if (reportOutput) reportOutput.classList.remove('active');

    if (section === 'comments' && commentsOutput) commentsOutput.classList.add('active');
    if (section === 'report' && reportOutput) reportOutput.classList.add('active');
}

function renderCrawlComments(comments) {
    const listDiv = document.getElementById('crawlCommentsList');
    if (!listDiv) return;

    if (!comments || comments.length === 0) {
        listDiv.innerHTML = '<div class="crawl-comment-item">没有可展示的评论。</div>';
        return;
    }

    listDiv.innerHTML = comments.map(item => `
        <div class="crawl-comment-item">
            <div class="crawl-comment-meta">
                车型：${escapeHtml(item.car_name || '未知')}<br>
                评分：${escapeHtml(item.rating || '未知')}<br>
                时间：${escapeHtml(item.published_at || '未知')}
            </div>
            <div class="crawl-comment-content">${escapeHtml(item.content || '')}</div>
        </div>
    `).join('');
}

function renderCrawlReport(result) {
    const reportContent = document.getElementById('crawlReportContent');
    const fileList = document.getElementById('crawlFileList');

    if (reportContent) {
        reportContent.textContent = result?.report_markdown || '暂无报告内容';
    }

    if (fileList) {
        fileList.innerHTML = `
            reviews.xlsx：${escapeHtml(result?.excel_file || '')}<br>
            reviews.json：${escapeHtml(result?.reviews_json_file || '')}<br>
            report.md：${escapeHtml(result?.report_file || '')}<br>
            summary.xlsx：${escapeHtml(result?.summary_excel_file || '')}
        `;
    }
}

async function analyzeCrawlUrl() {
    const analyzeBtn = document.getElementById('analyzeCrawlBtn');
    const urlInput = document.getElementById('crawlUrlInput');
    const maxItemsInput = document.getElementById('crawlMaxItemsInput');
    const toggleActions = document.getElementById('crawlToggleActions');
    const summaryDiv = document.getElementById('crawlSummary');

    const targetUrl = urlInput?.value?.trim() || '';
    const maxItems = Number(maxItemsInput?.value || 20);

    if (!targetUrl) {
        showCrawlStatus('请输入评论页 URL', 'error');
        return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '⏳ 分析中...';
    currentCrawlResult = null;

    if (toggleActions) toggleActions.classList.remove('active');
    if (summaryDiv) summaryDiv.style.display = 'none';

    renderCrawlComments([]);
    renderCrawlReport(null);
    showCrawlSection('');
    showCrawlStatus('正在抓取评论并生成分析报告，请稍等...', 'info');

    try {
        const response = await fetch(`${EXCEL_BACKEND_CONFIG.baseUrl}${CRAWL_BACKEND_CONFIG.analyzeEndpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: targetUrl,
                max_items: maxItems
            })
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            throw new Error(result.error || `HTTP ${response.status}`);
        }

        currentCrawlResult = result;
        document.getElementById('crawlReviewCount').textContent = result.review_count || 0;
        document.getElementById('crawlPreviewCount').textContent = (result.preview_reviews || []).length;

        if (summaryDiv) summaryDiv.style.display = 'grid';
        if (toggleActions) toggleActions.classList.add('active');

        renderCrawlComments(result.preview_reviews || []);
        renderCrawlReport(result);
        showCrawlSection('comments');
        showCrawlStatus('分析完成，可以查看评论或报告。', 'success');
    } catch (error) {
        console.error('评论爬取分析失败:', error);
        showCrawlStatus(`处理失败：${error.message}`, 'error');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '🚀 开始分析';
    }
}

function clearCrawlResult() {
    currentCrawlResult = null;

    const urlInput = document.getElementById('crawlUrlInput');
    const summaryDiv = document.getElementById('crawlSummary');
    const toggleActions = document.getElementById('crawlToggleActions');

    if (urlInput) urlInput.value = '';
    if (summaryDiv) summaryDiv.style.display = 'none';
    if (toggleActions) toggleActions.classList.remove('active');

    document.getElementById('crawlReviewCount').textContent = '0';
    document.getElementById('crawlPreviewCount').textContent = '0';
    renderCrawlComments([]);
    renderCrawlReport(null);
    showCrawlSection('');
    showCrawlStatus('结果已清空', 'info');
}

function tokenize(text) {
    if (!text) return [];
    const cleanText = text.toLowerCase().replace(/\s+/g, '');
    const tokens = [];
    const words = cleanText.match(/[a-z0-9]+/g) || [];
    words.forEach(w => {
        if (w.length >= 2) tokens.push(w);
    });
    const chars = Array.from(cleanText);
    for (let i = 0; i < chars.length - 1; i++) {
        const gram = chars[i] + chars[i + 1];
        if (/[\p{L}\p{N}]/u.test(gram)) {
            tokens.push(gram);
        }
    }
    return tokens;
}

function chunkText(text, title, fileName, chunkSize = 500, overlap = 50) {
    const chunks = [];
    const paragraphs = text.split(/\n+/);
    let currentChunk = "";

    paragraphs.forEach(para => {
        if ((currentChunk + para).length > chunkSize) {
            if (currentChunk) {
                chunks.push({
                    id: Date.now() + Math.random(),
                    title: title,
                    fileName: fileName,
                    content: currentChunk.trim(),
                    source: 'word',
                    uploadDate: new Date().toLocaleDateString(),
                    charCount: currentChunk.length
                });
            }
            currentChunk = para.slice(-overlap) + para;
        } else {
            currentChunk += "\n" + para;
        }
    });

    if (currentChunk && currentChunk.trim().length > 0) {
        chunks.push({
            id: Date.now() + Math.random(),
            title: title,
            fileName: fileName,
            content: currentChunk.trim(),
            source: 'word',
            uploadDate: new Date().toLocaleDateString(),
            charCount: currentChunk.length
        });
    }

    return chunks;
}

function buildSearchIndex() {
    searchIndex = {};
    API_CONFIG.knowledgeBase.forEach((item, idx) => {
        const text = `${item.title} ${item.content}`;
        const tokens = tokenize(text);
        tokens.forEach(token => {
            if (!searchIndex[token]) searchIndex[token] = new Set();
            searchIndex[token].add(idx);
        });
    });

    if (DEBUG_MODE) {
        console.log('📚 索引构建完成，关键词数:', Object.keys(searchIndex).length);
    }
}

function retrieveContext(query, topK = 3) {
    if (!API_CONFIG.ragEnabled || !API_CONFIG.knowledgeBase?.length) return '';

    const queryTokens = tokenize(query);
    if (queryTokens.length === 0) return '';

    const scores = {};
    queryTokens.forEach(token => {
        if (searchIndex[token]) {
            searchIndex[token].forEach(idx => {
                scores[idx] = (scores[idx] || 0) + 5;
            });
        }
    });

    Object.keys(scores).forEach(idx => {
        const text = `${API_CONFIG.knowledgeBase[idx].title} ${API_CONFIG.knowledgeBase[idx].content}`.toLowerCase();
        let count = 0;
        queryTokens.forEach(t => {
            const regex = new RegExp(t, 'g');
            const matches = text.match(regex);
            if (matches) count += matches.length;
        });
        if (count > 0) {
            scores[idx] += count;
        }
    });

    const scoredIds = Object.entries(scores)
        .sort((a, b) => b[1] - a[1])
        .slice(0, topK)
        .map(item => parseInt(item[0]));

    if (scoredIds.length === 0) return '';

    const chunks = scoredIds.map((idx, i) => {
        const item = API_CONFIG.knowledgeBase[idx];
        const sourceInfo = item.fileName ? `📄 ${item.fileName}` : `📝 ${item.title}`;
        return `【参考资料 ${i + 1}｜${sourceInfo}】\n${item.content}`;
    }).join('\n\n');

    return `\n\n📚 店内知识库参考：\n${chunks}\n\n请优先基于上述资料回答客户问题，涉及价格和政策务必准确。`;
}

function getDOMElements() {
    return {
        chatContainer: document.getElementById('chatContainer'),
        messagesContainer: document.getElementById('messages'),
        messageInput: document.getElementById('messageInput'),
        sendBtn: document.getElementById('sendBtn'),
        settingsBtn: document.getElementById('settingsBtn'),
        attachBtn: document.getElementById('attachBtn'),
        fileInput: document.getElementById('fileInput'),
        filePreviewContainer: document.getElementById('filePreviewContainer'),
        chatInputArea: document.getElementById('chatInputArea'),
        excelUploadArea: document.getElementById('excelUploadArea'),
        excelFileInput: document.getElementById('excelFileInput'),
        uploadExcelBtn: document.getElementById('uploadExcelBtn'),
        clearExcelBtn: document.getElementById('clearExcelBtn'),
        // 服务洞察相关元素 - 新增
        insightPanel: document.getElementById('insightPanel'),
        insightTextSection: document.getElementById('insightTextSection'),
        insightFileSection: document.getElementById('insightFileSection'),
        insightTextInput: document.getElementById('insightTextInput'),
        insightFileUpload: document.getElementById('insightFileUpload'),
        insightAudioInput: document.getElementById('insightAudioInput'),
        analyzeInsightBtn: document.getElementById('analyzeInsightBtn'),
        clearInsightBtn: document.getElementById('clearInsightBtn'),
        crawlPanel: document.getElementById('crawlPanel'),
        analyzeCrawlBtn: document.getElementById('analyzeCrawlBtn'),
        clearCrawlBtn: document.getElementById('clearCrawlBtn'),
        showCrawlCommentsBtn: document.getElementById('showCrawlCommentsBtn'),
        showCrawlReportBtn: document.getElementById('showCrawlReportBtn')
    };
}

function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab');
    const chatContainer = document.getElementById('chatContainer');
    const excelPanel = document.getElementById('excelPanel');
    const insightPanel = document.getElementById('insightPanel');
    const crawlPanel = document.getElementById('crawlPanel');
    const chatInputArea = document.getElementById('chatInputArea');
    const filePreviewContainer = document.getElementById('filePreviewContainer');

    tabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        }
    });

    if (tabName === 'chat') {
        if (chatContainer) chatContainer.style.display = 'flex';
        if (excelPanel) excelPanel.classList.remove('active');
        if (insightPanel) insightPanel.classList.remove('active');
        if (crawlPanel) crawlPanel.classList.remove('active');
        if (chatInputArea) chatInputArea.style.display = 'flex';
        if (filePreviewContainer) filePreviewContainer.style.display = 'block';
    } else if (tabName === 'excel') {
        if (chatContainer) chatContainer.style.display = 'none';
        if (excelPanel) excelPanel.classList.add('active');
        if (insightPanel) insightPanel.classList.remove('active');
        if (crawlPanel) crawlPanel.classList.remove('active');
        if (chatInputArea) chatInputArea.style.display = 'none';
        if (filePreviewContainer) filePreviewContainer.style.display = 'none';
    } else if (tabName === 'insight') {
        if (chatContainer) chatContainer.style.display = 'none';
        if (excelPanel) excelPanel.classList.remove('active');
        if (insightPanel) insightPanel.classList.add('active');
        if (crawlPanel) crawlPanel.classList.remove('active');
        if (chatInputArea) chatInputArea.style.display = 'none';
        if (filePreviewContainer) filePreviewContainer.style.display = 'none';
    } else if (tabName === 'crawl') {
        if (chatContainer) chatContainer.style.display = 'none';
        if (excelPanel) excelPanel.classList.remove('active');
        if (insightPanel) insightPanel.classList.remove('active');
        if (crawlPanel) crawlPanel.classList.add('active');
        if (chatInputArea) chatInputArea.style.display = 'none';
        if (filePreviewContainer) filePreviewContainer.style.display = 'none';
    }
}

window.onload = async function () {
    domElements = getDOMElements();

    if (!domElements.chatContainer) {
        console.error('❌ 未找到 chatContainer');
        return;
    }

    domElements.messageInput?.focus();

    domElements.sendBtn?.addEventListener('click', sendMessage);
    domElements.messageInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    domElements.settingsBtn?.addEventListener('click', showSettings);

    domElements.attachBtn?.addEventListener('click', () => {
        domElements.fileInput?.click();
    });
    domElements.fileInput?.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            addAttachments(e.target.files);
            e.target.value = '';
        }
    });

    // Excel 相关事件
    domElements.excelUploadArea?.addEventListener('click', () => {
        domElements.excelFileInput?.click();
    });
    domElements.excelFileInput?.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleExcelFileSelect(e.target.files[0]);
        }
    });
    domElements.uploadExcelBtn?.addEventListener('click', uploadExcelForAnalysis);
    domElements.clearExcelBtn?.addEventListener('click', clearExcelResult);

    // 服务洞察相关事件 - 新增
    document.querySelectorAll('.insight-input-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            handleInsightInputTypeSwitch(tab.dataset.inputType);
        });
    });

    domElements.insightFileUpload?.addEventListener('click', () => {
        domElements.insightAudioInput?.click();
    });
    domElements.insightAudioInput?.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleInsightAudioFileSelect(e.target.files[0]);
        }
    });
    domElements.analyzeInsightBtn?.addEventListener('click', analyzeInsight);
    domElements.clearInsightBtn?.addEventListener('click', clearInsightResult);
    document.getElementById('insightClearFileBtn')?.addEventListener('click', clearInsightAudioFile);

    // 标签页切换
    domElements.analyzeCrawlBtn?.addEventListener('click', analyzeCrawlUrl);
    domElements.clearCrawlBtn?.addEventListener('click', clearCrawlResult);
    domElements.showCrawlCommentsBtn?.addEventListener('click', () => showCrawlSection('comments'));
    domElements.showCrawlReportBtn?.addEventListener('click', () => showCrawlSection('report'));

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchTab(tab.dataset.tab);
        });
    });

    // 加载配置
    try {
        const result = await StorageUtil.get(['aiChatConfig', 'knowledgeBase', 'excelBackendConfig', 'insightBackendConfig']);

        if (result.aiChatConfig) {
            Object.assign(API_CONFIG, result.aiChatConfig);
        }
        if (result.knowledgeBase && Array.isArray(result.knowledgeBase)) {
            API_CONFIG.knowledgeBase = result.knowledgeBase;
        }
        if (result.excelBackendConfig) {
            Object.assign(EXCEL_BACKEND_CONFIG, result.excelBackendConfig);
        }
        if (result.insightBackendConfig) {
            Object.assign(INSIGHT_BACKEND_CONFIG, result.insightBackendConfig);
        }

        buildSearchIndex();

        if (DEBUG_MODE) {
            console.log('💾 配置已加载，知识库条目:', API_CONFIG.knowledgeBase.length);
        }
    } catch (e) {
        console.log('ℹ️ 未找到保存的配置', e);
    }

    messages = [{ role: 'system', content: API_CONFIG.systemPrompt }];

    if (!API_CONFIG.apiKey || API_CONFIG.apiKey.includes('YOUR_') || API_CONFIG.apiKey.length < 10) {
        setTimeout(() => {
            addMessage('👋 欢迎使用 4S 店销售智能助手！', 'ai');
            setTimeout(() => {
                addMessage('⚠️ 请先点击设置图标配置 API Key 并上传车型资料', 'ai');
                showSettings();
            }, 400);
        }, 300);
    } else {
        setTimeout(() => {
            addMessage('👋 您好！我是您的销售助手，随时帮您查询车型、价格和话术。', 'ai');
        }, 300);
    }
};

async function sendMessage() {
    const userInput = domElements.messageInput.value.trim();
    if (!userInput && currentAttachments.length === 0) return;

    addMessage(userInput, 'user', false, currentAttachments);

    domElements.messageInput.value = '';
    domElements.sendBtn.disabled = true;

    const aiMessageDiv = addMessage('', 'ai', true);
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span>•</span><span>•</span><span>•</span>';
    aiMessageDiv.appendChild(typingIndicator);

    let finalUserContent = userInput;

    if (currentAttachments.length > 0) {
        const attachmentInfo = currentAttachments.map(att => {
            if (att.type === 'image') {
                return `📎 图片：${att.name}`;
            } else if (att.content) {
                return `📎 文档 ${att.name} 内容摘要：${att.content.substring(0, 500)}...`;
            }
            return `📎 文件：${att.name}`;
        }).join('\n');

        if (userInput) {
            finalUserContent = `${userInput}\n\n${attachmentInfo}`;
        } else {
            finalUserContent = attachmentInfo;
        }
    }

    let ragContext = '';
    if (API_CONFIG.ragEnabled) {
        ragContext = retrieveContext(finalUserContent, API_CONFIG.ragTopK);
    }

    const baseSystem = API_CONFIG.systemPrompt;
    const finalSystem = ragContext ? `${baseSystem}${ragContext}` : baseSystem;

    const apiMessages = [
        { role: 'system', content: finalSystem },
        ...messages.filter(m => m.role !== 'system'),
        { role: 'user', content: finalUserContent }
    ];

    messages.push({ role: 'user', content: finalUserContent });

    try {
        await callAIStream(aiMessageDiv, typingIndicator, apiMessages);
        currentAttachments = [];
        renderFilePreview();
    } catch (error) {
        console.error('❌ API 调用失败:', error);
        aiMessageDiv.innerHTML = `<span style="color:#ff4444;">❌ 错误：</span><br>${error.message || error}`;
        messages.pop();
    } finally {
        domElements.sendBtn.disabled = false;
        domElements.messageInput.focus();
    }
}

async function callAIStream(messageDiv, typingIndicator, currentMessages = null) {
    const payloadMessages = currentMessages || messages;

    try {
        const response = await fetch(API_CONFIG.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_CONFIG.apiKey.trim()}`
            },
            body: JSON.stringify({
                model: API_CONFIG.model,
                messages: payloadMessages,
                stream: true,
                temperature: API_CONFIG.temperature,
                max_tokens: API_CONFIG.max_tokens
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
        }

        if (typingIndicator) typingIndicator.remove();

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let fullResponse = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed) continue;

                let data = trimmed.startsWith('data:') ? trimmed.slice(5).trim() : trimmed;
                if (data === '[DONE]' || data === '') continue;

                try {
                    const parsed = JSON.parse(data);
                    const content = parsed.choices?.[0]?.delta?.content || '';
                    if (content) {
                        fullResponse += content;
                        updateMessageContent(messageDiv, fullResponse);
                    }
                } catch (e) {
                    console.warn('⚠️ 解析失败:', e.message);
                }
            }
        }

        messages.push({ role: 'assistant', content: fullResponse });

    } catch (error) {
        if (error.message.includes('Failed to fetch')) {
            throw new Error('网络错误：无法连接到 API 服务器');
        }
        throw error;
    }
}

function updateMessageContent(element, content) {
    const safeContent = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');

    element.innerHTML = safeContent;

    if (domElements.messagesContainer) {
        domElements.messagesContainer.scrollTop = domElements.messagesContainer.scrollHeight;
    }
}

function addMessage(content, role, isStreaming = false, attachments = []) {
    if (!domElements.messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    let html = '';

    if (attachments.length > 0 && role === 'user') {
        html += '<div class="message-attachments">';
        attachments.forEach(att => {
            if (att.type === 'image') {
                html += `<div class="message-attachment">
                    <div class="att-info">🖼️ ${att.name} (${formatFileSize(att.size)})</div>
                    <img src="${att.content}" alt="${att.name}">
                </div>`;
            } else {
                html += `<div class="message-attachment">
                    <div class="att-info">${getFileIcon(att.mimeType)} ${att.name} (${formatFileSize(att.size)})</div>
                </div>`;
            }
        });
        html += '</div>';
    }

    if (content) {
        const safeContent = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
        html += safeContent;
    }

    if (!isStreaming) {
        messageDiv.innerHTML = html;
    }

    domElements.messagesContainer.appendChild(messageDiv);
    domElements.messagesContainer.scrollTop = domElements.messagesContainer.scrollHeight;

    return messageDiv;
}

function saveConfigToStorage() {
    buildSearchIndex();
    StorageUtil.set({
        aiChatConfig: API_CONFIG,
        knowledgeBase: API_CONFIG.knowledgeBase,
        excelBackendConfig: EXCEL_BACKEND_CONFIG,
        insightBackendConfig: INSIGHT_BACKEND_CONFIG
    }).then(() => {
        if (DEBUG_MODE) console.log('💾 配置已保存');
    }).catch(err => {
        console.error('💾 配置保存失败:', err);
    });
}

function showSettings() {
    if (!domElements.chatContainer || !domElements.messagesContainer) return;

    const existing = document.querySelector('.settings-panel');
    if (existing) {
        existing.remove();
        return;
    }

    const settingsHtml = `
        <div class="settings-panel">
            <h3 style="margin-bottom:15px;">⚙️ 销售助手配置</h3>
            
            <label>🔑 API Key</label>
            <input type="password" id="apiKeyInput" value="${API_CONFIG.apiKey}" placeholder="输入 API Key">
            
            <label>🌐 API Base URL</label>
            <input type="text" id="apiBaseUrlInput" value="${API_CONFIG.apiUrl.replace('/v1/chat/completions', '')}" placeholder="https://api.example.com">
            
            <label>🤖 模型名称</label>
            <input type="text" id="modelInput" value="${API_CONFIG.model}" placeholder="模型名称">
            
            <label>🔗 Excel 后端地址</label>
            <input type="text" id="excelBackendUrlInput" value="${EXCEL_BACKEND_CONFIG.baseUrl}" placeholder="http://127.0.0.1:8000">
            
            <label>🔍 服务洞察后端地址</label>
            <input type="text" id="insightBackendUrlInput" value="${INSIGHT_BACKEND_CONFIG.baseUrl}" placeholder="http://127.0.0.1:5000">
            
            <div style="margin:20px 0; padding:15px; background:#f8f9fa; border-radius:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <label style="font-weight:600;">📚 车型/价格知识库</label>
                    <label style="font-size:13px;">
                        <input type="checkbox" id="ragSwitch" ${API_CONFIG.ragEnabled ? 'checked' : ''}> 启用 RAG
                    </label>
                </div>
                <div class="file-upload-area" id="wordUploadArea" style="border:2px dashed #ddd; padding:20px; text-align:center; cursor:pointer; border-radius:4px;">
                    <p style="margin:0; color:#666;">📁 点击上传车型手册/价格表 (.docx/.pdf/.txt)</p>
                    <input type="file" id="wordFileInput" accept=".docx,.doc,.pdf,.txt" style="display:none;" multiple>
                </div>
                <div id="uploadStatus" style="margin:10px 0; font-size:13px;"></div>
                <div id="kbList" style="max-height:150px; overflow-y:auto; border:1px solid #eee; border-radius:4px; background:white; margin-top:15px;"></div>
            </div>
            
            <div style="display:flex; gap:12px;">
                <button id="testBtn" style="flex:1; background:#4CAF50; color:white; border:none; padding:10px; border-radius:4px; cursor:pointer;">🧪 测试连接</button>
                <button id="saveBtn" style="flex:1; background:#2196F3; color:white; border:none; padding:10px; border-radius:4px; cursor:pointer;">💾 保存配置</button>
            </div>
            <div id="testResult" style="margin-top:15px; padding:10px; border-radius:4px; display:none; font-size:14px;"></div>
        </div>
    `;

    const panel = document.createElement('div');
    panel.innerHTML = settingsHtml;
    domElements.chatContainer.insertBefore(panel, domElements.messagesContainer);
    domElements.messagesContainer.scrollTop = 0;

    const uploadArea = document.getElementById('wordUploadArea');
    const fileInput = document.getElementById('wordFileInput');
    const uploadStatus = document.getElementById('uploadStatus');

    uploadArea?.addEventListener('click', () => fileInput?.click());

    fileInput?.addEventListener('change', async (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        uploadStatus.innerHTML = '⏳ 正在解析并分块...';

        for (const file of files) {
            try {
                const result = await parseWordDocument(file);
                const chunks = chunkText(result.text, file.name.replace(/\.(docx|doc|pdf|txt)$/i, ''), file.name);
                chunks.forEach(chunk => {
                    API_CONFIG.knowledgeBase.push(chunk);
                });
                uploadStatus.innerHTML += `<br>✅ ${file.name} (生成 ${chunks.length} 个片段)`;
            } catch (err) {
                console.error(err);
                uploadStatus.innerHTML += `<br>❌ ${file.name} (${err.message})`;
            }
        }
        saveConfigToStorage();
        renderKbList();
        fileInput.value = '';
    });

    function renderKbList() {
        const list = document.getElementById('kbList');
        if (!list) return;

        if (!API_CONFIG.knowledgeBase.length) {
            list.innerHTML = '<div style="padding:10px; color:#999; text-align:center;">暂无文档</div>';
            return;
        }

        list.innerHTML = API_CONFIG.knowledgeBase.map((item, idx) => `
            <div style="padding:10px; border-bottom:1px solid #f0f0f0; display:flex; justify-content:space-between; align-items:center;">
                <div style="flex:1; min-width:0;">
                    <div style="margin-bottom:4px;">
                        <span style="display:inline-block; background:#2196F3; color:white; padding:2px 6px; border-radius:4px; font-size:10px; margin-right:6px;">${item.source === 'word' ? '📄 文档' : '📝 文本'}</span>
                        <span style="font-weight:500; color:#333;">${item.title || '未命名'}</span>
                    </div>
                    <div style="font-size:11px; color:#666;">📅 ${item.uploadDate || '未知'} | 🔤 ${item.charCount || 0} 字符</div>
                </div>
                <button data-idx="${idx}" class="del-kb" style="color:#ff4444; background:none; border:none; cursor:pointer; padding:4px 8px;">删除</button>
            </div>
        `).join('');

        list.querySelectorAll('.del-kb').forEach(btn => {
            btn.onclick = () => {
                API_CONFIG.knowledgeBase.splice(parseInt(btn.dataset.idx), 1);
                saveConfigToStorage();
                renderKbList();
            };
        });
    }

    document.getElementById('ragSwitch')?.addEventListener('change', (e) => {
        API_CONFIG.ragEnabled = e.target.checked;
        saveConfigToStorage();
    });

    document.getElementById('testBtn').addEventListener('click', async () => {
        const btn = document.getElementById('testBtn');
        const resultDiv = document.getElementById('testResult');
        btn.disabled = true;
        btn.innerHTML = '⏳ 测试中...';
        resultDiv.style.display = 'block';

        const apiKey = document.getElementById('apiKeyInput').value.trim();
        const baseUrl = document.getElementById('apiBaseUrlInput').value.trim().replace(/\/+$/, '');
        const model = document.getElementById('modelInput').value.trim();

        try {
            const response = await fetch(`${baseUrl}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: model,
                    messages: [{ role: 'user', content: '测试' }],
                    max_tokens: 20
                })
            });

            if (response.ok) {
                resultDiv.style.background = '#d4edda';
                resultDiv.style.color = '#155724';
                resultDiv.innerHTML = '✅ 连接成功！';
            } else {
                resultDiv.style.background = '#f8d7da';
                resultDiv.style.color = '#721c24';
                resultDiv.innerHTML = `❌ 请求失败 (${response.status})`;
            }
        } catch (error) {
            resultDiv.style.background = '#f8d7da';
            resultDiv.style.color = '#721c24';
            resultDiv.innerHTML = `❌ ${error.message}`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = '🧪 测试连接';
        }
    });

    document.getElementById('saveBtn').addEventListener('click', () => {
        const apiKey = document.getElementById('apiKeyInput').value.trim();
        const baseUrl = document.getElementById('apiBaseUrlInput').value.trim().replace(/\/+$/, '');
        const model = document.getElementById('modelInput').value.trim();
        const excelBackendUrl = document.getElementById('excelBackendUrlInput').value.trim().replace(/\/+$/, '');
        const insightBackendUrl = document.getElementById('insightBackendUrlInput').value.trim().replace(/\/+$/, '');

        if (!apiKey || !baseUrl || !model) {
            alert('⚠️ 请填写完整配置');
            return;
        }

        API_CONFIG.apiKey = apiKey;
        API_CONFIG.model = model;
        API_CONFIG.apiUrl = `${baseUrl}/v1/chat/completions`;
        API_CONFIG.ragEnabled = document.getElementById('ragSwitch')?.checked || false;

        if (excelBackendUrl) {
            EXCEL_BACKEND_CONFIG.baseUrl = excelBackendUrl;
        }

        if (insightBackendUrl) {
            INSIGHT_BACKEND_CONFIG.baseUrl = insightBackendUrl;
        }

        saveConfigToStorage();
        document.querySelector('.settings-panel')?.remove();
        addMessage('✅ 配置已更新！销售助手已就绪。', 'ai');
    });

    setTimeout(renderKbList, 50);
}

async function parseWordDocument(file) {
    if (typeof mammoth === 'undefined') {
        throw new Error('缺少 mammoth.js 库，请确保已下载 mammoth.browser.min.js 到扩展目录');
    }

    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = function (event) {
            const arrayBuffer = event.target.result;
            mammoth.extractRawText({ arrayBuffer: arrayBuffer })
                .then(result => {
                    if (!result.value || result.value.trim().length === 0) {
                        reject(new Error('文档内容为空'));
                    } else {
                        resolve({ text: result.value, messages: result.messages });
                    }
                })
                .catch(err => reject(err));
        };
        reader.onerror = () => reject(new Error('文件读取失败'));
        reader.readAsArrayBuffer(file);
    });
}
