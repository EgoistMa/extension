/**
 * Popup脚本 - 显示和管理产品列表
 */

let allProducts = [];
let isSmartMode = false;

// 显示提示信息
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2000);
}

// 渲染产品表格
function renderProducts(products) {
  const content = document.getElementById('content');
  const countEl = document.getElementById('productCount');

  countEl.textContent = `${products.length} 个产品`;

  if (products.length === 0) {
    content.innerHTML = `
      <div class="empty-state">
        <div class="icon">📦</div>
        <div>未找到产品</div>
        <div style="margin-top: 8px; font-size: 12px;">请确保在百应选品广场页面使用此插件</div>
      </div>
    `;
    return;
  }

  // 检查是否有综合得分（智能模式）
  const hasScore = products.length > 0 && products[0].totalScore !== undefined;

  let html = `
    <table class="product-table">
      <thead>
        <tr>
          <th style="width: 30px">#</th>
          <th>品名</th>
          <th style="width: 50px">佣金</th>
          <th style="width: 55px">赚</th>
          <th style="width: 50px">价格</th>
          <th style="width: 50px">月销</th>
          <th style="width: 40px">评分</th>
          ${hasScore ? '<th style="width: 45px">综合</th>' : ''}
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

// 从当前页面获取产品数据
async function fetchProducts() {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">正在解析产品...</div>';

  try {
    // 获取当前标签页
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url || !tab.url.includes('buyin.jinritemai.com')) {
      content.innerHTML = `
        <div class="empty-state">
          <div class="icon">⚠️</div>
          <div>请在百应选品广场页面使用</div>
          <div style="margin-top: 8px; font-size: 12px;">访问 buyin.jinritemai.com 后再试</div>
        </div>
      `;
      return;
    }

    // 向content script发送消息获取产品数据
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'parseProducts' });

    if (response && response.products) {
      allProducts = response.products;
      renderProducts(allProducts);
    } else {
      throw new Error('No products found');
    }
  } catch (error) {
    console.error('Error fetching products:', error);
    content.innerHTML = `
      <div class="empty-state">
        <div class="icon">❌</div>
        <div>获取产品失败</div>
        <div style="margin-top: 8px; font-size: 12px;">请刷新页面后重试</div>
      </div>
    `;
  }
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
  let text = '品名\t佣金比例\t佣金赚\t价格\t月销\t店铺评分' + (hasScore ? '\t综合得分' : '') + '\n';
  allProducts.forEach(p => {
    text += `${p.name || '-'}\t${p.commission_rate || '-'}\t${p.commission_amount || '-'}\t${p.price || '-'}\t${p.monthly_sales || '-'}\t${p.shop_score || '-'}`;
    if (hasScore) text += `\t${p.totalScore?.toFixed(1) || '-'}`;
    text += '\n';
  });

  navigator.clipboard.writeText(text).then(() => {
    showToast(`已复制 ${allProducts.length} 个产品`);
  }).catch(err => {
    console.error('Copy failed:', err);
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

  // BOM for UTF-8
  let csv = '\ufeff品名,佣金比例,佣金赚,价格,月销,店铺评分,店铺' + (hasScore ? ',综合得分' : '') + '\n';

  allProducts.forEach(p => {
    const name = (p.name || '').replace(/,/g, '，').replace(/"/g, '""');
    const rate = p.commission_rate || '';
    const amount = p.commission_amount || '';
    const price = p.price || '';
    const sales = p.monthly_sales || '';
    const score = p.shop_score || '';
    const shop = (p.shop_name || '').replace(/,/g, '，').replace(/"/g, '""');
    const totalScore = p.totalScore !== undefined ? p.totalScore.toFixed(1) : '';

    csv += `"${name}",${rate},${amount},${price},${sales},${score},"${shop}"`;
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

// 智能推荐 - 获取Top产品
async function fetchTopProducts() {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">正在智能分析...</div>';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url || !tab.url.includes('buyin.jinritemai.com')) {
      showToast('请在百应选品页面使用');
      return;
    }

    // 获取权重设置
    const commissionWeight = parseInt(document.getElementById('commissionWeight').value) / 100;
    const salesWeight = parseInt(document.getElementById('salesWeight').value) / 100;
    const scoreWeight = parseInt(document.getElementById('scoreWeight').value) / 100;
    const topCount = parseInt(document.getElementById('topCount').value);

    // 归一化权重
    const total = commissionWeight + salesWeight + scoreWeight;
    const weights = {
      commission: commissionWeight / total,
      sales: salesWeight / total,
      score: scoreWeight / total
    };

    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'getTopProducts',
      count: topCount,
      weights: weights
    });

    if (response && response.products) {
      allProducts = response.products;
      isSmartMode = true;
      renderProducts(allProducts);
      showToast(`已筛选出 Top ${topCount || '全部'} 推荐产品`);
    }
  } catch (error) {
    console.error('Error:', error);
    showToast('分析失败，请刷新重试');
  }
}

// 更新权重显示
function updateWeightDisplay() {
  document.getElementById('commissionVal').textContent = document.getElementById('commissionWeight').value + '%';
  document.getElementById('salesVal').textContent = document.getElementById('salesWeight').value + '%';
  document.getElementById('scoreVal').textContent = document.getElementById('scoreWeight').value + '%';
}

// 初始化事件监听
document.addEventListener('DOMContentLoaded', () => {
  // 加载产品
  fetchProducts();

  // 刷新按钮
  document.getElementById('refreshBtn').addEventListener('click', () => {
    isSmartMode = false;
    fetchProducts();
  });

  // 复制按钮
  document.getElementById('copyBtn').addEventListener('click', copyToClipboard);

  // 导出按钮
  document.getElementById('exportBtn').addEventListener('click', exportCSV);

  // 搜索框
  document.getElementById('searchBox').addEventListener('input', (e) => {
    filterProducts(e.target.value);
  });

  // 智能推荐按钮 - 显示/隐藏面板
  document.getElementById('smartBtn').addEventListener('click', () => {
    const panel = document.getElementById('smartPanel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  });

  // 关闭面板按钮
  document.getElementById('closePanelBtn').addEventListener('click', () => {
    document.getElementById('smartPanel').style.display = 'none';
  });

  // 权重滑块事件
  document.getElementById('commissionWeight').addEventListener('input', updateWeightDisplay);
  document.getElementById('salesWeight').addEventListener('input', updateWeightDisplay);
  document.getElementById('scoreWeight').addEventListener('input', updateWeightDisplay);

  // 应用推荐按钮
  document.getElementById('applySmartBtn').addEventListener('click', () => {
    document.getElementById('smartPanel').style.display = 'none';
    fetchTopProducts();
  });
});
