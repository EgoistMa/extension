function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, s => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[s]));
}

function renderProjectInfo(projectInfo) {
  const container = document.getElementById('project-info');
  if (!container) {
    return;
  }
  if (!projectInfo || !projectInfo.product_id) {
    container.innerHTML = '<div style="color:#6B7280;">暂无（请先在百应商品页点击“下载图片”）</div>';
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
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      chrome.storage.local.remove('baiying_project_info', () => {
        renderProjectInfo(null);
      });
    });
  }
});
