/**
 * 百应智能选品 - Background Service Worker
 */

// 存储当前状态
let currentState = {
  isOnBaiyingPage: false,
  productCount: 0,
  lastUrl: ''
};

// 监听来自content script的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'pageDetected') {
    currentState.isOnBaiyingPage = true;
    currentState.productCount = request.productCount;
    currentState.lastUrl = request.url;

    // 更新badge显示产品数量
    chrome.action.setBadgeText({ text: String(request.productCount) });
    chrome.action.setBadgeBackgroundColor({ color: '#667eea' });
  } else if (request.action === 'productsUpdated') {
    currentState.productCount = request.productCount;
    chrome.action.setBadgeText({ text: String(request.productCount) });
  } else if (request.action === 'getState') {
    sendResponse(currentState);
  }
  return true;
});

// 监听标签页变化
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    updateStateFromTab(tab);
  } catch (e) {
    console.error('Error getting tab:', e);
  }
});

// 监听URL变化
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete') {
    updateStateFromTab(tab);
  }
});

function updateStateFromTab(tab) {
  if (tab.url && tab.url.includes('buyin.jinritemai.com')) {
    currentState.isOnBaiyingPage = true;
    currentState.lastUrl = tab.url;
  } else {
    currentState.isOnBaiyingPage = false;
    currentState.productCount = 0;
    chrome.action.setBadgeText({ text: '' });
  }
}
