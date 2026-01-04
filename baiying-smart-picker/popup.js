/**
 * 百应智能选品 - Popup Script
 */

let allProducts = [];
let isSmartMode = false;
let autoSendTimer = null;
let countdownInterval = null;

// 显示提示
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}

// 更新状态栏
function updateStatusBar(type, icon, text) {
  const bar = document.getElementById('statusBar');
  const iconEl = document.getElementById('statusIcon');
  const textEl = document.getElementById('statusText');

  bar.className = 'status-bar ' + type;
  bar.style.display = 'flex';
  iconEl.textContent = icon;
  textEl.textContent = text;
}

// 隐藏状态栏
function hideStatusBar() {
  document.getElementById('statusBar').style.display = 'none';
}

// 渲染产品表格
function renderProducts(products) {
  const content = document.getElementById('content');
  const countEl = document.getElementById('productCount');

  countEl.textContent = `${products.length} 个产品`;

  if (products.length === 0) {
    content.innerHTML = `
      <div style="padding: 40px; text-align: center; color: #999;">
        <div style="font-size: 40px; margin-bottom: 12px;">📦</div>
        <div>未找到产品</div>
      </div>
    `;
    return;
  }

  const hasScore = products.length > 0 && products[0].totalScore !== undefined;

  let html = `
    <table class="product-table">
      <thead>
        <tr>
          <th style="width: 28px">#</th>
          <th>品名</th>
          <th style="width: 45px">佣金</th>
          <th style="width: 50px">赚</th>
          <th style="width: 45px">价格</th>
          <th style="width: 45px">月销</th>
          <th style="width: 38px">评分</th>
          ${hasScore ? '<th style="width: 40px">综合</th>' : ''}
        </tr>
      </thead>
      <tbody>
  `;

  products.forEach((product, index) => {
    const name = product.name || '-';
    const rate = product.commission_rate || '-';
    const amount = product.commission_amount || '-';
    const price = product.price || '-';
    const sales = product.monthly_sales || '-';
    const score = product.shop_score || '-';
    const totalScore = product.totalScore !== undefined ? product.totalScore.toFixed(1) : '';

    html += `
      <tr>
        <td style="color: #999">${index + 1}</td>
        <td class="product-name" title="${name}">${name}</td>
        <td class="commission-rate">${rate}</td>
        <td class="commission-amount">${amount}</td>
        <td class="price">${price}</td>
        <td class="sales">${sales}</td>
        <td class="score">${score}</td>
        ${hasScore ? `<td class="total-score">${totalScore}</td>` : ''}
      </tr>
    `;
  });

  html += '</tbody></table>';
  content.innerHTML = html;
}

// 检查页面状态
async function checkPageStatus() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url || !tab.url.includes('buyin.jinritemai.com')) {
      // 显示欢迎界面
      document.getElementById('welcomePanel').style.display = 'block';
      document.getElementById('productPanel').style.display = 'none';
      document.getElementById('statusDot').classList.remove('online');
      return false;
    }

    // 检查页面产品
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'checkPage' });

    if (response && response.isProductPage && response.productCount > 0) {
      // 显示产品面板
      document.getElementById('welcomePanel').style.display = 'none';
      document.getElementById('productPanel').style.display = 'block';
      document.getElementById('statusDot').classList.add('online');
      return true;
    } else {
      document.getElementById('welcomePanel').style.display = 'block';
      document.getElementById('productPanel').style.display = 'none';
      document.getElementById('statusDot').classList.remove('online');
      return false;
    }
  } catch (error) {
    console.error('检查页面状态失败:', error);
    document.getElementById('welcomePanel').style.display = 'block';
    document.getElementById('productPanel').style.display = 'none';
    return false;
  }
}

// 获取产品数据
async function fetchProducts() {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">正在解析产品...</div>';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'parseProducts' });

    if (response && response.products) {
      allProducts = response.products;
      renderProducts(allProducts);

      // 自动发送倒计时
      startAutoSendCountdown();
    } else {
      throw new Error('No products');
    }
  } catch (error) {
    console.error('获取产品失败:', error);
    content.innerHTML = `
      <div style="padding: 40px; text-align: center; color: #999;">
        <div style="font-size: 40px; margin-bottom: 12px;">❌</div>
        <div>获取产品失败，请刷新页面后重试</div>
      </div>
    `;
  }
}

// 自动发送倒计时
function startAutoSendCountdown() {
  let countdown = 3;

  updateStatusBar('warning', '⏳', `将在 ${countdown} 秒后自动发送到本地服务...`);

  countdownInterval = setInterval(() => {
    countdown--;
    if (countdown > 0) {
      updateStatusBar('warning', '⏳', `将在 ${countdown} 秒后自动发送到本地服务...`);
    } else {
      clearInterval(countdownInterval);
      sendToServer();
    }
  }, 1000);
}

// 发送到服务器
async function sendToServer() {
  const serverUrl = document.getElementById('serverUrl').value;

  updateStatusBar('', '📤', '正在发送到本地服务...');

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // 获取权重设置
    const weights = getWeights();
    const topCount = parseInt(document.getElementById('topCount').value);

    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'sendToServer',
      weights: weights,
      count: topCount,
      serverUrl: serverUrl
    });

    if (response && response.sendResult && response.sendResult.success) {
      updateStatusBar('success', '✅', `已成功发送 ${response.topProducts.length} 个产品到本地服务`);
      allProducts = response.topProducts;
      renderProducts(allProducts);
      showToast('发送成功！');
    } else {
      const msg = response?.sendResult?.message || '发送失败';
      updateStatusBar('error', '❌', `发送失败: ${msg}`);
      showToast('发送失败: ' + msg);
    }
  } catch (error) {
    console.error('发送失败:', error);
    updateStatusBar('error', '❌', `发送失败: ${error.message}`);
    showToast('发送失败');
  }
}

