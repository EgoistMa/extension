/**
 * 百应智能选品 - Content Script
 * 自动解析页面产品信息并发送到本地服务
 */

// 解析产品信息
function parseBaiyingProducts() {
  const products = [];
  const wrapperElements = document.querySelectorAll('[class*="index_module__wrapper___"]');

  wrapperElements.forEach((wrapper) => {
    const text = wrapper.textContent || '';
    if (!text.includes('赚')) return;

    const product = {};

    // 产品名称
    const titleElem = wrapper.querySelector('[class*="index_module__luckyTitle___"], [class*="index_module__oneLine___"]');
    if (titleElem) {
      product.name = titleElem.textContent.trim();
    }

    // 佣金百分比
    const ratioElem = wrapper.querySelector('[class*="index_module__cosratio___"]');
    if (ratioElem) {
      product.commission_rate = ratioElem.textContent.trim() + '%';
    }

    // 佣金金额
    const feeElem = wrapper.querySelector('[class*="index_module__cosFee___"]');
    if (feeElem) {
      const feeText = feeElem.textContent.trim();
      const match = feeText.match(/[¥￥]?(\d+\.?\d*)/);
      if (match) {
        product.commission_amount = '¥' + match[1];
      }
    }

    // 价格
    const priceElem = wrapper.querySelector('[class*="index_module__price___"]');
    if (priceElem) {
      const priceText = priceElem.textContent.trim();
      const match = priceText.match(/[¥￥](\d+\.?\d*)/);
      if (match) {
        product.price = '¥' + match[1];
      }
    }

    // 店铺名称
    const shopElem = wrapper.querySelector('[class*="index_module__shopName___"]');
    if (shopElem) {
      product.shop_name = shopElem.textContent.trim();
    }

    // 月销量
    const salesElem = wrapper.querySelector('[class*="index_module__priceAndSales___"]');
    if (salesElem) {
      const salesText = salesElem.textContent.trim();
      const salesMatch = salesText.match(/月销\s*([\d,]+)/);
      if (salesMatch) {
        product.monthly_sales = salesMatch[1].replace(/,/g, '');
      }
    }

    // 店铺评分
    const scoreElem = wrapper.querySelector('[class*="index_module__score___"]');
    if (scoreElem) {
      product.shop_score = scoreElem.textContent.trim();
    }

    if (product.name && (product.commission_amount || product.commission_rate)) {
      products.push(product);
    }
  });

  return products;
}

