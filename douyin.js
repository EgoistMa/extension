let video_url = '';
let user = {
  'id': "anonymous"
};
let excuteTime = null;
function getMidnightTimestamp() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
}
function loadUserData() {
  chrome.storage.local.get("xuanpin_user", function (result) {
    if (result.xuanpin_user) {
      try {
        user = JSON.parse(result.xuanpin_user);
        console.log("xuanpin_user======>", user);
      } catch (error) {
        console.warn("xuanpin_user 解析失败:", error);
        user = {
          'id': "anonymous"
        };
      }
    }
  });
  excuteTime = getMidnightTimestamp();
}
function earlyInjectScript() {
  try {
    console.info("【智能选品】开始尝试注入脚本");
    injectScriptToPage();
  } catch (error) {
    console.error("【智能选品】初始化注入脚本失败:", error);
    setTimeout(earlyInjectScript, 0x32);
  }
}
function injectScriptToPage() {
  try {
    if (!document.documentElement) {
      console.warn('【智能选品】DOM元素尚未准备好，稍后重试');
      return void setTimeout(injectScriptToPage, 0xa);
    }
    const scriptElement = document.createElement('script');
    scriptElement.async = false;
    scriptElement.defer = false;
    scriptElement.src = chrome.runtime.getURL("assets/douyin-insert.js");
    document.documentElement.appendChild(scriptElement);
    scriptElement.onload = function () {
      console.info("【智能选品】douyin-insert.js脚本加载成功.");
    };
    scriptElement.onerror = function () {
      console.error("【智能选品】douyin-insert.js脚本加载失败.");
      setTimeout(injectScriptToPage, 0x3e8);
    };
  } catch (error) {
    console.error("【智能选品】注入脚本过程出错:", error);
    setTimeout(injectScriptToPage, 0x32);
  }
}
earlyInjectScript();
window.addEventListener("message", function (event) {
  try {
    if (event.data && event.data.type && 'REQUEST_STORED_REQUESTS' === event.data.type && 'douyin-insert.js' === event.data.from) {
      console.log('【智能选品】收到页面脚本请求，获取存储的请求信息');
      chrome.storage.local.get(null, function (allStorage) {
        const storedRequests = [];
        for (const key in allStorage) if (key.startsWith("douyin_request_")) {
          storedRequests.push(allStorage[key]);
          chrome.storage.local.remove(key);
        }
        if (storedRequests.length > 0x0) {
          console.log("【智能选品】获取到存储的请求数量:", storedRequests.length);
          window.postMessage({
            'type': 'PRE_CAPTURED_REQUESTS',
            'requests': storedRequests
          }, '*');
        }
      });
    }
  } catch (error) {
    console.error("【智能选品】处理页面脚本消息失败:", error);
  }
}, false);
let video_map = {};
async function getRequestParams(paramType) {
  const urlParams = await parseUrlParameters();
  return "userParams" === paramType ? {
    'device_platform': "webapp",
    'aid': urlParams.aid || 0x18ef,
    'channel': 'channel_pc_web',
    'locate_item_id': urlParams.locate_item_id || "7377694813719678220",
    'locate_query': false,
    'show_live_replay_strategy': urlParams.show_live_replay_strategy || 0x1,
    'need_time_list': urlParams.need_time_list || 0x1,
    'time_list_query': urlParams.time_list_query || 0x0,
    'whale_cut_token': urlParams.whale_cut_token || '',
    'cut_version': urlParams.cut_version || 0x1,
    'count': 0x14,
    'publish_video_strategy_type': urlParams.publish_video_strategy_type || 0x2,
    'update_version_code': urlParams.update_version_code || "170400",
    'pc_client_type': urlParams.pc_client_type || 0x1,
    'version_code': urlParams.version_code || "290100",
    'version_name': urlParams.version_name || "29.1.0",
    'cookie_enabled': urlParams.cookie_enabled || true,
    'screen_width': urlParams.screen_width || 0x72b,
    'screen_height': urlParams.screen_height || 0x408,
    'browser_language': urlParams.browser_language || "zh-CN",
    'browser_platform': urlParams.browser_platform || "Linux x86_64",
    'browser_name': urlParams.browser_name || "Chrome",
    'browser_version': urlParams.browser_version || "124.0.0.0",
    'browser_online': urlParams.browser_online || true,
    'engine_name': urlParams.engine_name || "Blink",
    'engine_version': urlParams.engine_version || "124.0.0.0",
    'os_name': urlParams.os_name || "Linux",
    'os_version': urlParams.os_version || "x86_64",
    'cpu_core_num': urlParams.cpu_core_num || 0x10,
    'device_memory': urlParams.device_memory || 0x8,
    'platform': urlParams.platform || 'PC',
    'downlink': urlParams.downlink || 0xa,
    'effective_type': urlParams.effective_type || '4g',
    'round_trip_time': urlParams.round_trip_time || 0x64,
    'webid': getWebUserId() || '7373573059258828323'
  } : "detailParams" === paramType ? {
    'device_platform': 'webapp',
    'aid': urlParams.aid || 0x18ef,
    'channel': "channel_pc_web",
    'update_version_code': "170400",
    'pc_client_type': urlParams.pc_client_type || 0x1,
    'version_code': urlParams.version_code || "190500",
    'version_name': urlParams.version_name || "19.5.0",
    'cookie_enabled': urlParams.cookie_enabled || true,
    'screen_width': urlParams.screen_width || 0x72b,
    'screen_height': urlParams.screen_height || 0x408,
    'browser_language': urlParams.browser_language || "zh-CN",
    'browser_platform': urlParams.browser_platform || "Linux x86_64",
    'browser_name': urlParams.browser_name || 'Chrome',
    'browser_version': urlParams.browser_version || "124.0.0.0",
    'browser_online': urlParams.browser_online || true,
    'engine_name': urlParams.engine_name || "Blink",
    'engine_version': urlParams.engine_version || "124.0.0.0",
    'os_name': urlParams.os_name || "Linux",
    'os_version': urlParams.os_version || "x86_64",
    'cpu_core_num': urlParams.cpu_core_num || 0x10,
    'device_memory': urlParams.device_memory || 0x8,
    'platform': 'PC',
    'downlink': urlParams.downlink || 0xa,
    'effective_type': urlParams.effective_type || '4g',
    'round_trip_time': urlParams.round_trip_time || 0x32,
    'webid': getWebUserId() || "7373573059258828323"
  } : null;
}
let fileNumber = 0x1;
const AUTO_DOWNLOAD_CONFIG = {
  'minDuration': 0x0,
  'maxDuration': 0x3c,
  'limit': 0x3
};
let autoDownloadQueue = [];
let autoDownloading = false;
let currentAutoDownload = null;
const autoDownloadedSet = new Set();
let autoDownloadInitialized = false;
let autoDownloadFileIndex = 1;
let autoDownloadResults = [];
let concatInProgress = false;
let lastSearchKeyword = null;
function waitForElement(selector, callback) {
  const checkElement = () => {
    const element = document.querySelector(selector);
    return !!element && (callback(element), true);
  };
  if (checkElement()) {
    return;
  }
  const observer = new MutationObserver(mutations => {
    if (checkElement()) {
      observer.disconnect();
    }
  });
  const startObserving = () => {
    if (document.body) {
      observer.observe(document.body, {
        'childList': true,
        'subtree': true,
        'attributes': false
      });
    } else {
      setTimeout(startObserving, 0x64);
    }
  };
  startObserving();
}
function getWebUserId() {
  try {
    let cacheTokens = localStorage.getItem("__tea_cache_tokens_6383");
    if (cacheTokens) {
      let userId = JSON.parse(cacheTokens)?.["user_unique_id"];
      if (!userId) {
        cacheTokens = localStorage.getItem("__tea_cache_tokens_7497");
        if (cacheTokens) {
          userId = JSON.parse(cacheTokens)?.["user_unique_id"];
        }
      }
      return userId || '';
    }
    return '';
  } catch (error) {
    console.log("获取用户ID失败:", error);
    return '';
  }
}
function parseUrlParameters() {
  const url = window.location.href;
  const questionMarkIndex = url.indexOf('?');
  if (-0x1 === questionMarkIndex) {
    return {};
  }
  const queryString = url.substring(questionMarkIndex + 0x1);
  if (!queryString) {
    return {};
  }
  const pairs = queryString.split('&');
  const params = {};
  pairs.forEach(pair => {
    const [key, value] = pair.split('=');
    const decodedKey = decodeURIComponent(key || '');
    const decodedValue = decodeURIComponent(value || '');
    if (params.hasOwnProperty(decodedKey)) {
      if (!Array.isArray(params[decodedKey])) {
        params[decodedKey] = [params[decodedKey]];
      }
      params[decodedKey].push(decodedValue);
    } else {
      params[decodedKey] = decodedValue;
    }
  });
  return params;
}
function checkConditionPeriodically(config) {
  const intervalId = setInterval(() => {
    if (config.trueFunc && config.trueFunc() && "function" == typeof config.back) {
      clearInterval(intervalId);
      config.back();
    }
  }, 0x1f4);
}
function createDownloadButton(buttonText, className) {
  const button = document.createElement('button');
  button.textContent = buttonText;
  button.className = "download-button " + className;
  button.style.cssText = "padding: 5px 10px; background-color: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; white-space: nowrap;";
  return button;
}
async function handleDownloadButtonClick(fileNum, videoId) {
  console.log("点击了\"下载" + fileNum + "\"按钮，视频ID: " + videoId);
  fileNumber = fileNum;
  await requestVideoDetail({
    'vid': videoId,
    'trigger': "download4item"
  });
}
function addDownloadButtonsToCards() {
  console.log("aaa");
  document.querySelectorAll(".search-result-card").forEach(card => {
    console.log("bbb");
    if (!card.querySelector(".videoImage")?.["textContent"]['includes']('图文')) {
      const parentId = card.parentElement.getAttribute('id');
      let videoId = '';
      if (parentId) {
        videoId = parentId.replaceAll("waterfall_item_", '');
      } else {
        const link = card.querySelector('a');
        if (link) {
          const urlParts = link.getAttribute("href").split('/');
          videoId = urlParts[urlParts.length - 0x1];
        }
      }
      const buttonContainer = document.createElement('div');
      buttonContainer.style.cssText = "position: absolute; right: 10px; top: 50%; transform: translateY(-50%); display: flex; flex-direction: column; gap: 5px; z-index: 10;";
      const downloadButton1 = createDownloadButton("下载1", "btn-download-1");
      downloadButton1.addEventListener("click", () => {
        let waterfallItem = downloadButton1.closest(".AMqhOzPC");
        if (waterfallItem) {
          console.log(waterfallItem.id);
          chrome.storage.local.get("baiying_project_info", async result => {
            console.log("获取的数据:", result);
            if (!result || !result.baiying_project_info || !result.baiying_project_info.product_id) {
              return void alert("请先下载图片！");
            }
            let productId = result.baiying_project_info.product_id;
            if (old_product_id != productId) {
              return void alert("商品id已经发生变化，请重新进入页面再下载！");
            }
            const effectiveUserId = user?.id || "anonymous";
            if (!excuteTime) {
              return void alert('执行批次不正确，请检查');
            }
            downloadButton1.disabled = true;
            downloadButton1.innerHTML = '<span>下载中...</span>';
            const idParts = waterfallItem.id.split('_');
            const itemVideoId = idParts[idParts.length - 0x1];
            const videoUrl = video_map[itemVideoId];
            if (videoUrl) {
              await downloadResource(videoUrl, effectiveUserId + '_' + excuteTime + '_' + productId + '_video_1.mp4');
            } else {
              console.log("使用handleDownloadButtonClick下载");
              await handleDownloadButtonClick(0x1, videoId);
            }
            setTimeout(() => {
              downloadButton1.disabled = false;
              downloadButton1.innerHTML = "<span>下载1</span>";
            }, 0x3e8);
          });
        } else {
          alert("数据异常");
        }
      });
      const downloadButton2 = createDownloadButton('下载2', "btn-download-2");
      downloadButton2.addEventListener("click", () => {
        let waterfallItem = downloadButton2.closest(".AMqhOzPC");
        if (waterfallItem) {
          console.log(waterfallItem.id);
          chrome.storage.local.get("baiying_project_info", async result => {
            console.log('获取的数据:', result);
            if (!result || !result.baiying_project_info || !result.baiying_project_info.product_id) {
              return void alert('请先下载图片！');
            }
            let productId = result.baiying_project_info.product_id;
            if (old_product_id != productId) {
              return void alert("商品id已经发生变化，请重新进入页面再下载！");
            }
            const effectiveUserId = user?.id || "anonymous";
            if (!excuteTime) {
              return void alert('执行批次不正确，请检查');
            }
            downloadButton2.disabled = true;
            downloadButton2.innerHTML = '<span>下载中...</span>';
            const idParts = waterfallItem.id.split('_');
            const itemVideoId = idParts[idParts.length - 0x1];
            const videoUrl = video_map[itemVideoId];
            if (videoUrl) {
              await downloadResource(videoUrl, effectiveUserId + '_' + excuteTime + '_' + productId + "_video_2.mp4");
            } else {
              console.log('使用handleDownloadButtonClick下载');
              await handleDownloadButtonClick(0x2, videoId);
            }
            setTimeout(() => {
              downloadButton2.disabled = false;
              downloadButton2.innerHTML = "<span>下载2</span>";
            }, 0x3e8);
          });
        } else {
          alert("数据异常");
        }
      });
      const downloadButton3 = createDownloadButton("下载3", "btn-download-3");
      downloadButton3.addEventListener("click", () => {
        let waterfallItem = downloadButton3.closest(".AMqhOzPC");
        if (waterfallItem) {
          console.log(waterfallItem.id);
          chrome.storage.local.get("baiying_project_info", async result => {
            console.log("获取的数据:", result);
            if (!result || !result.baiying_project_info || !result.baiying_project_info.product_id) {
              return void alert("请先下载图片！");
            }
            let productId = result.baiying_project_info.product_id;
            if (old_product_id != productId) {
              return void alert("商品id已经发生变化，请重新进入页面再下载！");
            }
            const effectiveUserId = user?.id || "anonymous";
            if (!excuteTime) {
              return void alert('执行批次不正确，请检查');
            }
            downloadButton3.disabled = true;
            downloadButton3.innerHTML = '<span>下载中...</span>';
            const idParts = waterfallItem.id.split('_');
            const itemVideoId = idParts[idParts.length - 0x1];
            const videoUrl = video_map[itemVideoId];
            if (videoUrl) {
              await downloadResource(videoUrl, effectiveUserId + '_' + excuteTime + '_' + productId + "_video_3.mp4");
            } else {
              console.log("使用handleDownloadButtonClick下载");
              await handleDownloadButtonClick(0x3, videoId);
            }
            setTimeout(() => {
              downloadButton3.disabled = false;
              downloadButton3.innerHTML = "<span>下载3</span>";
            }, 0x3e8);
          });
        } else {
          alert("数据异常");
        }
      });
      buttonContainer.appendChild(downloadButton1);
      buttonContainer.appendChild(downloadButton2);
      buttonContainer.appendChild(downloadButton3);
      card.style.position = "relative";
      card.appendChild(buttonContainer);
    }
  });
}
async function requestVideoDetail(params) {
  const detailParams = await getRequestParams("detailParams");
  console.log("请求视频详情参数=>");
  detailParams.aweme_id = params.vid;
  const queryString = buildQueryString(detailParams);
  window.postMessage({
    'action': "DBDY_ACCQURE2",
    'actionRes': "DBDY_ACCQURE2_RES",
    'url': "https://www.douyin.com/aweme/v1/web/aweme/detail/?" + queryString,
    'trigger': params.trigger,
    'options': {
      'credentials': "include"
    },
    'location': window.location.href
  }, '*');
}
function getVideoUrl() {
  const videoContainer = document.querySelector(".xg-video-container");
  if (videoContainer) {
    const video = videoContainer.querySelector("video");
    if (video) {
      const sources = video.querySelectorAll("source");
      if (sources.length > 0x0) {
        const lastSourceUrl = sources[sources.length - 0x1].src;
        console.log("最后一个source的src:", lastSourceUrl);
        return lastSourceUrl;
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
function getHighestQualityVideoUrl(awemeData) {
  try {
    const bitRates = awemeData?.["video"]?.["bit_rate"];
    if (bitRates) {
      const highestQualityAddr = bitRates.sort((a, b) => (b.play_addr?.['width'] || 0x0) - (a.play_addr?.["width"] || 0x0))[0x0].play_addr;
      if (highestQualityAddr && highestQualityAddr.url_list && highestQualityAddr.url_list.length > 0x0) {
        return highestQualityAddr.url_list.find(url => url.startsWith("https://www.douyin.com")) || highestQualityAddr.url_list[0x0];
      }
    }
  } catch (error) {
    console.log("提取高清视频地址失败:", error);
  }
  return null;
}
function buildQueryString(params) {
  const pairs = [];
  for (const key in params) pairs.push(key + '=' + params[key]);
  return pairs.join('&');
}
function formatDate(timestamp) {
  return new Date(timestamp).toISOString().split('T')[0x0];
}
function normalizeVideoData(awemeDetail) {
  const urlList = awemeDetail.video?.["play_addr"]?.["url_list"];
  let videoUrl = urlList ? urlList[0x0] : '';
  if (urlList && urlList.length > 0x2) {
    videoUrl = urlList[0x2];
  }
  return {
    'vid': awemeDetail.aweme_id,
    'date': new Date(0x3e8 * awemeDetail.create_time).toISOString().split('T')[0x0],
    'cover': awemeDetail.video?.["origin_cover"]?.["url_list"][0x0],
    'url': getHighestQualityVideoUrl(awemeDetail) || videoUrl,
    'authorName': awemeDetail.author?.['nickname'],
    'title': awemeDetail.desc,
    'duration': ((awemeDetail.duration || awemeDetail.video?.duration || 0x0) / 0x3e8) || 0x0,
    'digg': awemeDetail.statistics?.digg_count || 0x0
  };
}
window.addEventListener('load', async () => {
  await parseUrlParameters();
  setInterval(() => {
    addDownloadButtonsToCards();
  }, 0x7d0);
  function displayProjectInfoCard(projectInfo) {
    let cardContent;
    let toggleButton;
    let infoCard = document.getElementById("baiying-project-info-card");
    let isCollapsed = false;
    if (infoCard) {
      cardContent = infoCard.querySelector(".card-content");
      toggleButton = infoCard.querySelector(".toggle-button");
      isCollapsed = cardContent && "none" === cardContent.style.display;
    } else {
      infoCard = document.createElement('div');
      infoCard.id = "baiying-project-info-card";
      Object.assign(infoCard.style, {
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
      document.body.appendChild(infoCard);
    }
    infoCard.innerHTML = '';
    const headerContainer = document.createElement("div");
    headerContainer.style.display = 'flex';
    headerContainer.style.justifyContent = "space-between";
    headerContainer.style.alignItems = 'center';
    headerContainer.style.marginBottom = "6px";
    const title = document.createElement('h3');
    title.textContent = "当前商品信息";
    title.style.margin = '0';
    title.style.color = '#555';
    title.style.fontSize = "14px";
    headerContainer.appendChild(title);
    toggleButton = document.createElement("button");
    toggleButton.className = 'toggle-button';
    toggleButton.textContent = isCollapsed ? '▼' : '▲';
    Object.assign(toggleButton.style, {
      'background': 'none',
      'border': 'none',
      'fontSize': "12px",
      'color': "#888",
      'cursor': "pointer",
      'padding': "0 4px",
      'outline': 'none'
    });
    headerContainer.appendChild(toggleButton);
    infoCard.appendChild(headerContainer);
    cardContent = document.createElement('div');
    cardContent.className = 'card-content';
    if (isCollapsed) {
      cardContent.style.display = 'none';
    }
    if (projectInfo) {
      if (projectInfo.cover) {
        const coverContainer = document.createElement("div");
        coverContainer.style.marginBottom = '6px';
        const coverImage = document.createElement('img');
        coverImage.src = projectInfo.cover;
        coverImage.style.width = "100%";
        coverImage.style.borderRadius = "3px";
        coverImage.style.objectFit = "cover";
        coverContainer.appendChild(coverImage);
        cardContent.appendChild(coverContainer);
      }
      if (projectInfo.product_id) {
        const productIdDiv = document.createElement("div");
        productIdDiv.innerHTML = "ID: " + projectInfo.product_id;
        productIdDiv.style.marginBottom = "3px";
        productIdDiv.style.color = "#888";
        productIdDiv.style.fontSize = "12px";
        productIdDiv.style.fontWeight = "normal";
        cardContent.appendChild(productIdDiv);
      }
      if (projectInfo.product_name) {
        const productNameDiv = document.createElement("div");
        productNameDiv.innerHTML = "名称: " + projectInfo.product_name;
        productNameDiv.style.marginBottom = "3px";
        productNameDiv.style.color = "#1e8a3eff";
        productNameDiv.style.fontSize = "14px";
        productNameDiv.style.fontWeight = "700";
        productNameDiv.style.wordBreak = "break-word";
        cardContent.appendChild(productNameDiv);
      }
    } else {
      const noInfoDiv = document.createElement("div");
      noInfoDiv.textContent = "暂无商品信息";
      noInfoDiv.style.color = "#050404ff";
      noInfoDiv.style.fontSize = "12px";
      cardContent.appendChild(noInfoDiv);
    }
    infoCard.appendChild(cardContent);
    toggleButton.addEventListener("click", function () {
      const shouldExpand = 'none' === cardContent.style.display;
      cardContent.style.display = shouldExpand ? 'block' : 'none';
      toggleButton.textContent = shouldExpand ? '▲' : '▼';
    });
  }
  chrome.storage.local.get("baiying_project_info", async result => {
    console.log("baiying_project_info res", result.baiying_project_info);
    if (result.baiying_project_info && result.baiying_project_info.product_id) {
      old_product_id = result.baiying_project_info.product_id;
    }
    displayProjectInfoCard(result.baiying_project_info);
    chrome.storage.onChanged.addListener((changes, areaName) => {
      if ("local" === areaName && changes.baiying_project_info) {
        console.log("商品信息已更新:", changes.baiying_project_info.newValue);
        displayProjectInfoCard(changes.baiying_project_info.newValue);
      }
    });
  });
  loadUserData();
  waitForElement("xg-right-grid.xg-right-grid", rightGrid => {
    const videoDownloadButton1 = document.createElement("button");
    videoDownloadButton1.textContent = "下载1";
    videoDownloadButton1.className = "custom-download-button";
    videoDownloadButton1.style.margin = "5px";
    videoDownloadButton1.style.padding = "8px 12px";
    videoDownloadButton1.style.backgroundColor = '#4CAF50';
    videoDownloadButton1.style.color = 'white';
    videoDownloadButton1.style.border = 'none';
    videoDownloadButton1.style.borderRadius = '4px';
    videoDownloadButton1.style.cursor = "pointer";
    videoDownloadButton1.style.zIndex = '1000';
    const videoDownloadButton2 = document.createElement("button");
    videoDownloadButton2.textContent = "下载2";
    videoDownloadButton2.className = "custom-download-button";
    videoDownloadButton2.style.margin = "5px";
    videoDownloadButton2.style.padding = "8px 12px";
    videoDownloadButton2.style.backgroundColor = '#4CAF50';
    videoDownloadButton2.style.color = 'white';
    videoDownloadButton2.style.border = "none";
    videoDownloadButton2.style.borderRadius = '4px';
    videoDownloadButton2.style.cursor = "pointer";
    videoDownloadButton2.style.zIndex = '1000';
    const videoDownloadButton3 = document.createElement("button");
    videoDownloadButton3.textContent = "下载3";
    videoDownloadButton3.className = 'custom-download-button';
    videoDownloadButton3.style.margin = '5px';
    videoDownloadButton3.style.padding = "8px 12px";
    videoDownloadButton3.style.backgroundColor = "#4CAF50";
    videoDownloadButton3.style.color = 'white';
    videoDownloadButton3.style.border = 'none';
    videoDownloadButton3.style.borderRadius = '4px';
    videoDownloadButton3.style.cursor = "pointer";
    videoDownloadButton3.style.zIndex = '1000';
    rightGrid.prepend(videoDownloadButton3);
    rightGrid.prepend(videoDownloadButton2);
    rightGrid.prepend(videoDownloadButton1);
    videoDownloadButton1.addEventListener("click", async () => {
      chrome.storage.local.get("baiying_project_info", async result => {
        console.log("获取的数据:", result);
        if (!result || !result.baiying_project_info || !result.baiying_project_info.product_id) {
          return void alert("请先下载图片！");
        }
        let productId = result.baiying_project_info.product_id;
        if (old_product_id == productId) {
          const effectiveUserId = user?.id || "anonymous";
          if (excuteTime) {
            videoDownloadButton1.disabled = true;
            videoDownloadButton1.innerHTML = '<span>下载中...</span>';
            if (video_url) {
              await downloadResource(video_url, effectiveUserId + '_' + excuteTime + '_' + productId + "_video_1.mp4");
            } else {
              console.log("使用handleDownloadButtonClick下载");
              const currentVideoId = window.location.href.split('/').pop();
              await handleDownloadButtonClick(0x1, currentVideoId);
            }
            setTimeout(() => {
              videoDownloadButton1.disabled = false;
              videoDownloadButton1.innerHTML = "<span>下载1</span>";
            }, 0x3e8);
          } else {
            alert("执行批次不正确，请检查");
          }
        } else {
          alert("商品id已经发生变化，请重新进入页面再下载！");
        }
      });
    });
    videoDownloadButton2.addEventListener("click", async () => {
      chrome.storage.local.get('baiying_project_info', async result => {
        console.log("获取的数据:", result);
        if (!result || !result.baiying_project_info || !result.baiying_project_info.product_id) {
          return void alert("请先下载图片！");
        }
        let productId = result.baiying_project_info.product_id;
        if (old_product_id == productId) {
          const effectiveUserId = user?.id || "anonymous";
          if (excuteTime) {
            videoDownloadButton2.disabled = true;
            videoDownloadButton2.innerHTML = '<span>下载中...</span>';
            if (video_url) {
              await downloadResource(video_url, effectiveUserId + '_' + excuteTime + '_' + productId + "_video_2.mp4");
            } else {
              console.log("使用handleDownloadButtonClick下载");
              const currentVideoId = window.location.href.split('/').pop();
              await handleDownloadButtonClick(0x2, currentVideoId);
            }
            setTimeout(() => {
              videoDownloadButton2.disabled = false;
              videoDownloadButton2.innerHTML = "<span>下载2</span>";
            }, 0x3e8);
          } else {
            alert("执行批次不正确，请检查");
          }
        } else {
          alert('商品id已经发生变化，请重新进入页面再下载！');
        }
      });
    });
    videoDownloadButton3.addEventListener("click", async () => {
      chrome.storage.local.get("baiying_project_info", async result => {
        console.log("获取的数据:", result);
        if (!result || !result.baiying_project_info || !result.baiying_project_info.product_id) {
          return void alert("请先下载图片！");
        }
        let productId = result.baiying_project_info.product_id;
        if (old_product_id == productId) {
          const effectiveUserId = user?.id || "anonymous";
          if (excuteTime) {
            videoDownloadButton3.disabled = true;
            videoDownloadButton3.innerHTML = "<span>下载中...</span>";
            if (video_url) {
              await downloadResource(video_url, effectiveUserId + '_' + excuteTime + '_' + productId + '_video_3.mp4');
            } else {
              console.log("使用handleDownloadButtonClick下载");
              const currentVideoId = window.location.href.split('/').pop();
              await handleDownloadButtonClick(0x3, currentVideoId);
            }
            setTimeout(() => {
              videoDownloadButton3.disabled = false;
              videoDownloadButton3.innerHTML = "<span>下载3</span>";
            }, 0x3e8);
          } else {
            alert("执行批次不正确，请检查");
          }
        } else {
          alert('商品id已经发生变化，请重新进入页面再下载！');
        }
      });
    });
  });
});
const FileHandler = {
  'cleanFileName': function (filename) {
    if (!filename) {
      filename = "抖音视频";
    }
    return (filename = (filename = filename.replace(/[\\/？?*.,"''|<>{}[\]【】：:、^$!~`]/g, '')).replace(/展开/g, '') || '未知名称').replace(/[<>:"/\\|?*\s]/g, '_');
  },
  'truncateTo50Chars': function (str) {
    return str && str.length > 0x32 ? str.substring(0x0, 0x32) : str;
  },
  'convertJpgToPng': function (imageUrl) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.setAttribute('crossOrigin', "anonymous");
      image.src = imageUrl;
      image.onload = function () {
        const canvas = document.createElement("canvas");
        canvas.width = image.width;
        canvas.height = image.height;
        canvas.getContext('2d').drawImage(image, 0x0, 0x0);
        resolve(canvas.toDataURL("image/png"));
      };
      image.onerror = reject;
    });
  },
  'saveAsZip': async function (fileName, config, videoData) {
    if (!videoData) {
      return;
    }
    const zip = new t();
    let completedCount = 0x0;
    let totalCount = 0x0;
    if ('single' === config.type) {
      if (videoData.url?.['startsWith']("http:")) {
        videoData.url = videoData.url.replaceAll("http:", 'https:');
      }
      fetch(videoData.url).then(response => response.blob()).then(blob => {
        const link = document.createElement('a');
        document.body.appendChild(link);
        link.style.display = 'none';
        const blobUrl = window.URL.createObjectURL(blob);
        link.href = blobUrl;
        link.download = this.truncateTo50Chars(this.cleanFileName(fileName)) + ".mp4";
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
        if (config.callback) {
          config.callback(config.id);
        }
      });
    } else {
      if ('batchs' === config.type) {
        const videoList = Array.isArray(videoData) ? videoData : [videoData];
        const usedFileNames = [];
        const queue = new el(0x14);
        totalCount = videoList.length;
        videoList.forEach(videoItem => {
          let videoFileName = this.getFileName(videoItem, config.fileNameFormat);
          if (usedFileNames.includes(videoFileName)) {
            videoFileName = videoFileName + '_' + videoItem.vid + ".mp4";
          } else {
            usedFileNames.push(videoFileName);
            videoFileName = videoFileName + ".mp4";
          }
          completedCount++;
          const taskConfig = {
            'progress': progressData => {
              if (config.progress) {
                config.progress(videoItem.vid, Math.round(progressData.percent));
              }
            },
            'callback': (error, binaryData) => {
              if (error) {
                console.log("获取二进制数据错误", error);
              } else {
                zip.file(videoFileName, binaryData, {
                  'binary': true
                });
              }
              if (error && config.callback) {
                config.callback(config.id);
              }
              completedCount++;
              if (completedCount === totalCount) {
                if (config.progress) {
                  config.progress("all_done", 0x64);
                }
                (() => {
                  let zipFileName = fileName + '_' + config.type;
                  if (config.name) {
                    zipFileName = fileName + '_' + config.name;
                  }
                  const writer = a().createWriteStream(zipFileName + ".zip").getWriter();
                  zip.generateInternalStream({
                    'type': "blob",
                    'compression': 'DEFLATE',
                    'compressionOptions': {
                      'level': 0x9
                    }
                  }).on("data", (data, metadata) => {
                    if (config.compressProgress) {
                      config.compressProgress(Math.round(metadata.percent));
                    }
                    writer.write(data);
                  }).on('error', error => console.error(error)).on("end", () => {
                    if (config.compressProgress) {
                      config.compressProgress(-0x64);
                    }
                    writer.close();
                  }).resume();
                })();
              }
            }
          };
          queue.enqueue(new Qo(videoItem, taskConfig)).then(() => {})["catch"](error => {
            console.log('获取异常，重试：', videoItem.url, error);
            taskConfig.flag = true;
            queue.enqueue(new Qo(videoItem, taskConfig));
          });
        });
      }
    }
  },
  async 'save2Directory'(directoryHandle, config, videoList) {
    try {
      let completedCount = 0x0;
      let totalCount = videoList.length;
      const usedFileNames = [];
      const queue = new el(0x14);
      videoList.forEach(videoItem => {
        totalCount++;
        let videoFileName = this.getFileName(videoItem, config.fileNameFormat);
        if (usedFileNames.includes(videoFileName)) {
          videoFileName = videoFileName + '_' + videoItem.vid + ".mp4";
        } else {
          usedFileNames.push(videoFileName);
          videoFileName = videoFileName + ".mp4";
        }
        const taskConfig = {
          'progress': progressData => {
            if (config.progress) {
              config.progress(videoItem.vid, Math.round(progressData.percent));
            }
          },
          'callback': async (error, binaryData) => {
            if (error) {
              console.log("获取二进制数据错误", error);
            } else {
              const fileHandle = await directoryHandle.getFileHandle(videoFileName, {
                'create': true
              });
              const writable = await fileHandle.createWritable();
              await writable.write(binaryData);
              await writable.close();
            }
            if (error && config.callback) {
              config.callback(config.id);
            }
            completedCount++;
            if (completedCount === totalCount && config.progress) {
              config.progress("all_done", 0x64);
            }
          }
        };
        queue.enqueue(new Qo(videoItem, taskConfig)).then(() => {})['catch'](error => {
          console.log('获取异常，重试：', videoItem.url, error);
          taskConfig.flag = true;
          queue.enqueue(new Qo(videoItem, taskConfig));
        });
      });
    } catch (error) {
      console.error('保存文件时出错:', error);
    }
  },
  async 'getDirectoryHandle'() {
    try {
      const directoryHandle = await window.showDirectoryPicker();
      return 'granted' !== (await directoryHandle.queryPermission({
        'mode': 'readwrite'
      })) && (console.log('用户未授予读写权限'), "granted" !== (await directoryHandle.requestPermission({
        'mode': "readwrite"
      }))) ? console.log("用户拒绝授予读写权限") : directoryHandle;
    } catch (error) {
      console.error("获取文件夹句柄失败:", error);
      throw error;
    }
  },
  'getFileName': function (videoData, format) {
    let fileName = videoData.title || videoData.desc ? this.truncateTo50Chars(this.cleanFileName(videoData.title || videoData.desc)) : videoData.vid;
    if (format) {
      switch (format) {
        case "date_title":
          fileName = videoData.date ? videoData.date.replaceAll('-', '') + '_' + fileName : fileName;
          break;
        case "date_title_productId":
          fileName = (videoData.date ? videoData.date.replaceAll('-', '') + '_' + fileName : fileName) + '_' + (videoData.goods?.["productId"] ? videoData.goods.productId : '');
          break;
        case 'vid_productId':
          fileName = videoData.vid + '_' + (videoData.goods?.["productId"] ? videoData.goods.productId : '');
          break;
        case "date_vid":
          fileName = (videoData.date ? videoData.date.replaceAll('-', '') : '') + '_' + videoData.vid;
          break;
        case "title_productId":
          fileName = fileName + '_' + (videoData.goods?.["productId"] ? videoData.goods.productId : '');
      }
    } else {
      fileName = videoData.date ? videoData.date.replaceAll('-', '') + '_' + fileName : fileName;
    }
    return fileName;
  },
  'downloadStream': async function (url, callbacks) {
    try {
      const response = await fetch(url);
      const contentLengthHeader = response.headers.get("content-length");
      const totalSize = parseInt(contentLengthHeader, 0xa);
      let loadedSize = 0x0;
      const chunks = [];
      const reader = response?.["body"]?.['getReader']();
      for (;;) {
        const {
          done: isDone,
          value: chunk
        } = await reader.read();
        if (isDone) {
          break;
        }
        loadedSize += chunk.byteLength;
        callbacks.progress({
          'percent': 0x64 * loadedSize / totalSize
        });
        chunks.push(chunk);
      }
      callbacks.callback(null, new Blob(chunks));
    } catch (error) {
      if (!callbacks.flag) {
        console.log("downloadStream:", error);
        throw error;
      }
      callbacks.callback(error, null);
    }
  },
  'handleExportField': function (exportFormat, fields, videoData) {
    let textRow = '';
    const jsonRow = {};
    for (const field of fields) switch (field) {
      case "nickName":
        if ('json' === exportFormat) {
          jsonRow.用户昵称 = videoData.author.nickName;
        } else {
          textRow += videoData ? videoData.author.nickName + "\t" : '用户昵称,';
        }
        break;
      case 'secUid':
        if ("json" === exportFormat) {
          jsonRow.用户链接 = "https://www.douyin.com/user/" + videoData.author.secUid;
        } else {
          textRow += videoData ? "https://www.douyin.com/user/" + videoData.author.secUid + "\t" : "用户链接,";
        }
        break;
      case "videoDetail":
        if ("json" === exportFormat) {
          jsonRow.视频详情 = "https://www.douyin.com/video/" + videoData.vid;
        } else {
          textRow += videoData ? "https://www.douyin.com/video/" + videoData.vid + "\t" : "视频详情,";
        }
        break;
      case "desc":
        if ("json" === exportFormat) {
          jsonRow.视频描述 = videoData.desc;
        } else {
          textRow += videoData ? videoData.desc + "\t" : "视频描述,";
        }
        break;
      case "digg":
        if ("json" === exportFormat) {
          jsonRow.点赞 = videoData.statistics.digg;
        } else {
          textRow += videoData ? videoData.statistics.digg + "\t" : '点赞,';
        }
        break;
      case 'collect':
        if ("json" === exportFormat) {
          jsonRow.收藏 = videoData.statistics.collect;
        } else {
          textRow += videoData ? videoData.statistics.collect + "\t" : "收藏,";
        }
        break;
      case "comment":
        if ("json" === exportFormat) {
          jsonRow.评论 = videoData.statistics.comment;
        } else {
          textRow += videoData ? videoData.statistics.comment + "\t" : '评论,';
        }
        break;
      case 'share':
        if ("json" === exportFormat) {
          jsonRow.分享 = videoData.statistics.share;
        } else {
          textRow += videoData ? videoData.statistics.share + "\t" : "分享,";
        }
        break;
      case "productId":
        if ("json" === exportFormat) {
          jsonRow.商品ID = videoData.goods?.["productId"] ? videoData.goods.productId : '';
        } else {
          textRow += videoData ? (videoData.goods?.["productId"] ? videoData.goods.productId : '') + "\t" : "商品ID,";
        }
        break;
      case "title":
        if ("json" === exportFormat) {
          jsonRow.商品标题 = videoData.goods?.['title'] ? videoData.goods.title : '';
        } else {
          textRow += videoData ? (videoData.goods?.["title"] ? videoData.goods.title : '') + "\t" : "商品标题,";
        }
        break;
      case "price":
        if ("json" === exportFormat) {
          jsonRow.商品价格 = videoData.goods?.["price"] ? videoData.goods.price : '';
        } else {
          textRow += videoData ? (videoData.goods?.['price'] ? videoData.goods.price : '') + "\t" : "商品价格,";
        }
        break;
      case "url":
        if ("json" === exportFormat) {
          jsonRow.商品URL = videoData.goods?.['url'] ? videoData.goods.url : '';
        } else {
          textRow += videoData ? (videoData.goods?.["url"] ? videoData.goods.url : '') + "\t" : "商品URL,";
        }
        break;
      case 'sales':
        if ('json' === exportFormat) {
          jsonRow.商品销量 = videoData.goods?.["sales"] ? videoData.goods.sales : '';
        } else {
          textRow += videoData ? (videoData.goods?.["sales"] ? videoData.goods.sales : '') + "\t" : "商品销量,";
        }
    }
    return "json" === exportFormat ? jsonRow : textRow + "\n";
  },
  'copyCSV': function (config, videoList) {
    let csvContent = '';
    videoList.forEach(videoItem => {
      csvContent += this.handleExportField("text", config.fields, videoItem);
    });
    return csvContent;
  },
  'downloadXlsx': function (config, videoList) {
    const workbook = Zo.book_new();
    const jsonData = videoList.map(videoItem => this.handleExportField("json", config.fields, videoItem));
    const worksheet = Zo.json_to_sheet(jsonData);
    let sheetName = this.cleanFileName(config.name);
    if (sheetName.length > 0x1e) {
      sheetName = sheetName.substring(0x0, 0x1e);
    }
    Zo.book_append_sheet(workbook, worksheet, sheetName);
    const xlsxData = Bo(workbook, {
      'bookType': "xlsx",
      'type': "array"
    });
    const blob = new Blob([xlsxData], {
      'type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8'
    });
    if (config.callback) {
      config.callback(config.id);
    }
    this.downloadFile(blob, config.filename + ".xlsx");
  },
  'downloadUserXlsx': function (config, videoList) {
    const workbook = Zo.book_new();
    let userName = null;
    const jsonData = videoList.map(videoItem => (userName || (userName = videoItem.name), {
      '视频ID': '' + videoItem.vid,
      '视频封面': '' + videoItem.cover,
      '视频描述': '' + (videoItem.title || ''),
      '视频详情': 'https://www.douyin.com/video/' + videoItem.awemeId,
      '视频下载URL': '' + videoItem.url,
      '是否置顶': '' + (videoItem.isTop || ''),
      '发布日期': '' + videoItem.date,
      '合集ID': '' + (videoItem.mixId && "undefined" != videoItem.mixId ? videoItem.mixId : ''),
      '合集名称': '' + (videoItem.mixName || ''),
      '时长/秒': '' + (videoItem.duration ? Math.round(videoItem.duration / 0x3e8) : ''),
      '点赞量': '' + (videoItem.stats.digg_count || 0x0),
      '收藏量': '' + (videoItem.stats.collect_count || 0x0),
      '评论量': '' + (videoItem.stats.comment_count || 0x0),
      '转发量': '' + (videoItem.stats.share_count || 0x0)
    }));
    const worksheet = Zo.json_to_sheet(jsonData);
    let sheetName = this.cleanFileName(config.name || userName);
    if (sheetName.length > 0x1e) {
      sheetName = sheetName.substring(0x0, 0x1e);
    }
    Zo.book_append_sheet(workbook, worksheet, sheetName);
    const xlsxData = Bo(workbook, {
      'bookType': "xlsx",
      'type': 'array'
    });
    const blob = new Blob([xlsxData], {
      'type': "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8"
    });
    if (config.callback) {
      config.callback(config.id);
    }
    this.downloadFile(blob, config.filename + '_' + userName + '.xlsx');
  },
  'downloadFile': function (blob, filename) {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }
};
async function downloadVideo(videoData, progressCallback, completeCallback) {
  ensureAutoProjectContext(async projectInfo => {
    const productId = projectInfo.product_id;
    if (!productId) {
      if (completeCallback) {
        completeCallback(new Error("缺少商品ID"));
      }
      return;
    }
    old_product_id = productId;
    if (!excuteTime) {
      excuteTime = getMidnightTimestamp();
    }
    if (videoData.url?.["startsWith"]("http:")) {
      videoData.url = videoData.url.replaceAll("http:", "https:");
    }
    const keywordForPath = sanitizeForPath(lastSearchKeyword || productId || "videos");
    const relativePath = "auto_videos/" + keywordForPath + "/" + (user?.['id'] || 'anonymous') + '_' + (excuteTime || '') + '_' + productId + "_video_" + fileNumber + ".mp4";
    chrome.runtime.sendMessage({
      'action': 'downloadVideoFile',
      'url': videoData.url,
      'filename': relativePath
    }, response => {
      if (chrome.runtime.lastError) {
        console.error("downloadVideoFile error:", chrome.runtime.lastError.message);
        if (completeCallback) {
          completeCallback(new Error(chrome.runtime.lastError.message));
        }
        return;
      }
      if (!response || !response.success) {
        console.error("下载失败:", response?.error);
        if (completeCallback) {
          completeCallback(new Error(response?.error || '下载失败'));
        }
        return;
      }
      if (completeCallback) {
        completeCallback(null, {
          'filePath': response.filePath,
          'relativePath': relativePath
        });
      }
    });
  });
}
async function downloadResource(url, filename, subPath = '') {
  const fullFilename = subPath ? subPath + '/' + filename : filename;
  try {
    if (!url || !url.startsWith("http")) {
      alert("无效的URL: " + url);
      throw new Error("无效的URL: " + url);
    }
    console.log("开始下载: " + fullFilename);
    const response = await fetch(url, {
      'method': "GET",
      'mode': "cors",
      'credentials': "same-origin"
    });
    if (!response.ok) {
      throw new Error("HTTP错误: " + response.status + " " + response.statusText);
    }
    const contentType = response.headers.get("Content-Type");
    const contentLength = response.headers.get('Content-Length');
    console.log("info", "响应信息：类型=" + contentType + '，预计大小=' + (contentLength ? (contentLength / 0x400 / 0x400).toFixed(0x2) + 'MB' : '未知'));
    if (!contentType?.["startsWith"]("video/")) {
      throw new Error("非视频类型: " + contentType);
    }
    const reader = response.body.getReader();
    const chunks = [];
    let loadedBytes = 0x0;
    for (console.log("info", "开始分块读取数据...");;) {
      const {
        done: isDone,
        value: chunk
      } = await reader.read();
      if (isDone) {
        break;
      }
      chunks.push(chunk);
      loadedBytes += chunk.byteLength;
      if (contentLength) {
        const progress = loadedBytes / contentLength * 0x64;
        if (progress % 0xa < 0.1 || loadedBytes % 0x500000 < 0x400) {
          console.log("info", "下载进度: " + progress.toFixed(0x1) + "% (" + (loadedBytes / 0x400 / 0x400).toFixed(0x2) + "MB/" + (contentLength / 0x400 / 0x400).toFixed(0x2) + "MB)");
        }
      } else {
        console.log("info", "已读取: " + (loadedBytes / 0x400 / 0x400).toFixed(0x2) + 'MB');
      }
    }
    if (contentLength && loadedBytes !== parseInt(contentLength)) {
      throw new Error("数据不完整：实际读取" + loadedBytes + '字节，预期' + contentLength + '字节');
    }
    console.log("info", "分块读取完成，共" + chunks.length + '块，开始合并为Blob');
    const blob = new Blob(chunks, {
      'type': contentType
    });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fullFilename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    }, 0x3e8);
    return {
      'success': true,
      'filename': fullFilename
    };
  } catch (error) {
    console.error("下载 " + fullFilename + " 失败:", error);
    return {
      'success': false,
      'filename': fullFilename,
      'error': error.message
    };
  }
}
function getCurrentSearchKeyword() {
  try {
    const pathMatch = window.location.pathname.match(/\/search\/([^/?#]+)/);
    if (pathMatch && pathMatch[0x1]) {
      return decodeURIComponent(pathMatch[0x1]);
    }
    const params = new URLSearchParams(window.location.search);
    return params.get('keyword') || params.get('search_key') || '';
  } catch (error) {
    console.warn("解析搜索关键词失败:", error);
    return '';
  }
}
function resetAutoDownloadState() {
  autoDownloadQueue = [];
  autoDownloading = false;
  currentAutoDownload = null;
  autoDownloadedSet.clear();
  autoDownloadInitialized = false;
  autoDownloadFileIndex = 1;
  autoDownloadResults = [];
  concatInProgress = false;
}
function prepareAutoDownloadForKeyword(keyword) {
  const normalized = (keyword || '').trim();
  if (lastSearchKeyword !== normalized) {
    resetAutoDownloadState();
    lastSearchKeyword = normalized;
  }
}
function sanitizeForPath(text) {
  return (text || '').toString().replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, '_').toLowerCase() || 'job';
}
function joinWindowsPath(base, name) {
  if (!base) {
    return name || '';
  }
  return base.replace(/[\\/]+$/, '') + '\\' + (name || '');
}
function ensureAutoProjectContext(callback) {
  chrome.storage.local.get("baiying_project_info", result => {
    if (result?.baiying_project_info?.product_id) {
      old_product_id = result.baiying_project_info.product_id;
      callback(result.baiying_project_info);
      return;
    }
    const fallbackInfo = {
      'product_id': 'auto_' + Date.now(),
      'product_name': '自动下载',
      'cover': ''
    };
    chrome.storage.local.set({
      'baiying_project_info': fallbackInfo
    }, () => {
      old_product_id = fallbackInfo.product_id;
      callback(fallbackInfo);
    });
  });
}

function selectAutoDownloadCandidates(awemeInfos) {
  if (!Array.isArray(awemeInfos)) {
    return [];
  }
  const candidates = awemeInfos.map(info => ({
    'awemeId': info?.aweme_id,
    'durationSec': (info?.video?.duration || 0x0) / 0x3e8,
    'digg': info?.statistics?.digg_count || 0x0
  })).filter(item => item.awemeId && item.durationSec >= AUTO_DOWNLOAD_CONFIG.minDuration && item.durationSec <= AUTO_DOWNLOAD_CONFIG.maxDuration);
  candidates.sort((a, b) => b.digg - a.digg);
  return candidates.slice(0x0, AUTO_DOWNLOAD_CONFIG.limit);
}

function enqueueAutoDownloads(awemeInfos) {
  prepareAutoDownloadForKeyword(getCurrentSearchKeyword());
  if (autoDownloadInitialized) {
    return;
  }
  const selectedCandidates = selectAutoDownloadCandidates(awemeInfos);
  if (0x0 === selectedCandidates.length) {
    return;
  }
  ensureAutoProjectContext(() => {
    let addedCount = 0x0;
    selectedCandidates.forEach(candidate => {
      const alreadyQueued = autoDownloadQueue.some(task => task.awemeId === candidate.awemeId);
      if (autoDownloadedSet.has(candidate.awemeId) || alreadyQueued) {
        return;
      }
      autoDownloadQueue.push({
        'awemeId': candidate.awemeId,
        'fileIndex': autoDownloadFileIndex++,
        'durationSec': candidate.durationSec,
        'digg': candidate.digg
      });
      addedCount++;
    });
    if (addedCount > 0x0) {
      autoDownloadInitialized = true;
      processAutoDownloadQueue();
    }
  });
}

function processAutoDownloadQueue() {
  if (autoDownloading) {
    return;
  }
  const nextTask = autoDownloadQueue.shift();
  if (!nextTask) {
    return;
  }
  autoDownloading = true;
  currentAutoDownload = nextTask;
  fileNumber = nextTask.fileIndex;
  requestVideoDetail({
    'vid': nextTask.awemeId,
    'trigger': 'auto_download'
  });
}

function finalizeAutoDownload() {
  if (currentAutoDownload?.awemeId) {
    autoDownloadedSet.add(currentAutoDownload.awemeId);
  }
  currentAutoDownload = null;
  autoDownloading = false;
  if (autoDownloadQueue.length > 0x0) {
    processAutoDownloadQueue();
  } else {
    maybeTriggerConcatJob();
  }
}

function initiateDownload(trigger, videoData) {
  downloadVideo(videoData, progress => {}, (error, fileInfo) => {
    if (error) {
      console.log("下载失败:", error);
    } else {
      console.log("下载完成");
    }
    if ('auto_download' === trigger) {
      const autoMeta = currentAutoDownload;
      if (!error && fileInfo?.filePath) {
        autoDownloadResults.push({
          'path': fileInfo.filePath,
          'duration': autoMeta?.durationSec || videoData.duration || 0x0,
          'digg': autoMeta?.digg || videoData.digg || 0x0
        });
      }
      finalizeAutoDownload();
    }
  });
}
function maybeTriggerConcatJob() {
  if (concatInProgress) {
    return;
  }
  if (autoDownloadQueue.length > 0x0 || autoDownloading) {
    return;
  }
  if (autoDownloadResults.length === 0x0) {
    return;
  }
  concatInProgress = true;
  chrome.storage.local.get('auto_concat_config', result => {
    const config = result?.auto_concat_config || {};
    if (!config.draftsRoot || !config.outputDir) {
      concatInProgress = false;
      alert('未配置剪辑服务参数，请在扩展弹窗中填写草稿根目录与输出目录。');
      return;
    }
    const keywordBase = sanitizeForPath(lastSearchKeyword || currentAutoDownload?.awemeId || "job");
    const jobId = (config.jobId && config.jobId.trim()) || (keywordBase + "_" + Date.now());
    const payload = {
      'job_id': jobId,
      'drafts_root': config.draftsRoot,
      'output_path': joinWindowsPath(config.outputDir, jobId + ".mp4"),
      'canvas': {
        'width': parseInt(config.canvasWidth, 10) || 1080,
        'height': parseInt(config.canvasHeight, 10) || 1920
      },
      'fps': parseInt(config.fps, 10) || 30,
      'videos': autoDownloadResults.map(item => item.path),
      'options': {},
      'keyword': lastSearchKeyword || ''
    };
    const maxEach = parseInt(config.maxEachSeconds, 10);
    if (!Number.isNaN(maxEach) && maxEach > 0x0) {
      payload.options.max_each_video_seconds = maxEach;
    }
    chrome.runtime.sendMessage({
      'action': 'concatVideos',
      'payload': payload
    }, response => {
      concatInProgress = false;
      if (chrome.runtime.lastError) {
        alert("调用剪辑服务失败：" + chrome.runtime.lastError.message);
        return;
      }
      if (response?.success && response?.data?.ok) {
        alert("素材已提交自动剪辑，Job ID: " + jobId);
        autoDownloadResults = [];
      } else {
        alert("自动剪辑失败：" + (response?.data?.error || response?.error || '未知错误'));
        autoDownloadResults = [];
      }
    });
  });
}
function extractAsMap(jsonString) {
  const dataMatch = jsonString.replace(/\\/g, '').replace(/\s+/g, " ").replace(/[\x00-\x1F\x7F]/g, '').replace(/"{2,}/g, "\"").match(/"data"\s*:\s*\[\s*({[^}]*"aweme_info"\s*:{[^}]+})[,\s]*(.{0,1000})*/);
  if (!dataMatch) {
    return '{}';
  }
  const typeSegments = dataMatch[0x0].split(/"type"\s*:\s*1/).filter(segment => segment.includes("\"aweme_info\""));
  const videoMap = {};
  typeSegments.forEach(segment => {
    const fullSegment = "\"type\":1" + segment;
    const awemeId = extractSingleField(fullSegment, /"aweme_info"\s*:\s*\{"aweme_id"\s*:\s*"([^"]+)"/);
    const playAddrs = extractPlayAddrs(fullSegment);
    if (awemeId && playAddrs.length > 0x0) {
      videoMap[awemeId] = playAddrs[0x0];
    }
  });
  console.log("✅ 生成 Map 结构，共 " + Object.keys(videoMap).length + " 个有效条目");
  return videoMap;
}
function extractSingleField(text, pattern) {
  const match = text.match(pattern);
  return match && match[0x1] ? match[0x1].trim() : null;
}
function extractPlayAddrs(text) {
  const playAddrMatch = text.match(/"video"\s*:\s*\{"play_addr"\s*:\s*\{([^}]+)\}/) || text.match(/"play_addr"\s*:\s*\{([^}]+)\}/);
  if (!playAddrMatch || !playAddrMatch[0x1]) {
    return [];
  }
  const urlListMatch = playAddrMatch[0x1].match(/"url_list"\s*:\s*\[(["'].*?["'](?:,\s*["'].*?["'])*)\]/);
  if (!urlListMatch || !urlListMatch[0x1]) {
    return [];
  }
  const urls = [];
  urlListMatch[0x1].split(/,\s*/).forEach(urlWithQuotes => {
    const url = urlWithQuotes.replace(/["']/g, '').trim();
    if (url) {
      urls.push(url);
    }
  });
  return urls;
}
function processStringFinal(responseString) {
  try {
    return extractAsMap(responseString);
  } catch (error) {
    console.error("⚠️ 提取失败：" + error.message);
    return '{}';
  }
}
window.addEventListener("message", async event => {
  console.log("【智能选品】Listener message", event.data);
  const messageData = event.data;
  const action = messageData?.["action"];
  const trigger = messageData?.["trigger"];
  if ("DBDY_ACCQURE2_RES" === action) {
    if (trigger) {
      initiateDownload(trigger, normalizeVideoData(messageData.res.aweme_detail));
    }
  } else if ('DBDY_SEARCH_ACCQURE_RES' === action) {
    const awemeInfos = [];
    (messageData.res?.data || []).forEach(item => {
      if (item.aweme_info && item.aweme_info.aweme_id) {
        video_map[item.aweme_info.aweme_id] = item.aweme_info.video.play_addr.url_list[0x2];
        awemeInfos.push(item.aweme_info);
      } else {
        console.log("item", item);
      }
    });
    console.log("searchSingle res", video_map);
    enqueueAutoDownloads(awemeInfos);
  } else if ("DBDY_SEARCH_FIRST_ACCQURE_RES" === action) {
    const extractedMap = processStringFinal(messageData.res);
    for (const videoId in extractedMap) video_map[videoId] = extractedMap[videoId];
    console.log("searchSingle2 res", video_map);
  } else if ('DBDY_INFO_ACCQURE_RES' === action) {
    video_url = messageData.res.aweme_detail.video.play_addr.url_list[0x0];
    console.log("searchSingle3 res", video_url);
  }
}, false);