// 获取权重设置
function getWeights() {
  const commissionWeight = parseInt(document.getElementById('commissionWeight').value) / 100;
  const salesWeight = parseInt(document.getElementById('salesWeight').value) / 100;
  const scoreWeight = parseInt(document.getElementById('scoreWeight').value) / 100;

  const total = commissionWeight + salesWeight + scoreWeight;
  return {
    commission: commissionWeight / total,
    sales: salesWeight / total,
    score: scoreWeight / total
  };
}

// 智能推荐
async function fetchTopProducts() {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">正在智能分析...</div>';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    const weights = getWeights();
    const topCount = parseInt(document.getElementById('topCount').value);

    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'getTopProducts',
      count: topCount,
      weights: weights
    });

    if (response && response.products) {
      allProducts = response.products;
      isSmartMode = true;
      renderProducts(allProducts);
      showToast(`已筛选 Top ${topCount || '全部'} 推荐产品`);
    }
  } catch (error) {
    console.error('智能推荐失败:', error);
    showToast('分析失败');
  }
}

// 更新权重显示
function updateWeightDisplay() {
  document.getElementById('commissionVal').textContent = document.getElementById('commissionWeight').value + '%';
  document.getElementById('salesVal').textContent = document.getElementById('salesWeight').value + '%';
  document.getElementById('scoreVal').textContent = document.getElementById('scoreWeight').value + '%';
}

// 搜索过滤
function filterProducts(keyword) {
  if (!keyword) {
    renderProducts(allProducts);
    return;
  }
  const filtered = allProducts.filter(p =>
    p.name && p.name.toLowerCase().includes(keyword.toLowerCase())
  );
  renderProducts(filtered);
}

// 复制到剪贴板
function copyToClipboard() {
  if (allProducts.length === 0) {
    showToast('没有产品可复制');
    return;
  }

  const hasScore = allProducts[0].totalScore !== undefined;
  let text = '品名\t佣金比例\t佣金赚\t价格\t月销\t评分' + (hasScore ? '\t综合得分' : '') + '\n';

  allProducts.forEach(p => {
    text += `${p.name || '-'}\t${p.commission_rate || '-'}\t${p.commission_amount || '-'}\t${p.price || '-'}\t${p.monthly_sales || '-'}\t${p.shop_score || '-'}`;
    if (hasScore) text += `\t${p.totalScore?.toFixed(1) || '-'}`;
    text += '\n';
  });

  navigator.clipboard.writeText(text).then(() => {
    showToast(`已复制 ${allProducts.length} 个产品`);
  }).catch(() => {
    showToast('复制失败');
  });
}

// 导出CSV
function exportCSV() {
  if (allProducts.length === 0) {
    showToast('没有产品可导出');
    return;
  }

  const hasScore = allProducts[0].totalScore !== undefined;
  let csv = '\ufeff品名,佣金比例,佣金赚,价格,月销,评分,店铺' + (hasScore ? ',综合得分' : '') + '\n';

  allProducts.forEach(p => {
    const name = (p.name || '').replace(/,/g, '，').replace(/"/g, '""');
    const shop = (p.shop_name || '').replace(/,/g, '，').replace(/"/g, '""');
    const totalScore = p.totalScore !== undefined ? p.totalScore.toFixed(1) : '';

    csv += `"${name}",${p.commission_rate || ''},${p.commission_amount || ''},${p.price || ''},${p.monthly_sales || ''},${p.shop_score || ''},"${shop}"`;
    if (hasScore) csv += `,${totalScore}`;
    csv += '\n';
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `百应选品_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);

  showToast(`已导出 ${allProducts.length} 个产品`);
}

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
  // 检查页面状态
  const isOnPage = await checkPageStatus();

  if (isOnPage) {
    fetchProducts();
  }

  // 事件绑定
  document.getElementById('refreshBtn').addEventListener('click', () => {
    clearInterval(countdownInterval);
    isSmartMode = false;
    hideStatusBar();
    fetchProducts();
  });

  document.getElementById('smartBtn').addEventListener('click', () => {
    const panel = document.getElementById('smartPanel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  });

  document.getElementById('closePanelBtn').addEventListener('click', () => {
    document.getElementById('smartPanel').style.display = 'none';
  });

  document.getElementById('applySmartBtn').addEventListener('click', () => {
    document.getElementById('smartPanel').style.display = 'none';
    clearInterval(countdownInterval);
    fetchTopProducts();
  });

  document.getElementById('sendBtn').addEventListener('click', () => {
    clearInterval(countdownInterval);
    sendToServer();
  });

  document.getElementById('copyBtn').addEventListener('click', copyToClipboard);
  document.getElementById('exportBtn').addEventListener('click', exportCSV);

  document.getElementById('searchBox').addEventListener('input', (e) => {
    filterProducts(e.target.value);
  });

  // 权重滑块
  document.getElementById('commissionWeight').addEventListener('input', updateWeightDisplay);
  document.getElementById('salesWeight').addEventListener('input', updateWeightDisplay);
  document.getElementById('scoreWeight').addEventListener('input', updateWeightDisplay);

  // 前往百应按钮
  document.getElementById('goBaiyingBtn').addEventListener('click', () => {
    window.close();
  });
});
