/**
 * 百应选品广场产品解析器
 * 自动提取页面中的产品信息：品名、佣金百分比、佣金赚
 */

// 解析产品信息
function parseBaiyingProducts() {
  const products = [];

  // 查找所有产品包装元素
  const wrapperElements = document.querySelectorAll('[class*="index_module__wrapper___"]');

  wrapperElements.forEach((wrapper) => {
    const text = wrapper.textContent || '';

    // 检查是否包含佣金信息
    if (!text.includes('赚')) {
      return;
    }

    const product = {};

    // 提取产品名称
    const titleElem = wrapper.querySelector('[class*="index_module__luckyTitle___"], [class*="index_module__oneLine___"]');
    if (titleElem) {
      product.name = titleElem.textContent.trim();
    }

    // 提取佣金百分比
    const ratioElem = wrapper.querySelector('[class*="index_module__cosratio___"]');
    if (ratioElem) {
      product.commission_rate = ratioElem.textContent.trim() + '%';
    }

    // 提取佣金金额
    const feeElem = wrapper.querySelector('[class*="index_module__cosFee___"]');
    if (feeElem) {
      const feeText = feeElem.textContent.trim();
      const match = feeText.match(/[¥￥]?(\d+\.?\d*)/);
      if (match) {
        product.commission_amount = '¥' + match[1];
      }
    }

    // 提取价格
    const priceElem = wrapper.querySelector('[class*="index_module__price___"]');
    if (priceElem) {
      const priceText = priceElem.textContent.trim();
      const match = priceText.match(/[¥￥](\d+\.?\d*)/);
      if (match) {
        product.price = '¥' + match[1];
      }
    }

    // 提取店铺名称
    const shopElem = wrapper.querySelector('[class*="index_module__shopName___"]');
    if (shopElem) {
      product.shop_name = shopElem.textContent.trim();
    }

    // 提取销量
    const salesElem = wrapper.querySelector('[class*="index_module__priceAndSales___"]');
    if (salesElem) {
      const salesText = salesElem.textContent.trim();
      const salesMatch = salesText.match(/月销\s*([\d,]+)/);
      if (salesMatch) {
        product.monthly_sales = salesMatch[1].replace(/,/g, '');
      }
    }

    // 提取店铺评分
    const scoreElem = wrapper.querySelector('[class*="index_module__score___"]');
    if (scoreElem) {
      product.shop_score = scoreElem.textContent.trim();
    }

    // 只添加有效数据
    if (product.name && (product.commission_amount || product.commission_rate)) {
      products.push(product);
    }
  });

  return products;
}

// 去重函数
function deduplicateProducts(products) {
  const seen = new Set();
  return products.filter(p => {
    const key = `${p.name}-${p.commission_amount}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

/**
 * 计算产品综合得分
 * @param {Object} product - 产品对象
 * @param {Object} weights - 权重配置 { commission: 0.4, sales: 0.35, score: 0.25 }
 * @returns {number} 综合得分 (0-100)
 */
function calculateProductScore(product, weights = { commission: 0.4, sales: 0.35, score: 0.25 }) {
  let totalScore = 0;

  // 1. 佣金得分 (基于佣金金额)
  const commissionAmount = parseFloat((product.commission_amount || '').replace(/[¥￥]/g, '')) || 0;
  // 假设佣金0-50元映射到0-100分
  const commissionScore = Math.min(commissionAmount / 50 * 100, 100);
  totalScore += commissionScore * weights.commission;

  // 2. 销量得分
  const sales = parseInt(product.monthly_sales) || 0;
  // 使用对数缩放，1000销量=50分，10000销量=75分，100000销量=100分
  let salesScore = 0;
  if (sales > 0) {
    salesScore = Math.min(Math.log10(sales) / 5 * 100, 100);
  }
  totalScore += salesScore * weights.sales;

  // 3. 店铺评分得分
  const shopScore = parseInt((product.shop_score || '').replace(/分/g, '')) || 0;
  // 评分通常在80-100之间，映射到0-100
  const normalizedScore = Math.max((shopScore - 80) / 20 * 100, 0);
  totalScore += normalizedScore * weights.score;

  return Math.round(totalScore * 100) / 100;
}

/**
 * 获取Top N推荐产品
 * @param {Array} products - 产品列表
 * @param {number} n - 返回数量
 * @param {Object} weights - 权重配置
 * @returns {Array} 排序后的产品列表（带综合得分）
 */
function getTopProducts(products, n = 10, weights = { commission: 0.4, sales: 0.35, score: 0.25 }) {
  // 计算每个产品的综合得分
  const scoredProducts = products.map(p => ({
    ...p,
    totalScore: calculateProductScore(p, weights)
  }));

  // 按综合得分降序排序
  scoredProducts.sort((a, b) => b.totalScore - a.totalScore);

  // 返回前N个
  return n > 0 ? scoredProducts.slice(0, n) : scoredProducts;
}

// 监听来自popup的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'parseProducts') {
    const products = parseBaiyingProducts();
    const uniqueProducts = deduplicateProducts(products);
    sendResponse({ products: uniqueProducts });
  } else if (request.action === 'getTopProducts') {
    const products = parseBaiyingProducts();
    const uniqueProducts = deduplicateProducts(products);
    const topProducts = getTopProducts(
      uniqueProducts,
      request.count || 10,
      request.weights || { commission: 0.4, sales: 0.35, score: 0.25 }
    );
    sendResponse({ products: topProducts });
  }
  return true;
});

// 页面加载完成后自动解析并存储
function autoParseOnLoad() {
  // 等待页面动态内容加载
  setTimeout(() => {
    const products = parseBaiyingProducts();
    const uniqueProducts = deduplicateProducts(products);

    // 存储到sessionStorage供popup使用
    sessionStorage.setItem('baiying_products', JSON.stringify(uniqueProducts));

    console.log(`[百应选品助手] 已解析 ${uniqueProducts.length} 个产品`);
  }, 2000);
}

// 监听页面变化（用于SPA页面）
let lastProductCount = 0;
function observePageChanges() {
  const observer = new MutationObserver(() => {
    const products = parseBaiyingProducts();
    if (products.length !== lastProductCount) {
      lastProductCount = products.length;
      const uniqueProducts = deduplicateProducts(products);
      sessionStorage.setItem('baiying_products', JSON.stringify(uniqueProducts));
      console.log(`[百应选品助手] 页面更新，已解析 ${uniqueProducts.length} 个产品`);
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// 初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    autoParseOnLoad();
    observePageChanges();
  });
} else {
  autoParseOnLoad();
  observePageChanges();
}
