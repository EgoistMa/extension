function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, s => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[s]));
}

function slugifyKeyword(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'prototype';
}

function createProjectInfoFromInput(rawInput) {
  const title = rawInput.trim();
  const slug = slugifyKeyword(title || 'prototype');
  return {
    'product_id': `prototype_${slug}_${Date.now()}`,
    'product_name': title,
    'cover': ''
  };
}

function renderProjectInfo(projectInfo) {
  const container = document.getElementById('project-info');
  if (!container) {
    return;
  }
  if (!projectInfo || !projectInfo.product_id) {
    // 原提示：暂无（请先在百应商品页点击“下载图片”）
    container.innerHTML = '<div style="color:#6B7280;">暂无（请先在上方输入关键词创建上下文）</div>';
    return;
  }
  const coverHtml = projectInfo.cover ? `<div style="margin-top:8px;"><img src="${escapeHtml(projectInfo.cover)}" style="max-width: 100%; border-radius: 8px;" /></div>` : '';
  container.innerHTML = `
    <div><b>商品ID：</b>${escapeHtml(projectInfo.product_id)}</div>
    <div style="margin-top:4px;"><b>名称：</b>${escapeHtml(projectInfo.product_name || '')}</div>
    ${coverHtml}
  `;
}

document.addEventListener('DOMContentLoaded', async () => {
  const manifest = chrome.runtime.getManifest();
  const versionEl = document.getElementById('version_name');
  if (versionEl) {
    versionEl.textContent = manifest?.version || 'unknown';
  }

  chrome.storage.local.get('baiying_project_info', result => {
    renderProjectInfo(result?.baiying_project_info);
  });

  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'local' && changes.baiying_project_info) {
      renderProjectInfo(changes.baiying_project_info.newValue);
    }
  });

  const clearBtn = document.getElementById('clear-project-btn');
  const manualInput = document.getElementById('manual-project-name');
  const manualBtn = document.getElementById('save-project-btn');
  const manualStatus = document.getElementById('manual-project-status');
  const draftsRootInput = document.getElementById('concat-drafts-root');
  const outputDirInput = document.getElementById('concat-output-dir');
  const jobIdInput = document.getElementById('concat-job-id');
  const canvasWidthInput = document.getElementById('concat-canvas-width');
  const canvasHeightInput = document.getElementById('concat-canvas-height');
  const fpsSelect = document.getElementById('concat-fps');
  const maxSecondsInput = document.getElementById('concat-max-seconds');
  const concatSaveBtn = document.getElementById('concat-save-btn');
  const concatHealthBtn = document.getElementById('concat-health-btn');
  const concatStatus = document.getElementById('concat-status');

  const setManualStatus = (message, type = 'muted') => {
    if (!manualStatus) {
      return;
    }
    const colorMap = {
      'success': '#059669',
      'error': '#B91C1C',
      'muted': '#6B7280'
    };
    manualStatus.textContent = message;
    manualStatus.style.color = colorMap[type] || colorMap.muted;
  };

  const setConcatStatus = (message, type = 'muted') => {
    if (!concatStatus) {
      return;
    }
    const colorMap = {
      'success': '#059669',
      'error': '#B91C1C',
      'muted': '#6B7280'
    };
    concatStatus.textContent = message;
    concatStatus.style.color = colorMap[type] || colorMap.muted;
  };

  const loadConcatConfig = () => {
    chrome.storage.local.get('auto_concat_config', result => {
      const config = result?.auto_concat_config || {};
      if (draftsRootInput) draftsRootInput.value = config.draftsRoot || '';
      if (outputDirInput) outputDirInput.value = config.outputDir || '';
      if (jobIdInput) jobIdInput.value = config.jobId || '';
      if (canvasWidthInput) canvasWidthInput.value = config.canvasWidth || 1080;
      if (canvasHeightInput) canvasHeightInput.value = config.canvasHeight || 1920;
      if (fpsSelect) fpsSelect.value = config.fps || '30';
      if (maxSecondsInput) maxSecondsInput.value = config.maxEachSeconds || '';
    });
  };

  const collectConcatConfig = () => ({
    'draftsRoot': draftsRootInput?.value.trim() || '',
    'outputDir': outputDirInput?.value.trim() || '',
    'jobId': jobIdInput?.value.trim() || '',
    'canvasWidth': parseInt(canvasWidthInput?.value, 10) || 1080,
    'canvasHeight': parseInt(canvasHeightInput?.value, 10) || 1920,
    'fps': fpsSelect?.value || '30',
    'maxEachSeconds': maxSecondsInput?.value ? parseInt(maxSecondsInput.value, 10) : ''
  });

  const saveConcatConfig = () => {
    const config = collectConcatConfig();
    if (!config.draftsRoot || !config.outputDir) {
      setConcatStatus('请填写草稿根目录与输出目录。', 'error');
      return;
    }
    chrome.storage.local.set({
      'auto_concat_config': config
    }, () => {
      setConcatStatus('已保存自动剪辑设置。', 'success');
    });
  };

  const testConcatHealth = () => {
    setConcatStatus('正在检测本地服务...', 'muted');
    chrome.runtime.sendMessage({
      'action': 'testConcatHealth'
    }, response => {
      if (chrome.runtime.lastError) {
        setConcatStatus('检测失败：' + chrome.runtime.lastError.message, 'error');
        return;
      }
      if (response?.success && response?.data?.ok) {
        setConcatStatus('服务正常，可以开始自动剪辑。', 'success');
      } else {
        setConcatStatus('服务不可用：' + (response?.error || '未知错误'), 'error');
      }
    });
  };

  loadConcatConfig();

  const startAutoDownloadFlow = keyword => {
    if (!keyword) {
      return;
    }
    setManualStatus('正在打开抖音并触发自动下载...', 'muted');
    chrome.runtime.sendMessage({
      'action': 'openDouyinSearch',
      'keyword': keyword
    }, response => {
      if (chrome.runtime.lastError) {
        setManualStatus('启动失败：' + chrome.runtime.lastError.message, 'error');
        return;
      }
      if (response?.success) {
        setManualStatus('已打开抖音，自动下载进行中，请稍候…', 'success');
      } else {
        setManualStatus('打开抖音失败：' + (response?.error || '未知错误'), 'error');
      }
    });
  };

  const handleManualSubmit = () => {
    if (!manualInput) {
      return;
    }
    if (manualBtn) {
      manualBtn.disabled = true;
    }
    const rawValue = manualInput.value.trim();
    if (!rawValue) {
      setManualStatus('请输入一个可识别的关键词。', 'error');
      manualInput.focus();
      if (manualBtn) {
        manualBtn.disabled = false;
      }
      return;
    }
    const projectInfo = createProjectInfoFromInput(rawValue);
    chrome.storage.local.set({
      'baiying_project_info': projectInfo
    }, () => {
      setManualStatus(`已创建上下文：${projectInfo.product_id}`, 'success');
      manualInput.value = '';
      renderProjectInfo(projectInfo);
      startAutoDownloadFlow(rawValue);
      if (manualBtn) {
        manualBtn.disabled = false;
      }
    });
  };

  if (manualBtn && manualInput) {
    manualBtn.addEventListener('click', handleManualSubmit);
    manualInput.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        event.preventDefault();
        handleManualSubmit();
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      chrome.storage.local.remove('baiying_project_info', () => {
        renderProjectInfo(null);
        setManualStatus('已清除上下文。', 'muted');
      });
    });
  }

  if (concatSaveBtn) {
    concatSaveBtn.addEventListener('click', saveConcatConfig);
  }
  if (concatHealthBtn) {
    concatHealthBtn.addEventListener('click', testConcatHealth);
  }
});