// 去重
function deduplicateProducts(products) {
  const seen = new Set();
  return products.filter(p => {
    const key = `${p.name}-${p.commission_amount}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// 计算综合得分
function calculateProductScore(product, weights = { commission: 0.4, sales: 0.35, score: 0.25 }) {
  let totalScore = 0;

  // 佣金得分
  const commissionAmount = parseFloat((product.commission_amount || '').replace(/[¥￥]/g, '')) || 0;
  const commissionScore = Math.min(commissionAmount / 50 * 100, 100);
  totalScore += commissionScore * weights.commission;

  // 销量得分 (对数缩放)
  const sales = parseInt(product.monthly_sales) || 0;
  let salesScore = 0;
  if (sales > 0) {
    salesScore = Math.min(Math.log10(sales) / 5 * 100, 100);
  }
  totalScore += salesScore * weights.sales;

  // 评分得分
  const shopScore = parseInt((product.shop_score || '').replace(/分/g, '')) || 0;
  const normalizedScore = Math.max((shopScore - 80) / 20 * 100, 0);
  totalScore += normalizedScore * weights.score;

  return Math.round(totalScore * 100) / 100;
}

// 获取Top N推荐产品
function getTopProducts(products, n = 10, weights = { commission: 0.4, sales: 0.35, score: 0.25 }) {
  const scoredProducts = products.map(p => ({
    ...p,
    totalScore: calculateProductScore(p, weights)
  }));

  scoredProducts.sort((a, b) => b.totalScore - a.totalScore);
  return n > 0 ? scoredProducts.slice(0, n) : scoredProducts;
}

// 发送产品列表到本地服务
async function sendToLocalServer(products, serverUrl = 'http://localhost:5000/api/products') {
  try {
    const response = await fetch(serverUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        timestamp: new Date().toISOString(),
        source: 'baiying-smart-picker',
        page_url: window.location.href,
        product_count: products.length,
        products: products
      })
    });

    if (response.ok) {
      console.log('[百应智能选品] 已发送产品列表到本地服务');
      return { success: true, message: '发送成功' };
    } else {
      console.error('[百应智能选品] 发送失败:', response.status);
      return { success: false, message: `HTTP ${response.status}` };
    }
  } catch (error) {
    console.error('[百应智能选品] 发送错误:', error);
    return { success: false, message: error.message };
  }
}

// 检测页面是否为选品广场
function isProductSelectionPage() {
  // 检查URL或页面特征
  const url = window.location.href;
  if (url.includes('merch-picking') || url.includes('xuanpin')) {
    return true;
  }

  // 检查页面是否有产品列表
  const wrappers = document.querySelectorAll('[class*="index_module__wrapper___"]');
  return wrappers.length > 0;
}

// 页面状态
let pageState = {
  isProductPage: false,
  productCount: 0,
  lastSentTime: 0,
  autoSendEnabled: true
};

// 自动解析并发送
async function autoParseAndSend(weights, topCount, serverUrl) {
  if (!isProductSelectionPage()) {
    console.log('[百应智能选品] 非选品页面，跳过解析');
    return null;
  }

  const products = parseBaiyingProducts();
  const uniqueProducts = deduplicateProducts(products);

  if (uniqueProducts.length === 0) {
    console.log('[百应智能选品] 未找到产品');
    return null;
  }

  const topProducts = getTopProducts(uniqueProducts, topCount, weights);

  console.log(`[百应智能选品] 解析到 ${uniqueProducts.length} 个产品，推荐 Top ${topCount}`);

  // 发送到本地服务
  const result = await sendToLocalServer(topProducts, serverUrl);

  return {
    allProducts: uniqueProducts,
    topProducts: topProducts,
    sendResult: result
  };
}

// 监听来自popup的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkPage') {
    // 检查页面状态
    const isProductPage = isProductSelectionPage();
    const products = isProductPage ? parseBaiyingProducts() : [];
    sendResponse({
      isProductPage: isProductPage,
      productCount: deduplicateProducts(products).length,
      url: window.location.href
    });
  } else if (request.action === 'parseProducts') {
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
  } else if (request.action === 'sendToServer') {
    (async () => {
      const result = await autoParseAndSend(
        request.weights || { commission: 0.4, sales: 0.35, score: 0.25 },
        request.count || 10,
        request.serverUrl || 'http://localhost:5000/api/products'
      );
      sendResponse(result);
    })();
    return true; // 异步响应
  }
  return true;
});

// 页面加载完成后的初始化
function initOnLoad() {
  setTimeout(() => {
    if (isProductSelectionPage()) {
      const products = parseBaiyingProducts();
      const uniqueProducts = deduplicateProducts(products);

      pageState.isProductPage = true;
      pageState.productCount = uniqueProducts.length;

      console.log(`[百应智能选品] 页面加载完成，检测到 ${uniqueProducts.length} 个产品`);

      // 通知background script
      chrome.runtime.sendMessage({
        action: 'pageDetected',
        productCount: uniqueProducts.length,
        url: window.location.href
      });

      // 3秒后自动发送
      if (pageState.autoSendEnabled && uniqueProducts.length > 0) {
        setTimeout(async () => {
          const topProducts = getTopProducts(uniqueProducts, 10);
          const result = await sendToLocalServer(topProducts);
          console.log('[百应智能选品] 自动发送结果:', result);
        }, 3000);
      }
    }
  }, 2000);
}

// 监听页面变化
let lastProductCount = 0;
function observePageChanges() {
  const observer = new MutationObserver(() => {
    if (!isProductSelectionPage()) return;

    const products = parseBaiyingProducts();
    const count = deduplicateProducts(products).length;

    if (count !== lastProductCount && count > 0) {
      lastProductCount = count;
      pageState.productCount = count;

      console.log(`[百应智能选品] 页面更新，产品数量: ${count}`);

      // 通知popup更新
      chrome.runtime.sendMessage({
        action: 'productsUpdated',
        productCount: count
      });
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
    initOnLoad();
    observePageChanges();
  });
} else {
  initOnLoad();
  observePageChanges();
}
