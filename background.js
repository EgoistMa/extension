const pendingDownloadTasks = new Map();

chrome.downloads.onChanged.addListener(delta => {
  if (!pendingDownloadTasks.has(delta.id)) {
    return;
  }
  const task = pendingDownloadTasks.get(delta.id);
  if (delta.state && 'complete' === delta.state.current) {
    chrome.downloads.search({
      'id': delta.id
    }, results => {
      const filePath = results && results[0x0] ? results[0x0].filename : '';
      task.sendResponse({
        'success': true,
        'filePath': filePath,
        'id': delta.id
      });
      pendingDownloadTasks.delete(delta.id);
    });
  } else {
    if (delta.state && 'interrupted' === delta.state.current) {
      task.sendResponse({
        'success': false,
        'error': '下载被中断'
      });
      pendingDownloadTasks.delete(delta.id);
    }
  }
});

function checkDirectory() {
  return new Promise(resolve => {
    chrome.storage.sync.get("downloadDirectory", result => {
      resolve(!!result.downloadDirectory);
    });
  });
}
function setDownloadDirectory() {
  return new Promise(resolve => {
    chrome.tabs.create({
      'url': 'chrome://settings/downloads'
    });
    chrome.notifications.create({
      'type': "basic",
      'iconUrl': "icon.png",
      'title': "设置下载目录",
      'message': "请在打开的Chrome设置页面中选择默认下载位置，然后返回扩展继续操作"
    });
    resolve(true);
  });
}
function downloadResource(url, directory, filename) {
  return new Promise((resolve, reject) => {
    const fullPath = directory + '/' + filename;
    chrome.downloads.download({
      'url': url,
      'filename': fullPath,
      'saveAs': false
    }, downloadId => {
      if (downloadId) {
        console.log("开始下载，ID:", downloadId);
        resolve(downloadId);
      } else {
        const error = chrome.runtime.lastError || new Error("下载失败，未知原因");
        console.error("下载失败:", error.message);
        reject(error);
      }
    });
  });
}
async function downloadResources(data) {
  console.log("downloadResources request", data);
  if (!data || !data.images && !data.videos) {
    throw new Error("没有提供要下载的资源" + JSON.stringify(data));
  }
  downloadResource('https://timesport-1313948175.cos.ap-shanghai.myqcloud.com/20250607/d510ab4b-8f0a-4ed7-8a85-18546b567317.jpg', '', "aa.jpg");
  try {
    const promises = [];
    if (data.images && data.images.length > 0x0) {
      data.images.forEach((image, index) => {
        const filename = image.filename || "image_" + (index + 0x1) + ".jpg";
        promises.push(downloadResource(image.url, "/images", filename)["catch"](error => console.warn("图片 " + filename + " 下载失败:", error)));
      });
    }
    if (data.videos && data.videos.length > 0x0) {
      data.videos.forEach((video, index) => {
        const filename = video.filename || 'video_' + (index + 0x1) + ".mp4";
        promises.push(downloadResource(video.url, "/videos", filename)["catch"](error => console.warn("视频 " + filename + " 下载失败:", error)));
      });
    }
    await Promise.allSettled(promises);
  } catch (error) {
    console.error('下载过程中出错:', error);
    throw error;
  }
}
chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
  console.log("收到来自 " + (sender.tab ? "content script" : 'extension') + " 的消息:", message);
  switch (message.action) {
    case "getCurrentTabId":
      chrome.tabs.query({
        'active': true,
        'currentWindow': true
      }, tabs => {
        if (tabs.length > 0x0) {
          sendResponse({
            'tabId': tabs[0x0].id
          });
        } else {
          sendResponse({
            'tabId': null
          });
        }
      });
      return true;
    case 'checkDirectory':
      checkDirectory().then(hasDirectory => sendResponse({
        'hasDirectory': hasDirectory
      }));
      return true;
    case "setDirectory":
      setDownloadDirectory().then(success => sendResponse({
        'success': success
      }));
      return true;
    case "download":
      downloadResources(message.data).then(() => {
        sendResponse({
          'success': true
        });
      })['catch'](error => {
        console.error("下载资源失败:", error);
        sendResponse({
          'success': false,
          'error': error.message
        });
      });
      return true;
    case "downloadVideoFile":
      if (!message.url || !message.filename) {
        sendResponse({
          'success': false,
          'error': "参数不完整"
        });
        return true;
      }
      chrome.downloads.download({
        'url': message.url,
        'filename': message.filename.replace(/^\/+/, ''),
        'saveAs': false,
        'conflictAction': "overwrite"
      }, downloadId => {
        if (chrome.runtime.lastError || !downloadId) {
          sendResponse({
            'success': false,
            'error': chrome.runtime.lastError?.message || "下载启动失败"
          });
        } else {
          pendingDownloadTasks.set(downloadId, {
            'sendResponse': sendResponse
          });
        }
      });
      return true;
    case "openDouyinSearch":
      if (!message.keyword || !message.keyword.trim()) {
        sendResponse({
          'success': false,
          'error': "缺少关键词"
        });
        return true;
      }
      chrome.tabs.create({
        'url': "https://www.douyin.com/search/" + encodeURIComponent(message.keyword.trim())
      }, tab => {
        if (chrome.runtime.lastError || !tab) {
          sendResponse({
            'success': false,
            'error': chrome.runtime.lastError?.message || "打开抖音失败"
          });
        } else {
          sendResponse({
            'success': true,
            'tabId': tab.id || null
          });
        }
      });
      return true;
    case "testConcatHealth":
      (async () => {
        try {
          const res = await fetch("http://127.0.0.1:8787/health");
          const data = await res.json();
          sendResponse({
            'success': true,
            'data': data
          });
        } catch (error) {
          sendResponse({
            'success': false,
            'error': error.message
          });
        }
      })();
      return true;
    case "concatVideos":
      if (!message.payload) {
        sendResponse({
          'success': false,
          'error': "缺少任务数据"
        });
        return true;
      }
      (async () => {
        try {
          const res = await fetch("http://127.0.0.1:8787/concat", {
            'method': "POST",
            'headers': {
              'Content-Type': 'application/json'
            },
            'body': JSON.stringify(message.payload)
          });
          const data = await res.json();
          sendResponse({
            'success': true,
            'data': data
          });
        } catch (error) {
          sendResponse({
            'success': false,
            'error': error.message
          });
        }
      })();
      return true;
    case "openAndScrape":
      console.log('openAndScrape', message.action);
      chrome.tabs.query({
        'active': true,
        'currentWindow': true
      }, tabs => {
        console.log("tabs.length", tabs.length);
        if (0x0 === tabs.length) {
          return void sendResponse({
            'status': "ERROR",
            'message': "未找到活动标签页"
          });
        }
        const pageData = message.data;
        console.log("pageData", pageData);
        const tabId = tabs[0x0].id;
        chrome.tabs.update(tabId, {
          'url': 'https://buyin.jinritemai.com/dashboard/merch-picking-library?pre_universal_page_params_id=&universal_page_params_id=b000f7e4-1613-4f30-ae27-5851a7d4e912'
        }, tab => {
          if (!tab) {
            console.error("标签页更新失败:", chrome.runtime.lastError);
            return void sendResponse({
              'status': "ERROR",
              'message': "打开页面失败"
            });
          }
          const onTabUpdated = (updatedTabId, changeInfo) => {
            console.log("onTabUpdated complete", updatedTabId, tabId);
            if (updatedTabId === tabId && 'complete' === changeInfo.status) {
              chrome.tabs.onUpdated.removeListener(onTabUpdated);
              pageData.action = "applyFilters";
              chrome.tabs.sendMessage(tabId, pageData, function (response) {
                if (chrome.runtime.lastError) {
                  console.error("Error sending message:", chrome.runtime.lastError.message);
                } else {
                  console.log("Message sent successfully:", response);
                }
              });
            }
          };
          chrome.tabs.onUpdated.addListener(onTabUpdated);
        });
        return true;
      });
      break;
    default:
      console.warn("未知消息类型:", message.action);
      sendResponse({
        'status': "ERROR",
        'message': "未知消息类型"
      });
  }
  return true;
});
