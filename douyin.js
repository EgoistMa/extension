let video_url = '';
let user = null;
let excuteTime = null;
function getMidnightTimestamp() {
  const _0xa3296c = new Date();
  return new Date(_0xa3296c.getFullYear(), _0xa3296c.getMonth(), _0xa3296c.getDate()).getTime();
}
function loadUserData() {
  chrome.storage.local.get("xuanpin_user", function (_0x6a90b2) {
    if (_0x6a90b2.xuanpin_user) {
      user = JSON.parse(_0x6a90b2.xuanpin_user);
      console.log("xuanpin_user======>", user);
    }
  });
  excuteTime = getMidnightTimestamp();
}
function earlyInjectScript() {
  try {
    console.info("【智能选品】开始尝试注入脚本");
    injectScriptToPage();
  } catch (_0xb77598) {
    console.error("【智能选品】初始化注入脚本失败:", _0xb77598);
    setTimeout(earlyInjectScript, 0x32);
  }
}
function injectScriptToPage() {
  try {
    if (!document.documentElement) {
      console.warn('【智能选品】DOM元素尚未准备好，稍后重试');
      return void setTimeout(injectScriptToPage, 0xa);
    }
    const _0x977f9 = document.createElement('script');
    _0x977f9.async = false;
    _0x977f9.defer = false;
    _0x977f9.src = chrome.runtime.getURL("assets/douyin-insert.js");
    document.documentElement.appendChild(_0x977f9);
    _0x977f9.onload = function () {
      console.info("【智能选品】douyin-insert.js脚本加载成功.");
    };
    _0x977f9.onerror = function () {
      console.error("【智能选品】douyin-insert.js脚本加载失败.");
      setTimeout(injectScriptToPage, 0x3e8);
    };
  } catch (_0x157a9e) {
    console.error("【智能选品】注入脚本过程出错:", _0x157a9e);
    setTimeout(injectScriptToPage, 0x32);
  }
}
earlyInjectScript();
window.addEventListener("message", function (_0x5c3409) {
  try {
    if (_0x5c3409.data && _0x5c3409.data.type && 'REQUEST_STORED_REQUESTS' === _0x5c3409.data.type && 'douyin-insert.js' === _0x5c3409.data.from) {
      console.log('【智能选品】收到页面脚本请求，获取存储的请求信息');
      chrome.storage.local.get(null, function (_0x2352eb) {
        const _0x57ad88 = [];
        for (const _0x55dc1c in _0x2352eb) if (_0x55dc1c.startsWith("douyin_request_")) {
          _0x57ad88.push(_0x2352eb[_0x55dc1c]);
          chrome.storage.local.remove(_0x55dc1c);
        }
        if (_0x57ad88.length > 0x0) {
          console.log("【智能选品】获取到存储的请求数量:", _0x57ad88.length);
          window.postMessage({
            'type': 'PRE_CAPTURED_REQUESTS',
            'requests': _0x57ad88
          }, '*');
        }
      });
    }
  } catch (_0x7c2e0f) {
    console.error("【智能选品】处理页面脚本消息失败:", _0x7c2e0f);
  }
}, false);
let video_map = {};
async function getRequestParams(_0x27bccd) {
  const _0x46c259 = await parseUrlParameters();
  return "userParams" === _0x27bccd ? {
    'device_platform': "webapp",
    'aid': _0x46c259.aid || 0x18ef,
    'channel': 'channel_pc_web',
    'locate_item_id': _0x46c259.locate_item_id || "7377694813719678220",
    'locate_query': false,
    'show_live_replay_strategy': _0x46c259.show_live_replay_strategy || 0x1,
    'need_time_list': _0x46c259.need_time_list || 0x1,
    'time_list_query': _0x46c259.time_list_query || 0x0,
    'whale_cut_token': _0x46c259.whale_cut_token || '',
    'cut_version': _0x46c259.cut_version || 0x1,
    'count': 0x14,
    'publish_video_strategy_type': _0x46c259.publish_video_strategy_type || 0x2,
    'update_version_code': _0x46c259.update_version_code || "170400",
    'pc_client_type': _0x46c259.pc_client_type || 0x1,
    'version_code': _0x46c259.version_code || "290100",
    'version_name': _0x46c259.version_name || "29.1.0",
    'cookie_enabled': _0x46c259.cookie_enabled || true,
    'screen_width': _0x46c259.screen_width || 0x72b,
    'screen_height': _0x46c259.screen_height || 0x408,
    'browser_language': _0x46c259.browser_language || "zh-CN",
    'browser_platform': _0x46c259.browser_platform || "Linux x86_64",
    'browser_name': _0x46c259.browser_name || "Chrome",
    'browser_version': _0x46c259.browser_version || "124.0.0.0",
    'browser_online': _0x46c259.browser_online || true,
    'engine_name': _0x46c259.engine_name || "Blink",
    'engine_version': _0x46c259.engine_version || "124.0.0.0",
    'os_name': _0x46c259.os_name || "Linux",
    'os_version': _0x46c259.os_version || "x86_64",
    'cpu_core_num': _0x46c259.cpu_core_num || 0x10,
    'device_memory': _0x46c259.device_memory || 0x8,
    'platform': _0x46c259.platform || 'PC',
    'downlink': _0x46c259.downlink || 0xa,
    'effective_type': _0x46c259.effective_type || '4g',
    'round_trip_time': _0x46c259.round_trip_time || 0x64,
    'webid': getWebUserId() || '7373573059258828323'
  } : "detailParams" === _0x27bccd ? {
    'device_platform': 'webapp',
    'aid': _0x46c259.aid || 0x18ef,
    'channel': "channel_pc_web",
    'update_version_code': "170400",
    'pc_client_type': _0x46c259.pc_client_type || 0x1,
    'version_code': _0x46c259.version_code || "190500",
    'version_name': _0x46c259.version_name || "19.5.0",
    'cookie_enabled': _0x46c259.cookie_enabled || true,
    'screen_width': _0x46c259.screen_width || 0x72b,
    'screen_height': _0x46c259.screen_height || 0x408,
    'browser_language': _0x46c259.browser_language || "zh-CN",
    'browser_platform': _0x46c259.browser_platform || "Linux x86_64",
    'browser_name': _0x46c259.browser_name || 'Chrome',
    'browser_version': _0x46c259.browser_version || "124.0.0.0",
    'browser_online': _0x46c259.browser_online || true,
    'engine_name': _0x46c259.engine_name || "Blink",
    'engine_version': _0x46c259.engine_version || "124.0.0.0",
    'os_name': _0x46c259.os_name || "Linux",
    'os_version': _0x46c259.os_version || "x86_64",
    'cpu_core_num': _0x46c259.cpu_core_num || 0x10,
    'device_memory': _0x46c259.device_memory || 0x8,
    'platform': 'PC',
    'downlink': _0x46c259.downlink || 0xa,
    'effective_type': _0x46c259.effective_type || '4g',
    'round_trip_time': _0x46c259.round_trip_time || 0x32,
    'webid': getWebUserId() || "7373573059258828323"
  } : null;
}
let fileNumber = 0x1;
function waitForElement(_0x17a4e7, _0x4e61b8) {
  const _0xf68790 = () => {
    const _0x25db1a = document.querySelector(_0x17a4e7);
    return !!_0x25db1a && (_0x4e61b8(_0x25db1a), true);
  };
  if (_0xf68790()) {
    return;
  }
  const _0xa0a7f8 = new MutationObserver(_0x157ccf => {
    if (_0xf68790()) {
      _0xa0a7f8.disconnect();
    }
  });
  const _0x3425d6 = () => {
    if (document.body) {
      _0xa0a7f8.observe(document.body, {
        'childList': true,
        'subtree': true,
        'attributes': false
      });
    } else {
      setTimeout(_0x3425d6, 0x64);
    }
  };
  _0x3425d6();
}
function getWebUserId() {
  try {
    let _0x70aeb8 = localStorage.getItem("__tea_cache_tokens_6383");
    if (_0x70aeb8) {
      let _0x1e4f82 = JSON.parse(_0x70aeb8)?.["user_unique_id"];
      if (!_0x1e4f82) {
        _0x70aeb8 = localStorage.getItem("__tea_cache_tokens_7497");
        if (_0x70aeb8) {
          _0x1e4f82 = JSON.parse(_0x70aeb8)?.["user_unique_id"];
        }
      }
      return _0x1e4f82 || '';
    }
    return '';
  } catch (_0x5112b3) {
    console.log("获取用户ID失败:", _0x5112b3);
    return '';
  }
}
function parseUrlParameters() {
  const _0x23c4d4 = window.location.href;
  const _0x32dee7 = _0x23c4d4.indexOf('?');
  if (-0x1 === _0x32dee7) {
    return {};
  }
  const _0x4f4cb3 = _0x23c4d4.substring(_0x32dee7 + 0x1);
  if (!_0x4f4cb3) {
    return {};
  }
  const _0x461f5e = _0x4f4cb3.split('&');
  const _0x227d09 = {};
  _0x461f5e.forEach(_0x181091 => {
    const [_0x315a8c, _0xcbb6c1] = _0x181091.split('=');
    const _0x5a291f = decodeURIComponent(_0x315a8c || '');
    const _0x241694 = decodeURIComponent(_0xcbb6c1 || '');
    if (_0x227d09.hasOwnProperty(_0x5a291f)) {
      if (!Array.isArray(_0x227d09[_0x5a291f])) {
        _0x227d09[_0x5a291f] = [_0x227d09[_0x5a291f]];
      }
      _0x227d09[_0x5a291f].push(_0x241694);
    } else {
      _0x227d09[_0x5a291f] = _0x241694;
    }
  });
  return _0x227d09;
}
function checkConditionPeriodically(_0x4f50b0) {
  const _0x1e80fc = setInterval(() => {
    if (_0x4f50b0.trueFunc && _0x4f50b0.trueFunc() && "function" == typeof _0x4f50b0.back) {
      clearInterval(_0x1e80fc);
      _0x4f50b0.back();
    }
  }, 0x1f4);
}
function createDownloadButton(_0x4e9a90, _0x4f989b) {
  const _0x49604b = document.createElement('button');
  _0x49604b.textContent = _0x4e9a90;
  _0x49604b.className = "download-button " + _0x4f989b;
  _0x49604b.style.cssText = "padding: 5px 10px; background-color: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; white-space: nowrap;";
  return _0x49604b;
}
async function handleDownloadButtonClick(_0x474f14, _0x45a965) {
  console.log("点击了\"下载" + _0x474f14 + "\"按钮，视频ID: " + _0x45a965);
  fileNumber = _0x474f14;
  await requestVideoDetail({
    'vid': _0x45a965,
    'trigger': "download4item"
  });
}
function addDownloadButtonsToCards() {
  console.log("aaa");
  document.querySelectorAll(".search-result-card").forEach(_0xdf4b65 => {
    console.log("bbb");
    if (!_0xdf4b65.querySelector(".videoImage")?.["textContent"]['includes']('图文')) {
      const _0x5b3490 = _0xdf4b65.parentElement.getAttribute('id');
      let _0x223b29 = '';
      if (_0x5b3490) {
        _0x223b29 = _0x5b3490.replaceAll("waterfall_item_", '');
      } else {
        const _0x2c7a2d = _0xdf4b65.querySelector('a');
        if (_0x2c7a2d) {
          const _0x2689a0 = _0x2c7a2d.getAttribute("href").split('/');
          _0x223b29 = _0x2689a0[_0x2689a0.length - 0x1];
        }
      }
      const _0x3c2109 = document.createElement('div');
      _0x3c2109.style.cssText = "position: absolute; right: 10px; top: 50%; transform: translateY(-50%); display: flex; flex-direction: column; gap: 5px; z-index: 10;";
      const _0x3605aa = createDownloadButton("下载1", "btn-download-1");
      _0x3605aa.addEventListener("click", () => {
        let _0x549d25 = _0x3605aa.closest(".AMqhOzPC");
        if (_0x549d25) {
          console.log(_0x549d25.id);
          chrome.storage.local.get("baiying_project_info", async _0x48e170 => {
            console.log("获取的数据:", _0x48e170);
            if (!_0x48e170 || !_0x48e170.baiying_project_info || !_0x48e170.baiying_project_info.product_id) {
              return void alert("请先下载图片！");
            }
            let _0x3ffafe = _0x48e170.baiying_project_info.product_id;
            if (old_product_id != _0x3ffafe) {
              return void alert("商品id已经发生变化，请重新进入页面再下载！");
            }
            if (!user || !user.id) {
              return void alert("未登录，请重新登录");
            }
            if (!excuteTime) {
              return void alert('执行批次不正确，请检查');
            }
            _0x3605aa.disabled = true;
            _0x3605aa.innerHTML = '<span>下载中...</span>';
            const _0x44d4c3 = _0x549d25.id.split('_');
            const _0x5659e5 = _0x44d4c3[_0x44d4c3.length - 0x1];
            const _0x4168f7 = video_map[_0x5659e5];
            if (_0x4168f7) {
              await downloadResource(_0x4168f7, user.id + '_' + excuteTime + '_' + _0x3ffafe + '_video_1.mp4');
            } else {
              console.log("使用handleDownloadButtonClick下载");
              await handleDownloadButtonClick(0x1, _0x223b29);
            }
            setTimeout(() => {
              _0x3605aa.disabled = false;
              _0x3605aa.innerHTML = "<span>下载1</span>";
            }, 0x3e8);
          });
        } else {
          alert("数据异常");
        }
      });
      const _0x37285c = createDownloadButton('下载2', "btn-download-2");
      _0x37285c.addEventListener("click", () => {
        let _0x4a9a63 = _0x37285c.closest(".AMqhOzPC");
        if (_0x4a9a63) {
          console.log(_0x4a9a63.id);
          chrome.storage.local.get("baiying_project_info", async _0x1a008f => {
            console.log('获取的数据:', _0x1a008f);
            if (!_0x1a008f || !_0x1a008f.baiying_project_info || !_0x1a008f.baiying_project_info.product_id) {
              return void alert('请先下载图片！');
            }
            let _0x18f115 = _0x1a008f.baiying_project_info.product_id;
            if (old_product_id != _0x18f115) {
              return void alert("商品id已经发生变化，请重新进入页面再下载！");
            }
            if (!user || !user.id) {
              return void alert("未登录，请重新登录");
            }
            if (!excuteTime) {
              return void alert('执行批次不正确，请检查');
            }
            _0x37285c.disabled = true;
            _0x37285c.innerHTML = '<span>下载中...</span>';
            const _0x516261 = _0x4a9a63.id.split('_');
            const _0x5740ad = _0x516261[_0x516261.length - 0x1];
            const _0x172bc6 = video_map[_0x5740ad];
            if (_0x172bc6) {
              await downloadResource(_0x172bc6, user.id + '_' + excuteTime + '_' + _0x18f115 + "_video_2.mp4");
            } else {
              console.log('使用handleDownloadButtonClick下载');
              await handleDownloadButtonClick(0x2, _0x223b29);
            }
            setTimeout(() => {
              _0x37285c.disabled = false;
              _0x37285c.innerHTML = "<span>下载2</span>";
            }, 0x3e8);
          });
        } else {
          alert("数据异常");
        }
      });
      const _0x3323fc = createDownloadButton("下载3", "btn-download-3");
      _0x3323fc.addEventListener("click", () => {
        let _0x9e8c1f = _0x3323fc.closest(".AMqhOzPC");
        if (_0x9e8c1f) {
          console.log(_0x9e8c1f.id);
          chrome.storage.local.get("baiying_project_info", async _0xeb256e => {
            console.log("获取的数据:", _0xeb256e);
            if (!_0xeb256e || !_0xeb256e.baiying_project_info || !_0xeb256e.baiying_project_info.product_id) {
              return void alert("请先下载图片！");
            }
            let _0x495520 = _0xeb256e.baiying_project_info.product_id;
            if (old_product_id != _0x495520) {
              return void alert("商品id已经发生变化，请重新进入页面再下载！");
            }
            if (!user || !user.id) {
              return void alert('未登录，请重新登录');
            }
            if (!excuteTime) {
              return void alert('执行批次不正确，请检查');
            }
            _0x3323fc.disabled = true;
            _0x3323fc.innerHTML = '<span>下载中...</span>';
            const _0x17039b = _0x9e8c1f.id.split('_');
            const _0x34f808 = _0x17039b[_0x17039b.length - 0x1];
            const _0x1c408c = video_map[_0x34f808];
            if (_0x1c408c) {
              await downloadResource(_0x1c408c, user.id + '_' + excuteTime + '_' + _0x495520 + "_video_3.mp4");
            } else {
              console.log("使用handleDownloadButtonClick下载");
              await handleDownloadButtonClick(0x3, _0x223b29);
            }
            setTimeout(() => {
              _0x3323fc.disabled = false;
              _0x3323fc.innerHTML = "<span>下载3</span>";
            }, 0x3e8);
          });
        } else {
          alert("数据异常");
        }
      });
      _0x3c2109.appendChild(_0x3605aa);
      _0x3c2109.appendChild(_0x37285c);
      _0x3c2109.appendChild(_0x3323fc);
      _0xdf4b65.style.position = "relative";
      _0xdf4b65.appendChild(_0x3c2109);
    }
  });
}
async function requestVideoDetail(_0x35669f) {
  const _0xda350d = await getRequestParams("detailParams");
  console.log("请求视频详情参数=>");
  _0xda350d.aweme_id = _0x35669f.vid;
  const _0x87b9d1 = buildQueryString(_0xda350d);
  window.postMessage({
    'action': "DBDY_ACCQURE2",
    'actionRes': "DBDY_ACCQURE2_RES",
    'url': "https://www.douyin.com/aweme/v1/web/aweme/detail/?" + _0x87b9d1,
    'trigger': _0x35669f.trigger,
    'options': {
      'credentials': "include"
    },
    'location': window.location.href
  }, '*');
}
function getVideoUrl() {
  const _0x3d5187 = document.querySelector(".xg-video-container");
  if (_0x3d5187) {
    const _0x509ff4 = _0x3d5187.querySelector("video");
    if (_0x509ff4) {
      const _0x6893b7 = _0x509ff4.querySelectorAll("source");
      if (_0x6893b7.length > 0x0) {
        const _0x28f038 = _0x6893b7[_0x6893b7.length - 0x1].src;
        console.log("最后一个source的src:", _0x28f038);
        return _0x28f038;
      }
      console.log("video下没有找到source元素");
    } else {
      console.log('xg-video-container下没有找到video元素');
    }
  } else {
    console.log("未找到class为xg-video-container的节点");
  }
  return '';
}
let old_product_id = '';
function getHighestQualityVideoUrl(_0x1bfced) {
  try {
    const _0x28446b = _0x1bfced?.["video"]?.["bit_rate"];
    if (_0x28446b) {
      const _0xac7c78 = _0x28446b.sort((_0x38fc22, _0x25eef9) => (_0x25eef9.play_addr?.['width'] || 0x0) - (_0x38fc22.play_addr?.["width"] || 0x0))[0x0].play_addr;
      if (_0xac7c78 && _0xac7c78.url_list && _0xac7c78.url_list.length > 0x0) {
        return _0xac7c78.url_list.find(_0x4479b2 => _0x4479b2.startsWith("https://www.douyin.com")) || _0xac7c78.url_list[0x0];
      }
    }
  } catch (_0x44e63b) {
    console.log("提取高清视频地址失败:", _0x44e63b);
  }
  return null;
}
function buildQueryString(_0x10560f) {
  const _0x122ca7 = [];
  for (const _0x7de532 in _0x10560f) _0x122ca7.push(_0x7de532 + '=' + _0x10560f[_0x7de532]);
  return _0x122ca7.join('&');
}
function formatDate(_0x5c8b19) {
  return new Date(_0x5c8b19).toISOString().split('T')[0x0];
}
function normalizeVideoData(_0x4778d3) {
  const _0x224938 = _0x4778d3.video?.["play_addr"]?.["url_list"];
  let _0x3de9a0 = _0x224938 ? _0x224938[0x0] : '';
  if (_0x224938 && _0x224938.length > 0x2) {
    _0x3de9a0 = _0x224938[0x2];
  }
  return {
    'vid': _0x4778d3.aweme_id,
    'date': new Date(0x3e8 * _0x4778d3.create_time).toISOString().split('T')[0x0],
    'cover': _0x4778d3.video?.["origin_cover"]?.["url_list"][0x0],
    'url': getHighestQualityVideoUrl(_0x4778d3) || _0x3de9a0,
    'authorName': _0x4778d3.author?.['nickname'],
    'title': _0x4778d3.desc
  };
}
window.addEventListener('load', async () => {
  await parseUrlParameters();
  setInterval(() => {
    addDownloadButtonsToCards();
  }, 0x7d0);
  function _0x3a4d08(_0x2c24c5) {
    let _0xd71b00;
    let _0x3bd0cd;
    let _0x1812c8 = document.getElementById("baiying-project-info-card");
    let _0x8b76cd = false;
    if (_0x1812c8) {
      _0xd71b00 = _0x1812c8.querySelector(".card-content");
      _0x3bd0cd = _0x1812c8.querySelector(".toggle-button");
      _0x8b76cd = _0xd71b00 && "none" === _0xd71b00.style.display;
    } else {
      _0x1812c8 = document.createElement('div');
      _0x1812c8.id = "baiying-project-info-card";
      Object.assign(_0x1812c8.style, {
        'position': "fixed",
        'top': "120px",
        'right': "20px",
        'zIndex': "9999",
        'background': "rgba(255, 255, 255, 0.95)",
        'border': "1px solid #e0e0e0",
        'borderRadius': "6px",
        'padding': "8px",
        'boxShadow': "0 2px 8px rgba(0, 0, 0, 0.1)",
        'maxWidth': "200px",
        'fontFamily': "Arial, sans-serif"
      });
      document.body.appendChild(_0x1812c8);
    }
    _0x1812c8.innerHTML = '';
    const _0x125215 = document.createElement("div");
    _0x125215.style.display = 'flex';
    _0x125215.style.justifyContent = "space-between";
    _0x125215.style.alignItems = 'center';
    _0x125215.style.marginBottom = "6px";
    const _0x295aa1 = document.createElement('h3');
    _0x295aa1.textContent = "当前商品信息";
    _0x295aa1.style.margin = '0';
    _0x295aa1.style.color = '#555';
    _0x295aa1.style.fontSize = "14px";
    _0x125215.appendChild(_0x295aa1);
    _0x3bd0cd = document.createElement("button");
    _0x3bd0cd.className = 'toggle-button';
    _0x3bd0cd.textContent = _0x8b76cd ? '▼' : '▲';
    Object.assign(_0x3bd0cd.style, {
      'background': 'none',
      'border': 'none',
      'fontSize': "12px",
      'color': "#888",
      'cursor': "pointer",
      'padding': "0 4px",
      'outline': 'none'
    });
    _0x125215.appendChild(_0x3bd0cd);
    _0x1812c8.appendChild(_0x125215);
    _0xd71b00 = document.createElement('div');
    _0xd71b00.className = 'card-content';
    if (_0x8b76cd) {
      _0xd71b00.style.display = 'none';
    }
    if (_0x2c24c5) {
      if (_0x2c24c5.cover) {
        const _0x56814b = document.createElement("div");
        _0x56814b.style.marginBottom = '6px';
        const _0x58aaa0 = document.createElement('img');
        _0x58aaa0.src = _0x2c24c5.cover;
        _0x58aaa0.style.width = "100%";
        _0x58aaa0.style.borderRadius = "3px";
        _0x58aaa0.style.objectFit = "cover";
        _0x56814b.appendChild(_0x58aaa0);
        _0xd71b00.appendChild(_0x56814b);
      }
      if (_0x2c24c5.product_id) {
        const _0x2574d9 = document.createElement("div");
        _0x2574d9.innerHTML = "ID: " + _0x2c24c5.product_id;
        _0x2574d9.style.marginBottom = "3px";
        _0x2574d9.style.color = "#888";
        _0x2574d9.style.fontSize = "12px";
        _0x2574d9.style.fontWeight = "normal";
        _0xd71b00.appendChild(_0x2574d9);
      }
      if (_0x2c24c5.product_name) {
        const _0x16c20b = document.createElement("div");
        _0x16c20b.innerHTML = "名称: " + _0x2c24c5.product_name;
        _0x16c20b.style.marginBottom = "3px";
        _0x16c20b.style.color = "#1e8a3eff";
        _0x16c20b.style.fontSize = "14px";
        _0x16c20b.style.fontWeight = "700";
        _0x16c20b.style.wordBreak = "break-word";
        _0xd71b00.appendChild(_0x16c20b);
      }
    } else {
      const _0xe1ea8b = document.createElement("div");
      _0xe1ea8b.textContent = "暂无商品信息";
      _0xe1ea8b.style.color = "#050404ff";
      _0xe1ea8b.style.fontSize = "12px";
      _0xd71b00.appendChild(_0xe1ea8b);
    }
    _0x1812c8.appendChild(_0xd71b00);
    _0x3bd0cd.addEventListener("click", function () {
      const _0x32a056 = 'none' === _0xd71b00.style.display;
      _0xd71b00.style.display = _0x32a056 ? 'block' : 'none';
      _0x3bd0cd.textContent = _0x32a056 ? '▲' : '▼';
    });
  }
  chrome.storage.local.get("baiying_project_info", async _0x64101e => {
    console.log("baiying_project_info res", _0x64101e.baiying_project_info);
    if (_0x64101e.baiying_project_info && _0x64101e.baiying_project_info.product_id) {
      old_product_id = _0x64101e.baiying_project_info.product_id;
    }
    _0x3a4d08(_0x64101e.baiying_project_info);
    chrome.storage.onChanged.addListener((_0x285636, _0x449955) => {
      if ("local" === _0x449955 && _0x285636.baiying_project_info) {
        console.log("商品信息已更新:", _0x285636.baiying_project_info.newValue);
        _0x3a4d08(_0x285636.baiying_project_info.newValue);
      }
    });
  });
  loadUserData();
  waitForElement("xg-right-grid.xg-right-grid", _0x9e07f => {
    const _0x47485f = document.createElement("button");
    _0x47485f.textContent = "下载1";
    _0x47485f.className = "custom-download-button";
    _0x47485f.style.margin = "5px";
    _0x47485f.style.padding = "8px 12px";
    _0x47485f.style.backgroundColor = '#4CAF50';
    _0x47485f.style.color = 'white';
    _0x47485f.style.border = 'none';
    _0x47485f.style.borderRadius = '4px';
    _0x47485f.style.cursor = "pointer";
    _0x47485f.style.zIndex = '1000';
    const _0x5a360f = document.createElement("button");
    _0x5a360f.textContent = "下载2";
    _0x5a360f.className = "custom-download-button";
    _0x5a360f.style.margin = "5px";
    _0x5a360f.style.padding = "8px 12px";
    _0x5a360f.style.backgroundColor = '#4CAF50';
    _0x5a360f.style.color = 'white';
    _0x5a360f.style.border = "none";
    _0x5a360f.style.borderRadius = '4px';
    _0x5a360f.style.cursor = "pointer";
    _0x5a360f.style.zIndex = '1000';
    const _0x2d833a = document.createElement("button");
    _0x2d833a.textContent = "下载3";
    _0x2d833a.className = 'custom-download-button';
    _0x2d833a.style.margin = '5px';
    _0x2d833a.style.padding = "8px 12px";
    _0x2d833a.style.backgroundColor = "#4CAF50";
    _0x2d833a.style.color = 'white';
    _0x2d833a.style.border = 'none';
    _0x2d833a.style.borderRadius = '4px';
    _0x2d833a.style.cursor = "pointer";
    _0x2d833a.style.zIndex = '1000';
    _0x9e07f.prepend(_0x2d833a);
    _0x9e07f.prepend(_0x5a360f);
    _0x9e07f.prepend(_0x47485f);
    _0x47485f.addEventListener("click", async () => {
      chrome.storage.local.get("baiying_project_info", async _0x3eeae6 => {
        console.log("获取的数据:", _0x3eeae6);
        if (!_0x3eeae6 || !_0x3eeae6.baiying_project_info || !_0x3eeae6.baiying_project_info.product_id) {
          return void alert("请先下载图片！");
        }
        let _0x1e7260 = _0x3eeae6.baiying_project_info.product_id;
        if (old_product_id == _0x1e7260) {
          if (user && user.id) {
            if (excuteTime) {
              _0x47485f.disabled = true;
              _0x47485f.innerHTML = '<span>下载中...</span>';
              if (video_url) {
                await downloadResource(video_url, user.id + '_' + excuteTime + '_' + _0x1e7260 + "_video_1.mp4");
              } else {
                console.log("使用handleDownloadButtonClick下载");
                const _0x36f57b = window.location.href.split('/').pop();
                await handleDownloadButtonClick(0x1, _0x36f57b);
              }
              setTimeout(() => {
                _0x47485f.disabled = false;
                _0x47485f.innerHTML = "<span>下载1</span>";
              }, 0x3e8);
            } else {
              alert("执行批次不正确，请检查");
            }
          } else {
            alert("未登录，请重新登录");
          }
        } else {
          alert("商品id已经发生变化，请重新进入页面再下载！");
        }
      });
    });
    _0x5a360f.addEventListener("click", async () => {
      chrome.storage.local.get('baiying_project_info', async _0x43ab16 => {
        console.log("获取的数据:", _0x43ab16);
        if (!_0x43ab16 || !_0x43ab16.baiying_project_info || !_0x43ab16.baiying_project_info.product_id) {
          return void alert("请先下载图片！");
        }
        let _0x4f6fc7 = _0x43ab16.baiying_project_info.product_id;
        if (old_product_id == _0x4f6fc7) {
          if (user && user.id) {
            if (excuteTime) {
              _0x5a360f.disabled = true;
              _0x5a360f.innerHTML = '<span>下载中...</span>';
              if (video_url) {
                await downloadResource(video_url, user.id + '_' + excuteTime + '_' + _0x4f6fc7 + "_video_2.mp4");
              } else {
                console.log("使用handleDownloadButtonClick下载");
                const _0x145807 = window.location.href.split('/').pop();
                await handleDownloadButtonClick(0x2, _0x145807);
              }
              setTimeout(() => {
                _0x5a360f.disabled = false;
                _0x5a360f.innerHTML = "<span>下载2</span>";
              }, 0x3e8);
            } else {
              alert("执行批次不正确，请检查");
            }
          } else {
            alert("未登录，请重新登录");
          }
        } else {
          alert('商品id已经发生变化，请重新进入页面再下载！');
        }
      });
    });
    _0x2d833a.addEventListener("click", async () => {
      chrome.storage.local.get("baiying_project_info", async _0x2b6285 => {
        console.log("获取的数据:", _0x2b6285);
        if (!_0x2b6285 || !_0x2b6285.baiying_project_info || !_0x2b6285.baiying_project_info.product_id) {
          return void alert("请先下载图片！");
        }
        let _0x11925e = _0x2b6285.baiying_project_info.product_id;
        if (old_product_id == _0x11925e) {
          if (user && user.id) {
            if (excuteTime) {
              _0x2d833a.disabled = true;
              _0x2d833a.innerHTML = "<span>下载中...</span>";
              if (video_url) {
                await downloadResource(video_url, user.id + '_' + excuteTime + '_' + _0x11925e + '_video_3.mp4');
              } else {
                console.log("使用handleDownloadButtonClick下载");
                const _0x2c4ae2 = window.location.href.split('/').pop();
                await handleDownloadButtonClick(0x3, _0x2c4ae2);
              }
              setTimeout(() => {
                _0x2d833a.disabled = false;
                _0x2d833a.innerHTML = "<span>下载3</span>";
              }, 0x3e8);
            } else {
              alert("执行批次不正确，请检查");
            }
          } else {
            alert("未登录，请重新登录");
          }
        } else {
          alert('商品id已经发生变化，请重新进入页面再下载！');
        }
      });
    });
  });
});
const FileHandler = {
  'cleanFileName': function (_0x5ddaee) {
    if (!_0x5ddaee) {
      _0x5ddaee = "抖音视频";
    }
    return (_0x5ddaee = (_0x5ddaee = _0x5ddaee.replace(/[\\/？?*.,"‘’|<>{}[\]【】：:、^$!~`]/g, '')).replace(/展开/g, '') || '未知名称').replace(/[<>:"/\\|?*\s]/g, '_');
  },
  'truncateTo50Chars': function (_0x23cc6a) {
    return _0x23cc6a && _0x23cc6a.length > 0x32 ? _0x23cc6a.substring(0x0, 0x32) : _0x23cc6a;
  },
  'convertJpgToPng': function (_0x1303e9) {
    return new Promise((_0x180fa5, _0x21a08a) => {
      const _0xe7855e = new Image();
      _0xe7855e.setAttribute('crossOrigin', "anonymous");
      _0xe7855e.src = _0x1303e9;
      _0xe7855e.onload = function () {
        const _0x301991 = document.createElement("canvas");
        _0x301991.width = _0xe7855e.width;
        _0x301991.height = _0xe7855e.height;
        _0x301991.getContext('2d').drawImage(_0xe7855e, 0x0, 0x0);
        _0x180fa5(_0x301991.toDataURL("image/png"));
      };
      _0xe7855e.onerror = _0x21a08a;
    });
  },
  'saveAsZip': async function (_0x3c3b2e, _0x529605, _0x14791b) {
    if (!_0x14791b) {
      return;
    }
    const _0x30d0ed = new t();
    let _0x4f90b5 = 0x0;
    let _0x42bc00 = 0x0;
    if ('single' === _0x529605.type) {
      if (_0x14791b.url?.['startsWith']("http:")) {
        _0x14791b.url = _0x14791b.url.replaceAll("http:", 'https:');
      }
      fetch(_0x14791b.url).then(_0x502f97 => _0x502f97.blob()).then(_0x147a53 => {
        const _0x5a6bed = document.createElement('a');
        document.body.appendChild(_0x5a6bed);
        _0x5a6bed.style.display = 'none';
        const _0x1a8827 = window.URL.createObjectURL(_0x147a53);
        _0x5a6bed.href = _0x1a8827;
        _0x5a6bed.download = this.truncateTo50Chars(this.cleanFileName(_0x3c3b2e)) + ".mp4";
        _0x5a6bed.click();
        document.body.removeChild(_0x5a6bed);
        window.URL.revokeObjectURL(_0x1a8827);
        if (_0x529605.callback) {
          _0x529605.callback(_0x529605.id);
        }
      });
    } else {
      if ('batchs' === _0x529605.type) {
        const _0xa0a279 = Array.isArray(_0x14791b) ? _0x14791b : [_0x14791b];
        const _0x82ea6d = [];
        const _0xd79489 = new el(0x14);
        _0x42bc00 = _0xa0a279.length;
        _0xa0a279.forEach(_0x101d78 => {
          let _0xf57a3c = this.getFileName(_0x101d78, _0x529605.fileNameFormat);
          if (_0x82ea6d.includes(_0xf57a3c)) {
            _0xf57a3c = _0xf57a3c + '_' + _0x101d78.vid + ".mp4";
          } else {
            _0x82ea6d.push(_0xf57a3c);
            _0xf57a3c = _0xf57a3c + ".mp4";
          }
          _0x4f90b5++;
          const _0x4e2bc4 = {
            'progress': _0x518ca2 => {
              if (_0x529605.progress) {
                _0x529605.progress(_0x101d78.vid, Math.round(_0x518ca2.percent));
              }
            },
            'callback': (_0x554984, _0x37dba1) => {
              if (_0x554984) {
                console.log("获取二进制数据错误", _0x554984);
              } else {
                _0x30d0ed.file(_0xf57a3c, _0x37dba1, {
                  'binary': true
                });
              }
              if (_0x554984 && _0x529605.callback) {
                _0x529605.callback(_0x529605.id);
              }
              _0x4f90b5++;
              if (_0x4f90b5 === _0x42bc00) {
                if (_0x529605.progress) {
                  _0x529605.progress("all_done", 0x64);
                }
                (() => {
                  let _0x26d527 = _0x3c3b2e + '_' + _0x529605.type;
                  if (_0x529605.name) {
                    _0x26d527 = _0x3c3b2e + '_' + _0x529605.name;
                  }
                  const _0x33b564 = a().createWriteStream(_0x26d527 + ".zip").getWriter();
                  _0x30d0ed.generateInternalStream({
                    'type': "blob",
                    'compression': 'DEFLATE',
                    'compressionOptions': {
                      'level': 0x9
                    }
                  }).on("data", (_0x3093f6, _0x39394c) => {
                    if (_0x529605.compressProgress) {
                      _0x529605.compressProgress(Math.round(_0x39394c.percent));
                    }
                    _0x33b564.write(_0x3093f6);
                  }).on('error', _0x28891d => console.error(_0x28891d)).on("end", () => {
                    if (_0x529605.compressProgress) {
                      _0x529605.compressProgress(-0x64);
                    }
                    _0x33b564.close();
                  }).resume();
                })();
              }
            }
          };
          _0xd79489.enqueue(new Qo(_0x101d78, _0x4e2bc4)).then(() => {})["catch"](_0x5d8701 => {
            console.log('获取异常，重试：', _0x101d78.url, _0x5d8701);
            _0x4e2bc4.flag = true;
            _0xd79489.enqueue(new Qo(_0x101d78, _0x4e2bc4));
          });
        });
      }
    }
  },
  async 'save2Directory'(_0x3c443b, _0x55e0ef, _0x212442) {
    try {
      let _0x276113 = 0x0;
      let _0x3e33fd = _0x212442.length;
      const _0x15110a = [];
      const _0x275d4c = new el(0x14);
      _0x212442.forEach(_0x11e7e5 => {
        _0x3e33fd++;
        let _0x1e64a7 = this.getFileName(_0x11e7e5, _0x55e0ef.fileNameFormat);
        if (_0x15110a.includes(_0x1e64a7)) {
          _0x1e64a7 = _0x1e64a7 + '_' + _0x11e7e5.vid + ".mp4";
        } else {
          _0x15110a.push(_0x1e64a7);
          _0x1e64a7 = _0x1e64a7 + ".mp4";
        }
        const _0x354a31 = {
          'progress': _0x210e25 => {
            if (_0x55e0ef.progress) {
              _0x55e0ef.progress(_0x11e7e5.vid, Math.round(_0x210e25.percent));
            }
          },
          'callback': async (_0x39a862, _0x55998d) => {
            if (_0x39a862) {
              console.log("获取二进制数据错误", _0x39a862);
            } else {
              const _0x4871ef = await _0x3c443b.getFileHandle(_0x1e64a7, {
                'create': true
              });
              const _0x5da8f4 = await _0x4871ef.createWritable();
              await _0x5da8f4.write(_0x55998d);
              await _0x5da8f4.close();
            }
            if (_0x39a862 && _0x55e0ef.callback) {
              _0x55e0ef.callback(_0x55e0ef.id);
            }
            _0x276113++;
            if (_0x276113 === _0x3e33fd && _0x55e0ef.progress) {
              _0x55e0ef.progress("all_done", 0x64);
            }
          }
        };
        _0x275d4c.enqueue(new Qo(_0x11e7e5, _0x354a31)).then(() => {})['catch'](_0x306d31 => {
          console.log('获取异常，重试：', _0x11e7e5.url, _0x306d31);
          _0x354a31.flag = true;
          _0x275d4c.enqueue(new Qo(_0x11e7e5, _0x354a31));
        });
      });
    } catch (_0x322ad3) {
      console.error('保存文件时出错:', _0x322ad3);
    }
  },
  async 'getDirectoryHandle'() {
    try {
      const _0x18c659 = await window.showDirectoryPicker();
      return 'granted' !== (await _0x18c659.queryPermission({
        'mode': 'readwrite'
      })) && (console.log('用户未授予读写权限'), "granted" !== (await _0x18c659.requestPermission({
        'mode': "readwrite"
      }))) ? console.log("用户拒绝授予读写权限") : _0x18c659;
    } catch (_0xb504cc) {
      console.error("获取文件夹句柄失败:", _0xb504cc);
      throw _0xb504cc;
    }
  },
  'getFileName': function (_0x189d1a, _0x1514d3) {
    let _0x5d0f9d = _0x189d1a.title || _0x189d1a.desc ? this.truncateTo50Chars(this.cleanFileName(_0x189d1a.title || _0x189d1a.desc)) : _0x189d1a.vid;
    if (_0x1514d3) {
      switch (_0x1514d3) {
        case "date_title":
          _0x5d0f9d = _0x189d1a.date ? _0x189d1a.date.replaceAll('-', '') + '_' + _0x5d0f9d : _0x5d0f9d;
          break;
        case "date_title_productId":
          _0x5d0f9d = (_0x189d1a.date ? _0x189d1a.date.replaceAll('-', '') + '_' + _0x5d0f9d : _0x5d0f9d) + '_' + (_0x189d1a.goods?.["productId"] ? _0x189d1a.goods.productId : '');
          break;
        case 'vid_productId':
          _0x5d0f9d = _0x189d1a.vid + '_' + (_0x189d1a.goods?.["productId"] ? _0x189d1a.goods.productId : '');
          break;
        case "date_vid":
          _0x5d0f9d = (_0x189d1a.date ? _0x189d1a.date.replaceAll('-', '') : '') + '_' + _0x189d1a.vid;
          break;
        case "title_productId":
          _0x5d0f9d = _0x5d0f9d + '_' + (_0x189d1a.goods?.["productId"] ? _0x189d1a.goods.productId : '');
      }
    } else {
      _0x5d0f9d = _0x189d1a.date ? _0x189d1a.date.replaceAll('-', '') + '_' + _0x5d0f9d : _0x5d0f9d;
    }
    return _0x5d0f9d;
  },
  'downloadStream': async function (_0x35a242, _0x539818) {
    try {
      const _0x4e7316 = await fetch(_0x35a242);
      const _0x152f93 = _0x4e7316.headers.get("content-length");
      const _0x2cfcfe = parseInt(_0x152f93, 0xa);
      let _0x5411df = 0x0;
      const _0x66e540 = [];
      const _0x14a3dc = _0x4e7316?.["body"]?.['getReader']();
      for (;;) {
        const {
          done: _0x44518a,
          value: _0x1403b1
        } = await _0x14a3dc.read();
        if (_0x44518a) {
          break;
        }
        _0x5411df += _0x1403b1.byteLength;
        _0x539818.progress({
          'percent': 0x64 * _0x5411df / _0x2cfcfe
        });
        _0x66e540.push(_0x1403b1);
      }
      _0x539818.callback(null, new Blob(_0x66e540));
    } catch (_0x2d7ca4) {
      if (!_0x539818.flag) {
        console.log("downloadStream:", _0x2d7ca4);
        throw _0x2d7ca4;
      }
      _0x539818.callback(_0x2d7ca4, null);
    }
  },
  'handleExportField': function (_0x2b5ff9, _0x1b7258, _0x55b91a) {
    let _0x2bfdcd = '';
    const _0x74a5c9 = {};
    for (const _0x2a9223 of _0x1b7258) switch (_0x2a9223) {
      case "nickName":
        if ('json' === _0x2b5ff9) {
          _0x74a5c9.用户昵称 = _0x55b91a.author.nickName;
        } else {
          _0x2bfdcd += _0x55b91a ? _0x55b91a.author.nickName + "\t" : '用户昵称,';
        }
        break;
      case 'secUid':
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.用户链接 = "https://www.douyin.com/user/" + _0x55b91a.author.secUid;
        } else {
          _0x2bfdcd += _0x55b91a ? "https://www.douyin.com/user/" + _0x55b91a.author.secUid + "\t" : "用户链接,";
        }
        break;
      case "videoDetail":
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.视频详情 = "https://www.douyin.com/video/" + _0x55b91a.vid;
        } else {
          _0x2bfdcd += _0x55b91a ? "https://www.douyin.com/video/" + _0x55b91a.vid + "\t" : "视频详情,";
        }
        break;
      case "desc":
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.视频描述 = _0x55b91a.desc;
        } else {
          _0x2bfdcd += _0x55b91a ? _0x55b91a.desc + "\t" : "视频描述,";
        }
        break;
      case "digg":
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.点赞 = _0x55b91a.statistics.digg;
        } else {
          _0x2bfdcd += _0x55b91a ? _0x55b91a.statistics.digg + "\t" : '点赞,';
        }
        break;
      case 'collect':
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.收藏 = _0x55b91a.statistics.collect;
        } else {
          _0x2bfdcd += _0x55b91a ? _0x55b91a.statistics.collect + "\t" : "收藏,";
        }
        break;
      case "comment":
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.评论 = _0x55b91a.statistics.comment;
        } else {
          _0x2bfdcd += _0x55b91a ? _0x55b91a.statistics.comment + "\t" : '评论,';
        }
        break;
      case 'share':
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.分享 = _0x55b91a.statistics.share;
        } else {
          _0x2bfdcd += _0x55b91a ? _0x55b91a.statistics.share + "\t" : "分享,";
        }
        break;
      case "productId":
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.商品ID = _0x55b91a.goods?.["productId"] ? _0x55b91a.goods.productId : '';
        } else {
          _0x2bfdcd += _0x55b91a ? (_0x55b91a.goods?.["productId"] ? _0x55b91a.goods.productId : '') + "\t" : "商品ID,";
        }
        break;
      case "title":
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.商品标题 = _0x55b91a.goods?.['title'] ? _0x55b91a.goods.title : '';
        } else {
          _0x2bfdcd += _0x55b91a ? (_0x55b91a.goods?.["title"] ? _0x55b91a.goods.title : '') + "\t" : "商品标题,";
        }
        break;
      case "price":
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.商品价格 = _0x55b91a.goods?.["price"] ? _0x55b91a.goods.price : '';
        } else {
          _0x2bfdcd += _0x55b91a ? (_0x55b91a.goods?.['price'] ? _0x55b91a.goods.price : '') + "\t" : "商品价格,";
        }
        break;
      case "url":
        if ("json" === _0x2b5ff9) {
          _0x74a5c9.商品URL = _0x55b91a.goods?.['url'] ? _0x55b91a.goods.url : '';
        } else {
          _0x2bfdcd += _0x55b91a ? (_0x55b91a.goods?.["url"] ? _0x55b91a.goods.url : '') + "\t" : "商品URL,";
        }
        break;
      case 'sales':
        if ('json' === _0x2b5ff9) {
          _0x74a5c9.商品销量 = _0x55b91a.goods?.["sales"] ? _0x55b91a.goods.sales : '';
        } else {
          _0x2bfdcd += _0x55b91a ? (_0x55b91a.goods?.["sales"] ? _0x55b91a.goods.sales : '') + "\t" : "商品销量,";
        }
    }
    return "json" === _0x2b5ff9 ? _0x74a5c9 : _0x2bfdcd + "\n";
  },
  'copyCSV': function (_0x26f508, _0x11590b) {
    let _0x36b703 = '';
    _0x11590b.forEach(_0x717979 => {
      _0x36b703 += this.handleExportField("text", _0x26f508.fields, _0x717979);
    });
    return _0x36b703;
  },
  'downloadXlsx': function (_0x2a8a95, _0x3af3c6) {
    const _0x722025 = Zo.book_new();
    const _0x2e882 = _0x3af3c6.map(_0x322861 => this.handleExportField("json", _0x2a8a95.fields, _0x322861));
    const _0x34d72b = Zo.json_to_sheet(_0x2e882);
    let _0x1cbf6d = this.cleanFileName(_0x2a8a95.name);
    if (_0x1cbf6d.length > 0x1e) {
      _0x1cbf6d = _0x1cbf6d.substring(0x0, 0x1e);
    }
    Zo.book_append_sheet(_0x722025, _0x34d72b, _0x1cbf6d);
    const _0x30d509 = Bo(_0x722025, {
      'bookType': "xlsx",
      'type': "array"
    });
    const _0x3b5786 = new Blob([_0x30d509], {
      'type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8'
    });
    if (_0x2a8a95.callback) {
      _0x2a8a95.callback(_0x2a8a95.id);
    }
    this.downloadFile(_0x3b5786, _0x2a8a95.filename + ".xlsx");
  },
  'downloadUserXlsx': function (_0xc349b, _0x56b8ec) {
    const _0x3386ad = Zo.book_new();
    let _0x121640 = null;
    const _0x391bef = _0x56b8ec.map(_0x5a700e => (_0x121640 || (_0x121640 = _0x5a700e.name), {
      '视频ID': '' + _0x5a700e.vid,
      '视频封面': '' + _0x5a700e.cover,
      '视频描述': '' + (_0x5a700e.title || ''),
      '视频详情': 'https://www.douyin.com/video/' + _0x5a700e.awemeId,
      '视频下载URL': '' + _0x5a700e.url,
      '是否置顶': '' + (_0x5a700e.isTop || ''),
      '发布日期': '' + _0x5a700e.date,
      '合集ID': '' + (_0x5a700e.mixId && "undefined" != _0x5a700e.mixId ? _0x5a700e.mixId : ''),
      '合集名称': '' + (_0x5a700e.mixName || ''),
      '时长/秒': '' + (_0x5a700e.duration ? Math.round(_0x5a700e.duration / 0x3e8) : ''),
      '点赞量': '' + (_0x5a700e.stats.digg_count || 0x0),
      '收藏量': '' + (_0x5a700e.stats.collect_count || 0x0),
      '评论量': '' + (_0x5a700e.stats.comment_count || 0x0),
      '转发量': '' + (_0x5a700e.stats.share_count || 0x0)
    }));
    const _0x41796d = Zo.json_to_sheet(_0x391bef);
    let _0x3acb67 = this.cleanFileName(_0xc349b.name || _0x121640);
    if (_0x3acb67.length > 0x1e) {
      _0x3acb67 = _0x3acb67.substring(0x0, 0x1e);
    }
    Zo.book_append_sheet(_0x3386ad, _0x41796d, _0x3acb67);
    const _0x582943 = Bo(_0x3386ad, {
      'bookType': "xlsx",
      'type': 'array'
    });
    const _0x3229e4 = new Blob([_0x582943], {
      'type': "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8"
    });
    if (_0xc349b.callback) {
      _0xc349b.callback(_0xc349b.id);
    }
    this.downloadFile(_0x3229e4, _0xc349b.filename + '_' + _0x121640 + '.xlsx');
  },
  'downloadFile': function (_0xf329b3, _0x1997b4) {
    const _0x292c58 = document.createElement('a');
    _0x292c58.href = URL.createObjectURL(_0xf329b3);
    _0x292c58.download = _0x1997b4;
    document.body.appendChild(_0x292c58);
    _0x292c58.click();
    document.body.removeChild(_0x292c58);
    URL.revokeObjectURL(_0x292c58.href);
  }
};
async function downloadVideo(_0x21a35c, _0x19b818, _0x407c99) {
  chrome.storage.local.get("baiying_project_info", async _0x4e28d3 => {
    console.log("获取的数据:", _0x4e28d3);
    if (!_0x4e28d3 || !_0x4e28d3.baiying_project_info || !_0x4e28d3.baiying_project_info.product_id) {
      return void alert("请先下载图片！");
    }
    const _0x349a54 = _0x4e28d3.baiying_project_info.product_id;
    if (old_product_id != _0x349a54) {
      return void alert("商品id已经发生变化，请重新进入页面再下载！");
    }
    if (_0x21a35c.url?.["startsWith"]("http:")) {
      _0x21a35c.url = _0x21a35c.url.replaceAll("http:", "https:");
    }
    let _0x5ed4a1 = null;
    try {
      _0x5ed4a1 = await fetch(_0x21a35c.url);
      const _0x2ece5e = _0x5ed4a1.headers.get("content-length");
      const _0x39d21f = parseInt(_0x2ece5e, 0xa);
      let _0x3b5634 = 0x0;
      const _0x226c43 = [];
      const _0x5bb69f = _0x5ed4a1?.["body"]?.["getReader"]();
      for (;;) {
        const {
          done: _0x56b104,
          value: _0x4ff3bb
        } = await _0x5bb69f.read();
        if (_0x56b104) {
          break;
        }
        _0x3b5634 += _0x4ff3bb.byteLength;
        if (_0x19b818) {
          _0x19b818(Math.round(0x64 * _0x3b5634 / _0x39d21f));
        }
        _0x226c43.push(_0x4ff3bb);
      }
      const _0x301acb = (user?.['id'] || '') + '_' + (excuteTime || '') + '_' + _0x349a54 + "_video_" + fileNumber + ".mp4";
      FileHandler.downloadFile(new Blob(_0x226c43), _0x301acb);
      console.log("下载文件: " + _0x301acb);
      if (_0x407c99) {
        _0x407c99();
      }
    } catch (_0x35be18) {
      console.error("fetch操作:", _0x35be18);
    }
  });
}
async function downloadResource(_0x34061e, _0xab507a, _0x565873 = '') {
  const _0xba1c10 = _0x565873 ? _0x565873 + '/' + _0xab507a : _0xab507a;
  try {
    if (!_0x34061e || !_0x34061e.startsWith("http")) {
      alert("无效的URL: " + _0x34061e);
      throw new Error("无效的URL: " + _0x34061e);
    }
    console.log("开始下载: " + _0xba1c10);
    const _0x226344 = await fetch(_0x34061e, {
      'method': "GET",
      'mode': "cors",
      'credentials': "same-origin"
    });
    if (!_0x226344.ok) {
      throw new Error("HTTP错误: " + _0x226344.status + " " + _0x226344.statusText);
    }
    const _0x367fb4 = _0x226344.headers.get("Content-Type");
    const _0x15b7a6 = _0x226344.headers.get('Content-Length');
    console.log("info", "响应信息：类型=" + _0x367fb4 + '，预计大小=' + (_0x15b7a6 ? (_0x15b7a6 / 0x400 / 0x400).toFixed(0x2) + 'MB' : '未知'));
    if (!_0x367fb4?.["startsWith"]("video/")) {
      throw new Error("非视频类型: " + _0x367fb4);
    }
    const _0x40e28d = _0x226344.body.getReader();
    const _0x22736b = [];
    let _0x260f22 = 0x0;
    for (console.log("info", "开始分块读取数据...");;) {
      const {
        done: _0x5a80bc,
        value: _0x47f9be
      } = await _0x40e28d.read();
      if (_0x5a80bc) {
        break;
      }
      _0x22736b.push(_0x47f9be);
      _0x260f22 += _0x47f9be.byteLength;
      if (_0x15b7a6) {
        const _0x2d2980 = _0x260f22 / _0x15b7a6 * 0x64;
        if (_0x2d2980 % 0xa < 0.1 || _0x260f22 % 0x500000 < 0x400) {
          console.log("info", "下载进度: " + _0x2d2980.toFixed(0x1) + "% (" + (_0x260f22 / 0x400 / 0x400).toFixed(0x2) + "MB/" + (_0x15b7a6 / 0x400 / 0x400).toFixed(0x2) + "MB)");
        }
      } else {
        console.log("info", "已读取: " + (_0x260f22 / 0x400 / 0x400).toFixed(0x2) + 'MB');
      }
    }
    if (_0x15b7a6 && _0x260f22 !== parseInt(_0x15b7a6)) {
      throw new Error("数据不完整：实际读取" + _0x260f22 + '字节，预期' + _0x15b7a6 + '字节');
    }
    console.log("info", "分块读取完成，共" + _0x22736b.length + '块，开始合并为Blob');
    const _0x2c5f6e = new Blob(_0x22736b, {
      'type': _0x367fb4
    });
    const _0x22e36a = document.createElement('a');
    _0x22e36a.href = URL.createObjectURL(_0x2c5f6e);
    _0x22e36a.download = _0xba1c10;
    _0x22e36a.style.display = "none";
    document.body.appendChild(_0x22e36a);
    _0x22e36a.click();
    setTimeout(() => {
      document.body.removeChild(_0x22e36a);
      URL.revokeObjectURL(_0x22e36a.href);
    }, 0x3e8);
    return {
      'success': true,
      'filename': _0xba1c10
    };
  } catch (_0x48484d) {
    console.error("下载 " + _0xba1c10 + " 失败:", _0x48484d);
    return {
      'success': false,
      'filename': _0xba1c10,
      'error': _0x48484d.message
    };
  }
}
function initiateDownload(_0x234518, _0x2ace17) {
  downloadVideo(_0x2ace17, _0x172092 => {}, () => {
    console.log("下载完成");
  });
}
function extractAsMap(_0x584697) {
  const _0x274dff = _0x584697.replace(/\\/g, '').replace(/\s+/g, " ").replace(/[\x00-\x1F\x7F]/g, '').replace(/"{2,}/g, "\"").match(/"data"\s*:\s*\[\s*({[^}]*"aweme_info"\s*:{[^}]+})[,\s]*(.{0,1000})*/);
  if (!_0x274dff) {
    return '{}';
  }
  const _0x5390f8 = _0x274dff[0x0].split(/"type"\s*:\s*1/).filter(_0x5647a6 => _0x5647a6.includes("\"aweme_info\""));
  const _0x552c3f = {};
  _0x5390f8.forEach(_0x60a719 => {
    const _0x1c5fbf = "\"type\":1" + _0x60a719;
    const _0x3663e1 = extractSingleField(_0x1c5fbf, /"aweme_info"\s*:\s*\{"aweme_id"\s*:\s*"([^"]+)"/);
    const _0x193bfb = extractPlayAddrs(_0x1c5fbf);
    if (_0x3663e1 && _0x193bfb.length > 0x0) {
      _0x552c3f[_0x3663e1] = _0x193bfb[0x0];
    }
  });
  console.log("✅ 生成 Map 结构，共 " + Object.keys(_0x552c3f).length + " 个有效条目");
  return _0x552c3f;
}
function extractSingleField(_0x328f06, _0x21abf1) {
  const _0x22756b = _0x328f06.match(_0x21abf1);
  return _0x22756b && _0x22756b[0x1] ? _0x22756b[0x1].trim() : null;
}
function extractPlayAddrs(_0x4cc875) {
  const _0x354296 = _0x4cc875.match(/"video"\s*:\s*\{"play_addr"\s*:\s*\{([^}]+)\}/) || _0x4cc875.match(/"play_addr"\s*:\s*\{([^}]+)\}/);
  if (!_0x354296 || !_0x354296[0x1]) {
    return [];
  }
  const _0x45e89e = _0x354296[0x1].match(/"url_list"\s*:\s*\[(["'].*?["'](?:,\s*["'].*?["'])*)\]/);
  if (!_0x45e89e || !_0x45e89e[0x1]) {
    return [];
  }
  const _0x55e559 = [];
  _0x45e89e[0x1].split(/,\s*/).forEach(_0xeecfe3 => {
    const _0x1867a0 = _0xeecfe3.replace(/["']/g, '').trim();
    if (_0x1867a0) {
      _0x55e559.push(_0x1867a0);
    }
  });
  return _0x55e559;
}
function processStringFinal(_0xd36d0b) {
  try {
    return extractAsMap(_0xd36d0b);
  } catch (_0x261351) {
    console.error("⚠️ 提取失败：" + _0x261351.message);
    return '{}';
  }
}
window.addEventListener("message", async _0x10f4a0 => {
  console.log("【智能选品】Listener message", _0x10f4a0.data);
  const _0x3b02b9 = _0x10f4a0.data;
  const _0x47ea9f = _0x3b02b9?.["action"];
  const _0x145a31 = _0x3b02b9?.["trigger"];
  if ("DBDY_ACCQURE2_RES" === _0x47ea9f) {
    if (_0x145a31) {
      initiateDownload(_0x145a31, normalizeVideoData(_0x3b02b9.res.aweme_detail));
    }
  } else {
    if ('DBDY_SEARCH_ACCQURE_RES' === _0x47ea9f) {
      _0x3b02b9.res.data.forEach(_0x51878c => {
        if (_0x51878c.aweme_info && _0x51878c.aweme_info.aweme_id) {
          video_map[_0x51878c.aweme_info.aweme_id] = _0x51878c.aweme_info.video.play_addr.url_list[0x2];
        } else {
          console.log("item", _0x51878c);
        }
      });
      console.log("searchSingle res", video_map);
    } else {
      if ("DBDY_SEARCH_FIRST_ACCQURE_RES" === _0x47ea9f) {
        const _0x56c5d2 = processStringFinal(_0x3b02b9.res);
        for (const _0x2fdfdd in _0x56c5d2) video_map[_0x2fdfdd] = _0x56c5d2[_0x2fdfdd];
        console.log("searchSingle2 res", video_map);
      } else if ('DBDY_INFO_ACCQURE_RES' === _0x47ea9f) {
        video_url = _0x3b02b9.res.aweme_detail.video.play_addr.url_list[0x0];
        console.log("searchSingle3 res", video_url);
      }
    }
  }
}, false);