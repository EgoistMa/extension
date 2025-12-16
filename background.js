function checkDirectory() {
  return new Promise(_0x1e0d20 => {
    chrome.storage.sync.get("downloadDirectory", _0x2245b3 => {
      _0x1e0d20(!!_0x2245b3.downloadDirectory);
    });
  });
}
function setDownloadDirectory() {
  return new Promise(_0x9ddbc7 => {
    chrome.tabs.create({
      'url': 'chrome://settings/downloads'
    });
    chrome.notifications.create({
      'type': "basic",
      'iconUrl': "icon.png",
      'title': "设置下载目录",
      'message': "请在打开的Chrome设置页面中选择默认下载位置，然后返回扩展继续操作"
    });
    _0x9ddbc7(true);
  });
}
function downloadResource(_0x50269f, _0x2f3d30, _0x1e2932) {
  return new Promise((_0x1ebf51, _0x2e1c34) => {
    const _0x5ab6ad = _0x2f3d30 + '/' + _0x1e2932;
    chrome.downloads.download({
      'url': _0x50269f,
      'filename': _0x5ab6ad,
      'saveAs': false
    }, _0x1d454b => {
      if (_0x1d454b) {
        console.log("开始下载，ID:", _0x1d454b);
        _0x1ebf51(_0x1d454b);
      } else {
        const _0x1e5028 = chrome.runtime.lastError || new Error("下载失败，未知原因");
        console.error("下载失败:", _0x1e5028.message);
        _0x2e1c34(_0x1e5028);
      }
    });
  });
}
async function downloadResources(_0x960929) {
  console.log("downloadResources request", _0x960929);
  if (!_0x960929 || !_0x960929.images && !_0x960929.videos) {
    throw new Error("没有提供要下载的资源" + JSON.stringify(_0x960929));
  }
  downloadResource('https://timesport-1313948175.cos.ap-shanghai.myqcloud.com/20250607/d510ab4b-8f0a-4ed7-8a85-18546b567317.jpg', '', "aa.jpg");
  try {
    const _0xaa8e45 = [];
    if (_0x960929.images && _0x960929.images.length > 0x0) {
      _0x960929.images.forEach((_0x579c97, _0x215f2a) => {
        const _0x1a99bb = _0x579c97.filename || "image_" + (_0x215f2a + 0x1) + ".jpg";
        _0xaa8e45.push(downloadResource(_0x579c97.url, "/images", _0x1a99bb)["catch"](_0x782907 => console.warn("图片 " + _0x1a99bb + " 下载失败:", _0x782907)));
      });
    }
    if (_0x960929.videos && _0x960929.videos.length > 0x0) {
      _0x960929.videos.forEach((_0x307412, _0x4e0770) => {
        const _0x1964ef = _0x307412.filename || 'video_' + (_0x4e0770 + 0x1) + ".mp4";
        _0xaa8e45.push(downloadResource(_0x307412.url, "/videos", _0x1964ef)["catch"](_0x204f89 => console.warn("视频 " + _0x1964ef + " 下载失败:", _0x204f89)));
      });
    }
    await Promise.allSettled(_0xaa8e45);
  } catch (_0x3d1201) {
    console.error('下载过程中出错:', _0x3d1201);
    throw _0x3d1201;
  }
}
chrome.runtime.onMessage.addListener(function (_0x2e958a, _0x30ce25, _0x271720) {
  console.log("收到来自 " + (_0x30ce25.tab ? "content script" : 'extension') + " 的消息:", _0x2e958a);
  switch (_0x2e958a.action) {
    case "getCurrentTabId":
      chrome.tabs.query({
        'active': true,
        'currentWindow': true
      }, _0x61cb87 => {
        if (_0x61cb87.length > 0x0) {
          _0x271720({
            'tabId': _0x61cb87[0x0].id
          });
        } else {
          _0x271720({
            'tabId': null
          });
        }
      });
      return true;
    case 'checkDirectory':
      checkDirectory().then(_0x440aa3 => _0x271720({
        'hasDirectory': _0x440aa3
      }));
      return true;
    case "setDirectory":
      setDownloadDirectory().then(_0x325f6f => _0x271720({
        'success': _0x325f6f
      }));
      return true;
    case "download":
      downloadResources(_0x2e958a.data).then(() => {
        _0x271720({
          'success': true
        });
      })['catch'](_0x4c791d => {
        console.error("下载资源失败:", _0x4c791d);
        _0x271720({
          'success': false,
          'error': _0x4c791d.message
        });
      });
      return true;
    case "openAndScrape":
      console.log('openAndScrape', _0x2e958a.action);
      chrome.tabs.query({
        'active': true,
        'currentWindow': true
      }, _0x457082 => {
        console.log("tabs.length", _0x457082.length);
        if (0x0 === _0x457082.length) {
          return void _0x271720({
            'status': "ERROR",
            'message': "未找到活动标签页"
          });
        }
        const _0x3b8e1d = _0x2e958a.data;
        console.log("pageData", _0x3b8e1d);
        const _0x5b67f7 = _0x457082[0x0].id;
        chrome.tabs.update(_0x5b67f7, {
          'url': 'https://buyin.jinritemai.com/dashboard/merch-picking-library?pre_universal_page_params_id=&universal_page_params_id=b000f7e4-1613-4f30-ae27-5851a7d4e912'
        }, _0x1070ba => {
          if (!_0x1070ba) {
            console.error("标签页更新失败:", chrome.runtime.lastError);
            return void _0x271720({
              'status': "ERROR",
              'message': "打开页面失败"
            });
          }
          const _0x49b8b4 = (_0x2ed617, _0x58cedb) => {
            console.log("onTabUpdated complete", _0x2ed617, _0x5b67f7);
            if (_0x2ed617 === _0x5b67f7 && 'complete' === _0x58cedb.status) {
              chrome.tabs.onUpdated.removeListener(_0x49b8b4);
              _0x3b8e1d.action = "applyFilters";
              chrome.tabs.sendMessage(_0x5b67f7, _0x3b8e1d, function (_0x3ea333) {
                if (chrome.runtime.lastError) {
                  console.error("Error sending message:", chrome.runtime.lastError.message);
                } else {
                  console.log("Message sent successfully:", _0x3ea333);
                }
              });
            }
          };
          chrome.tabs.onUpdated.addListener(_0x49b8b4);
        });
        return true;
      });
      break;
    default:
      console.warn("未知消息类型:", _0x2e958a.action);
      _0x271720({
        'status': "ERROR",
        'message': "未知消息类型"
      });
  }
  return true;
});