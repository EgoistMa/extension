/* PROTOTYPE TEMPORARILY DISABLED: 当前原型阶段跳过百应图片流程，暂时整体注释以便后续恢复
let aalock = false;
let product_id = null;
function earlyInjectScript() {
  try {
    if ("loading" === document.readyState) {
      document.addEventListener('DOMContentLoaded', injectScriptToPage);
    } else {
      injectScriptToPage();
    }
  } catch (error) {
    console.error('【智能选品】初始化注入脚本失败:', error);
    setTimeout(earlyInjectScript, 0x64);
  }
}

function injectScriptToPage() {
  try {
    if (!document.head && !document.documentElement) {
      console.warn('【智能选品】DOM元素尚未准备好，稍后重试');
      return void setTimeout(injectScriptToPage, 0xa);
    }
    const script = document.createElement("script");
    script.src = chrome.runtime.getURL('assets/insert.js');
    (document.head || document.documentElement).appendChild(script);
    script.onload = function () {
      console.info('【智能选品】插入的脚本加载成功.');
      script.remove();
    };
    script.onerror = function () {
      console.error("【智能选品】插入的脚本加载失败.");
      setTimeout(injectScriptToPage, 0x3e8);
    };
  } catch (error) {
    console.error('【智能选品】注入脚本过程出错:', error);
  }
}
earlyInjectScript();
window.addEventListener('message', function (event) {
  try {
    if (event.data && event.data.action && 'onPackDetail' === event.data.action) {
      console.log("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", event.data);
      if (!product_id) {
        product_id = event.data.data.product_id;
        checkUpdateProjectElment();
      }
    }
  } catch (error) {
    console.error("【智能选品】处理页面脚本消息失败:", error);
  }
}, false);
chrome.runtime.onMessage.addListener(function (message) {
  if ("dataUpdated" === message.action) {
    window.location.reload();
  }
});
let user = null;
function loadUser(callback) {
  user = null;
  chrome.storage.local.get('xuanpin_user', function (result) {
    if (result.xuanpin_user) {
      try {
        user = JSON.parse(result.xuanpin_user);
        console.log("xuanpin_user======>", user);
      } catch (error) {
        console.warn("xuanpin_user 解析失败:", error);
        user = null;
      }
    }
    callback();
  });
}
function loadSharedData() {
  loadUser(init);
}
class DouyinWordDetector {
  constructor(apiUrl) {
    this.apiUrl = apiUrl;
  }
  async ["checkText"](text, productId) {
    try {
      const response = await fetch(this.apiUrl, {
        'method': "POST",
        'headers': {
          'Content-Type': 'application/json'
        },
        'body': JSON.stringify({
          'text': text,
          'product_id': productId
        })
      });
      if (!response.ok) {
        throw new Error("HTTP error! status: " + response.status);
      }
      return await response.json();
    } catch (error) {
      console.error("检测过程中发生错误:", error);
      return {
        'hasViolation': false,
        'error': error.message
      };
    }
  }
}
let productInfo = {
  'userId': '',
  'excuteTime': '',
  'noSelectSevenDay': false,
  'deleted': 0x0,
  'promotion_id': '',
  'product_id': '',
  'product_price': '',
  'cos_ratio': '',
  'cos_fee': '',
  'good_ratio': '',
  'sell_num': '',
  'author_num': '',
  'service_score': '',
  'goods_score': '',
  'logistics_score': '',
  'exper_score': '',
  'product_name': '',
  'by30': {
    'video_match_order_num': 0x0
  },
  'by7': '',
  'lvs': '',
  'sales': '',
  'detail_url': ''
};
function getProductName() {
  const titleElement = document.querySelector(".index_module__title____450e");
  return titleElement ? titleElement.textContent.trim() : '';
}
function getProductInfo() {
  productInfo = {};
  const effectiveUserId = user?.id || "anonymous";
  const promotionId = getUrlParam('id');
  productInfo.userId = effectiveUserId;
  productInfo.excuteTime = getMidnightTimestamp();
  productInfo.noSelectSevenDay = false;
  productInfo.deleted = 0x0;
  productInfo.promotion_id = promotionId;
  productInfo.product_id = product_id;
  console.log('bbbbbbbbbbbbb==>productInfo', productInfo);
  const dataContainer = document.querySelector(".index_module__dataCardContainer____0bd5");
  if (dataContainer) {
    dataContainer.querySelectorAll(".index_module__dataItem____0bd5").forEach(item => {
      let titleElement = item.querySelector('.index_module__dataTitle____0bd5');
      let title = null;
      let value = null;
      if (titleElement) {
        title = titleElement.textContent.trim();
        const contentElement = item.querySelector(".index_module__dataContent____0bd5");
        if (!contentElement) {
          return;
        }
        value = contentElement.textContent.trim();
      } else {
        const contentElement = item.querySelector(".index_module__dataContent____0bd5");
        if (!contentElement) {
          return;
        }
        titleElement = contentElement.querySelector('span:nth-of-type(1)');
        if (!titleElement) {
          return;
        }
        title = titleElement.textContent.trim();
        const valueElement = contentElement.querySelector("span:nth-of-type(2)");
        if (!valueElement) {
          return;
        }
        value = valueElement.textContent.trim();
      }
      switch (title) {
        case '到手价':
          const priceMatch = value.match(/¥\d+(\.\d+)?/);
          productInfo.product_price = priceMatch ? priceMatch[0x0] : '0';
          break;
        case "团长高佣":
        case '专属高佣':
        case '佣金':
          const ratioMatch = value.match(/\d+(\.\d+)?%/);
          const feeMatch = value.match(/赚\d+(\.\d+)?/);
          productInfo.cos_ratio = ratioMatch ? ratioMatch[0x0] : '0';
          productInfo.cos_fee = feeMatch ? feeMatch[0x0].replace('赚', '¥') : '0';
          break;
        case '好评率':
          productInfo.good_ratio = value || '0';
          break;
        case '已售':
          if (value && value.includes('万+')) {
            const numStr = value.replace('万+', '');
            productInfo.sell_num = (0x2710 * parseFloat(numStr)).toString();
          } else {
            productInfo.sell_num = value || '0';
          }
          break;
        case "带货人数":
          if (value && value.includes('万+')) {
            const numStr = value.replace('万+', '');
            productInfo.author_num = (0x2710 * parseFloat(numStr)).toString();
          } else {
            productInfo.author_num = value || '0';
          }
      }
    });
    if (!productInfo.product_price) {
      const priceElement = document.querySelector(".index_module__dataContent____0bd5 span:nth-child(2)");
      if (priceElement) {
        productInfo.product_price = priceElement.textContent.replace('¥', '');
        console.log('新元素中包含价格', productInfo.product_price);
      } else {
        console.log("未找到价格元素");
      }
    }
  } else {
    console.error('未找到数据容器，请检查HTML结构或类名是否正确');
  }
  const scoreContainer = document.querySelector(".index_module__scoreContainer____1d3f");
  if (scoreContainer) {
    const totalScoreElement = scoreContainer.querySelector('.index_module__totalScore____1d3f');
    if (totalScoreElement) {
      const bigNumElement = totalScoreElement.querySelector('.index_module__bigNum____1d3f');
      productInfo.service_score = bigNumElement ? bigNumElement.textContent.trim() + '分' : '0';
    } else {
      productInfo.service_score = '0';
    }
    const detailItems = scoreContainer.querySelectorAll(".index_module__detailItem____1d3f");
    if (detailItems.length > 0x0) {
      detailItems.forEach(detailItem => {
        const smallNumElement = detailItem.querySelector(".index_module__smallNum____1d3f");
        const scoreText = smallNumElement ? smallNumElement.textContent.trim() + '分' : "未获取到分数";
        const textLineElement = detailItem.querySelector(".index_module__textLine____1d3f");
        switch (textLineElement ? textLineElement.textContent.trim() : '') {
          case '商品':
            productInfo.goods_score = scoreText;
            break;
          case '物流':
            productInfo.logistics_score = scoreText;
            break;
          case '商家':
            productInfo.exper_score = scoreText;
        }
      });
    } else {
      productInfo.goods_score = '0';
      productInfo.logistics_score = '0';
      productInfo.exper_score = '0';
    }
  } else {
    console.error('未找到评分容器，请检查HTML结构或类名是否正确');
  }
  productInfo.product_name = getProductName();
  productInfo.detail_url = "https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?id=" + product_id + "&origin_type=pc_buyin_selection_decision";
  productInfo.cos_fee = parseFloat(productInfo.cos_fee?.["replace"](/[^\d.]/g, '') || '0');
  productInfo.cos_ratio = parseFloat(productInfo.cos_ratio?.["replace"](/[^\d.]/g, '') || '0');
  productInfo.exper_score = parseFloat(productInfo.exper_score?.["replace"](/[^\d.]/g, '') || '0');
  productInfo.good_ratio = parseFloat(productInfo.good_ratio?.["replace"](/[^\d.]/g, '') || '0');
  productInfo.goods_score = parseFloat(productInfo.goods_score?.["replace"](/[^\d.]/g, '') || '0');
  productInfo.logistics_score = parseFloat(productInfo.logistics_score?.["replace"](/[^\d.]/g, '') || '0');
  productInfo.service_score = parseFloat(productInfo.service_score?.["replace"](/[^\d.]/g, '') || '0');
  productInfo.product_price = parseFloat(productInfo.product_price?.["replace"](/[^\d.]/g, '') || '0');
  setTimeout(() => {
    const dataItemContainer = document.querySelector(".index_module__dataItemContainer____2d98");
    if (dataItemContainer) {
      dataItemContainer.querySelectorAll(".index_module__dataItem____45dd").forEach(dataItem => {
        const titleElement = dataItem.querySelector(".index_module__title____45dd");
        if (!titleElement) {
          return;
        }
        if ("出单达人数" === titleElement.textContent.trim()) {
          const contentItems = dataItem.querySelectorAll(".index_module__contentItem____45dd");
          if (!contentItems) {
            return;
          }
          contentItems.forEach(contentItem => {
            if ('视频' === contentItem.querySelector('.index_module__contentType____45dd').textContent.trim()) {
              const numElement = contentItem.querySelector(".index_module__num____45dd");
              if (numElement) {
                productInfo.by30.video_match_order_num = numElement.textContent.trim();
              }
            }
          });
        }
      });
      const dataCardContainers = document.querySelectorAll(".index_module__dataCardContainer____0bd5");
      const orderRate = (productInfo.by30.video_match_order_num / productInfo.author_num).toFixed(0x2);
      console.log('出单率=====》', productInfo.by30.video_match_order_num, productInfo.author_num);
      const orderRateHtml = "\n\t\t\t<div class=\"index_module__dataItem____0bd5\" elementtiming=\"element-timing\" style=\"max-width: 150px; flex: 1 0 auto;\">\n\t\t\t  <div class=\"index_module__dataTitle____0bd5\" elementtiming=\"element-timing\">出单率</div>\n\t\t\t  <div class=\"index_module__dataContent____0bd5\" elementtiming=\"element-timing\">\n\t\t\t    <div elementtiming=\"element-timing\">" + orderRate + "</div>\n\t\t\t    <div class=\"index_module__suffix____0bd5 index_module__gap____0bd5\" elementtiming=\"element-timing\" style=\"position: relative; top: 2px;\"></div>\n\t\t\t  </div>\n\t\t\t</div>\n\t\t\t";
      dataCardContainers.forEach(container => {
        container.insertAdjacentHTML("beforeend", orderRateHtml);
      });
    } else {
      console.error('未找到出单达人数据容器，请检查HTML类名是否正确');
    }
  }, 0x7d0);
}
function getUrlParam(paramName) {
  const params = window.location.search.slice(0x1).split('&');
  for (let param of params) {
    const [key, value] = param.split('=');
    if (decodeURIComponent(key) === paramName) {
      return decodeURIComponent(value || '');
    }
  }
  return null;
}
function createButton(text, clickHandler) {
  const button = document.createElement("button");
  button.textContent = text;
  button.className = "your-custom-button-class";
  button.addEventListener('click', clickHandler);
  return button;
}
async function bindTabsClick() {
  let tabElements = document.querySelectorAll(".auxo-tabs-tab");
  for (; !tabElements;) {
    await delay(0x3e8);
    tabElements = document.querySelectorAll(".auxo-tabs-tab");
    console.log("等待tab出现");
  }
  tabElements.forEach(tabElement => {
    tabElement.addEventListener("click", async () => {
      const tabText = tabElement.querySelector(".auxo-tabs-tab-btn").textContent.trim();
      console.log("点击了选项卡：" + tabText);
      if ("带货内容" == tabText) {
        if (aalock) {
          return;
        }
        aalock = true;
        await insertStringToCardWrappers();
        await insertAiAudioBtn();
        let pageItems = document.querySelectorAll(".auxo-pagination-item");
        console.log("pageItems", pageItems.length);
        pageItems.forEach(pageItem => {
          pageItem.addEventListener("click", async () => {
            console.log("aaa clike");
            setTimeout(async () => {
              await insertStringToCardWrappers();
              await insertAiAudioBtn();
            }, 0x7d0);
          });
        });
        aalock = false;
      }
    });
  });
}
async function insertDownBtns() {
  const versionCheck = await versionChecker.checkVersion();
  console.log('canContinue', versionCheck);
  if (versionCheck.enable) {
    console.log('版本检查通过');
    waitForElement(".index_module__actionButtons____2fbb", async function (actionButtonsContainer) {
      getProductInfo();
      const downloadImageBtn = document.createElement('button');
      downloadImageBtn.style.marginRight = '10px';
      downloadImageBtn.style.marginTop = "6px";
      downloadImageBtn.style.borderColor = "green";
      downloadImageBtn.style.color = 'green';
      downloadImageBtn.className = "auxo-btn auxo-btn-dashed";
      downloadImageBtn.innerHTML = "<i class=\"fas fa-download mr-1\"></i> 下载图片";
      const downloadImageWithCartBtn = document.createElement('button');
      downloadImageWithCartBtn.style.marginRight = "10px";
      downloadImageWithCartBtn.style.marginTop = '6px';
      downloadImageWithCartBtn.style.borderColor = 'orange';
      downloadImageWithCartBtn.style.color = 'orange';
      downloadImageWithCartBtn.className = "auxo-btn auxo-btn-dashed";
      downloadImageWithCartBtn.innerHTML = "<i class=\"fas fa-download mr-1\"></i> 下载图片(加购物车)";
      const downloadVideoBtn = document.createElement('button');
      downloadVideoBtn.style.marginRight = "10px";
      downloadVideoBtn.style.marginTop = '6px';
      downloadVideoBtn.className = "auxo-btn auxo-btn-dashed";
      downloadVideoBtn.innerHTML = "<i class=\"fas fa-download mr-1\"></i> 下载视频";
      let coverImage = getBaiyingImageUrls()[0x0];
      let productName = getProductName();
      let projectInfo = {
        'product_id': product_id,
        'product_name': productName,
        'cover': coverImage
      };
      console.log('baiying_project_info', projectInfo);
      downloadImageBtn.addEventListener("click", async () => {
        downloadImageBtn.disabled = true;
        downloadImageBtn.innerHTML = "<span>下载中...</span>";
        try {
          chrome.storage.local.set({
            'baiying_project_info': projectInfo
          }, async () => {
            await checkTitleText(async () => {
              console.log("product_id数据已保存:" + product_id);
              await saveProject();
              await downImage();
            });
          });
        } catch (error) {
          console.log('error', error);
        }
        downloadImageBtn.disabled = false;
        downloadImageBtn.innerHTML = '<span>下载图片</span>';
      });
      downloadImageWithCartBtn.addEventListener("click", async () => {
        downloadImageWithCartBtn.disabled = true;
        downloadImageWithCartBtn.innerHTML = "<span>下载中...</span>";
        try {
          chrome.storage.local.set({
            'baiying_project_info': projectInfo
          }, async () => {
            await checkTitleText(async () => {
              console.log("product_id数据已保存:" + product_id);
              await saveProject();
              await downImage();
              triggerButtonClick();
            });
          });
        } catch (error) {
          console.log("error", error);
        }
        downloadImageWithCartBtn.disabled = false;
        downloadImageWithCartBtn.innerHTML = "<span>下载图片(加购物车)</span>";
      });
      downloadVideoBtn.addEventListener("click", async () => {
        downloadVideoBtn.disabled = true;
        downloadVideoBtn.innerHTML = "<span>下载中...</span>";
        try {
          chrome.storage.local.set({
            'baiying_project_info': projectInfo
          }, async () => {
            await checkTitleText(async () => {
              await saveProject();
              await downMainVideo();
            });
          });
        } catch (error) {
          console.log('error', error);
        }
        downloadVideoBtn.disabled = false;
        downloadVideoBtn.innerHTML = '<span>下载视频</span>';
      });
      const goToKaogujiaBtn = document.createElement('button');
      goToKaogujiaBtn.style.marginRight = "10px";
      goToKaogujiaBtn.style.marginTop = '6px';
      goToKaogujiaBtn.style.borderColor = "red";
      goToKaogujiaBtn.style.color = 'red';
      goToKaogujiaBtn.className = "auxo-btn auxo-btn-dashed";
      goToKaogujiaBtn.innerHTML = "<i class=\"fas fa-volume-up mr-1\"></i> 去考古加";
      goToKaogujiaBtn.addEventListener("click", async () => {
        const titleElement = document.querySelector(".index_module__title____450e");
        if (!titleElement.textContent.trim()) {
          return void alert("没有产品名称");
        }
        if (titleElement.textContent.trim().replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, '')) {
          chrome.storage.local.set({
            'baiying_project_info': projectInfo
          }, async () => {
            window.open("https://www.kaogujia.com/darenSquare/videoList?keyword=" + encodeURIComponent("https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?id=" + product_id + "%26origin_type=pc_buyin_selection_decision"), "_blank");
          });
        } else {
          alert('产品名称不合法');
        }
      });
      const goToDouyinBtn = document.createElement('button');
      goToDouyinBtn.style.marginRight = "10px";
      goToDouyinBtn.style.marginTop = '6px';
      goToDouyinBtn.style.borderColor = 'red';
      goToDouyinBtn.style.color = 'red';
      goToDouyinBtn.className = "auxo-btn auxo-btn-dashed";
      goToDouyinBtn.innerHTML = "<i class=\"fas fa-volume-up mr-1\"></i> 去抖音";
      goToDouyinBtn.addEventListener("click", async () => {
        const titleElement = document.querySelector('.index_module__title____450e');
        if (!titleElement.textContent.trim()) {
          return void alert("没有产品名称");
        }
        const cleanedTitle = titleElement.textContent.trim().replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, '');
        if (cleanedTitle) {
          chrome.storage.local.set({
            'baiying_project_info': projectInfo
          }, async () => {
            window.open("https://www.douyin.com/root/search/" + encodeURIComponent(cleanedTitle) + "?aid=745ad0ce-6c4e-4551-94eb-71a2a0a0f48e&type=general", '_blank');
          });
        } else {
          alert("产品名称不合法");
        }
      });
      actionButtonsContainer.insertBefore(goToDouyinBtn, actionButtonsContainer.firstChild);
      actionButtonsContainer.insertBefore(goToKaogujiaBtn, actionButtonsContainer.firstChild);
      actionButtonsContainer.insertBefore(downloadImageBtn, actionButtonsContainer.firstChild);
      actionButtonsContainer.insertBefore(downloadImageWithCartBtn, actionButtonsContainer.firstChild);
      actionButtonsContainer.insertBefore(downloadVideoBtn, actionButtonsContainer.firstChild);
    });
  } else {
    console.log("版本检查未通过");
  }
}
function checkUpdateProjectElment() {
  let checkInterval;
  checkInterval = setInterval(async function () {
    if (document.querySelector(".index_module__titleContainer____450e")) {
      console.log('商品id目标元素已加载');
      bindTabsClick();
      insertParamsToNode();
      await insertDownBtns();
      let coverImage = getBaiyingImageUrls()[0x0];
      let productName = getProductName();
      let projectInfo = {
        'product_id': product_id,
        'product_name': productName,
        'cover': coverImage
      };
      console.log("checkParamsElement baiying_project_info", projectInfo);
      chrome.storage.local.set({
        'baiying_project_info': projectInfo
      }, () => {
        console.log("product_id数据已保存:" + product_id);
      });
      clearInterval(checkInterval);
    } else {
      console.log("商品id模板元素未加载");
    }
  }, 0x3e8);
  setTimeout(() => {
    clearInterval(checkInterval);
    console.log('清理商品id目标元素');
  }, 0x7530);
}
async function init() {
  product_id = getUrlParam("product_id");
  if (product_id) {
    console.log("获取链接中的id", product_id);
    checkUpdateProjectElment();
  } else {
    let copyIdCheckInterval;
    copyIdCheckInterval = setInterval(function () {
      const copyIdButton = document.querySelector('.index_module__copyId____0e09');
      if (copyIdButton) {
        console.log("目标元素已加载");
        copyIdButton.click();
        setTimeout(async () => {
          await document.body.focus();
          const clipboardText = await navigator.clipboard.readText();
          console.log('当前剪贴板内容：', clipboardText);
          if (!product_id) {
            product_id = clipboardText;
            checkUpdateProjectElment();
          }
        }, 0x7d0);
        clearInterval(copyIdCheckInterval);
      } else {
        console.log("模板元素未加载");
      }
    }, 0x64);
    setTimeout(() => {
      clearInterval(copyIdCheckInterval);
      console.log("清理目标元素");
    }, 0x7530);
  }
}
const waitForElement = (selector, callback) => {
  const element = document.querySelector(selector);
  if (element) {
    return void callback(element);
  }
  const observer = new MutationObserver(() => {
    const foundElement = document.querySelector(selector);
    if (foundElement) {
      callback(foundElement);
      observer.disconnect();
    }
  });
  observer.observe(document.body, {
    'childList': true,
    'subtree': true
  });
};
async function callDoubaoAPI2(productName) {
  const prompt = "请根据商品名称，生成一份300字以内的口播文案：参考下面这个文案风格（自然亲切，避免硬广词汇），不要带家人们这种套近乎的词，也不需要提醒赶紧入手：\n\t参考文案：不要再买169一个的坐姿椅了， 科轩尼联合敦煌博物馆一起宠粉了 升级的新款新色， 不仅颜色温柔好看， 支撑力和舒适性也做了提升， 就算200斤也能牢牢撑住！ 人体工学设计， 坐上瞬间就能把腰背给你好好托住， 久坐不会伤腰累腰。 整体克重也做了减轻， 单只手就能轻松提握， 不管是放在椅子上、地上， 甚至躺床上刷手机， 都能垫一个。 有了它， 就算久坐8小时也很轻松刷到！ 活动还在的赶紧来冲！\n商品名称：\n" + productName;
  try {
    const response = await fetch("https://ark.cn-beijing.volces.com/api/v3/chat/completions", {
      'method': "POST",
      'headers': {
        'Content-Type': "application/json",
        'Authorization': "Bearer 148cad4d-631d-4419-b991-b551d85aab5e"
      },
      'body': JSON.stringify({
        'model': 'doubao-1-5-pro-32k-250115',
        'messages': [{
          'role': "system",
          'content': "你是一个专业的口播文案撰写者，擅长创作简洁、有吸引力的产品介绍文案。"
        }, {
          'role': 'user',
          'content': prompt
        }],
        'temperature': 0.7,
        'max_tokens': 0x12c
      })
    });
    if (!response.ok) {
      throw new Error("HTTP错误! 状态码: " + response.status);
    }
    return (await response.json()).choices[0x0].message.content;
  } catch (error) {
    console.error("调用API时出错:", error);
    throw error;
  }
}
async function callDoubaoAPI(referenceText) {
  const prompt = "请根据以下参考文案，生成一份70秒以内的口播文案。内容要口语化、有感染力，能够突出产品特点和促销信息：\n    \n参考文案：\n" + referenceText;
  try {
    const response = await fetch('https://ark.cn-beijing.volces.com/api/v3/chat/completions', {
      'method': "POST",
      'headers': {
        'Content-Type': "application/json",
        'Authorization': "Bearer 148cad4d-631d-4419-b991-b551d85aab5e"
      },
      'body': JSON.stringify({
        'model': "doubao-1-5-pro-32k-250115",
        'messages': [{
          'role': "system",
          'content': "你是一个专业的口播文案撰写者，擅长创作简洁、有吸引力的产品介绍文案。"
        }, {
          'role': "user",
          'content': prompt
        }],
        'temperature': 0.7,
        'max_tokens': 0x12c
      })
    });
    if (!response.ok) {
      throw new Error("HTTP错误! 状态码: " + response.status);
    }
    return (await response.json()).choices[0x0].message.content;
  } catch (error) {
    console.error("调用API时出错:", error);
    throw error;
  }
}
async function callTtsApi(text) {
  try {
    if (!productInfo.userId) {
      productInfo.userId = "anonymous";
    }
    if (!productInfo.excuteTime) {
      return void alert("执行批次不正确，请检查");
    }
    alert("语音合成功能已禁用：后续可接入自建 TTS 服务");
    return {
      'success': false,
      'error': "TTS_DISABLED"
    };
  } catch (error) {
    console.error("调用API时出错:", error);
    throw error;
  }
}
async function insertAiAudioBtn() {
  const leftButtons = document.querySelectorAll(".index_module__leftButton____1821");
  if (leftButtons.length > 0x0) {
    leftButtons.forEach((leftButton) => {
      leftButton.addEventListener("click", function () {
        waitForElement(".auxo-modal-footer", modalFooter => {
          const aiAudioBtn = document.createElement("button");
          aiAudioBtn.type = "button";
          aiAudioBtn.className = "auxo-btn auxo-btn-primary";
          aiAudioBtn.innerHTML = "<span>生成AI音频</span>";
          modalFooter.insertBefore(aiAudioBtn, modalFooter.firstChild);
          aiAudioBtn.addEventListener("click", async () => {
            try {
              aiAudioBtn.disabled = true;
              aiAudioBtn.innerHTML = '<span>生成中...</span>';
              const actionRows = document.querySelectorAll('.index_module__actionRow___b5587');
              let contentText = '';
              if (actionRows.length >= 0x2) {
                const contentArea = actionRows[0x1].querySelector(".index_module__contentArea___b5587");
                if (contentArea) {
                  contentArea.querySelectorAll("[elementtiming=\"element-timing\"]").forEach(element => {
                    contentText += element.textContent.trim() + "\n";
                  });
                  contentText = contentText.slice(0x0, -0x1);
                }
              }
              console.log(contentText);
              const generatedScript = await callDoubaoAPI(contentText);
              console.log("result", generatedScript);
              await callTtsApi(generatedScript);
              aiAudioBtn.disabled = false;
              aiAudioBtn.innerHTML = "<span>生成AI音频</span>";
            } catch (error) {
              console.error("生成口播失败:", error);
              alert("生成口播失败: " + error.message);
              aiAudioBtn.disabled = false;
              aiAudioBtn.innerHTML = "<span>生成AI音频</span>";
            }
          });
          const audioBtn = document.createElement("button");
          audioBtn.type = "button";
          audioBtn.className = "auxo-btn auxo-btn-primary";
          audioBtn.innerHTML = "<span>生成音频</span>";
          modalFooter.insertBefore(audioBtn, modalFooter.firstChild);
          audioBtn.addEventListener("click", async () => {
            try {
              audioBtn.disabled = true;
              audioBtn.innerHTML = "<span>生成中...</span>";
              const actionRows = document.querySelectorAll(".index_module__actionRow___b5587");
              let contentText = '';
              if (actionRows.length >= 0x2) {
                const contentArea = actionRows[0x1].querySelector(".index_module__contentArea___b5587");
                if (contentArea) {
                  contentArea.querySelectorAll("[elementtiming=\"element-timing\"]").forEach(element => {
                    contentText += element.textContent.trim() + "\n";
                  });
                  contentText = contentText.slice(0x0, -0x1);
                }
              }
              console.log(contentText);
              await callTtsApi(contentText);
              aiAudioBtn.disabled = false;
              aiAudioBtn.innerHTML = "<span>生成音频</span>";
            } catch (error) {
              console.error("生成口播文案失败:", error);
              alert("生成口播文案失败: " + error.message);
              aiAudioBtn.disabled = false;
              aiAudioBtn.innerHTML = "<span>生成音频</span>";
            }
          });
        });
      });
    });
  } else {
    console.warn("未找到任何左侧按钮元素");
  }
}
function showCopySuccessAlert(message) {
  const alertDiv = document.createElement("div");
  alertDiv.textContent = message;
  alertDiv.classList.add('copy-success-alert');
  document.body.appendChild(alertDiv);
  setTimeout(() => {
    alertDiv.remove();
  }, 0xbb8);
}
function showCopyErrorAlert(message) {
  const alertDiv = document.createElement("div");
  alertDiv.textContent = message;
  alertDiv.classList.add('copy-error-alert');
  document.body.appendChild(alertDiv);
  setTimeout(() => {
    alertDiv.remove();
  }, 0xbb8);
}
function insertParamsToNode() {
  const titleContainer = document.querySelector(".index_module__titleContainer____450e");
  if (titleContainer) {
    const productIdSpan = document.createElement("span");
    productIdSpan.textContent = '' + product_id;
    productIdSpan.classList.add("param-style");
    productIdSpan.addEventListener("click", () => {
      navigator.clipboard.writeText(productIdSpan.textContent).then(() => {
        console.log("复制成功");
        showCopySuccessAlert(productIdSpan.textContent + "复制成功");
      })["catch"](error => {
        console.error("复制失败:", error);
      });
    });
    const setDirectoryBtn = document.createElement("div");
    setDirectoryBtn.textContent = "修改下载目录";
    setDirectoryBtn.classList.add("delete-button-style");
    setDirectoryBtn.addEventListener("click", async () => {
      console.log("修改下载目录");
      chrome.runtime.sendMessage({
        'action': "setDirectory"
      }, response => {
        console.log("setDirectory Response:", response);
      });
    });
    const deleteBtn = document.createElement("div");
    deleteBtn.textContent = '删除';
    deleteBtn.classList.add("delete-button-style");
    deleteBtn.addEventListener("click", async () => {
      console.log("开始删除");
      try {
        alert("已移除服务器同步删除功能（后续可接入自建后端）");
        return;
      } catch (error) {
        console.error("查询失败: " + error.message);
      }
    });
    const paramContainer = document.createElement("div");
    paramContainer.classList.add("param-container");
    paramContainer.appendChild(productIdSpan);
    paramContainer.appendChild(deleteBtn);
    paramContainer.appendChild(setDirectoryBtn);
    titleContainer.appendChild(paramContainer);
  }
}
function customEncode(text) {
  const charCodes = Array.from(text).map(char => char.charCodeAt(0x0));
  const hashArray = new Array(0x10).fill(0x0);
  charCodes.forEach((charCode, index) => {
    const position = index % 0x10;
    hashArray[position] = (hashArray[position] + charCode) % 0x100;
  });
  return hashArray.map(value => value.toString(0x10).padStart(0x2, '0')).join('').substring(0x0, 0x10);
}
function getBaiyingImageUrls() {
  try {
    const imageUrls = [];
    const slickTrack = document.querySelector("div.slick-track");
    if (slickTrack) {
      const images = slickTrack.querySelectorAll("img");
      console.log("获取到图片标签数: " + images.length);
      const mainContent = document.querySelector("div.index_module__mainContent___ac928");
      const hasVideo = !!mainContent && null !== mainContent.querySelector('video');
      let hasSkippedFirst = false;
      images.forEach((image, index) => {
        if (hasVideo && 0x0 === index && !hasSkippedFirst) {
          console.log('跳过第一个图片，因为主内容区域包含视频元素');
          return void (hasSkippedFirst = true);
        }
        const imgSrc = image.getAttribute("src");
        if (imgSrc) {
          const fullUrl = new URL(imgSrc, window.location.href).href;
          imageUrls.push(fullUrl);
        } else {
          console.log('未获取到img_src属性');
        }
      });
    } else {
      console.log("未获取到slick-track元素");
    }
    return imageUrls;
  } catch (error) {
    console.error("发生错误:", error);
    return [];
  }
}
function getVideoUrlFromParent(element) {
  const cardWrapper = element.closest(".index_module__cardWrapper____3c42");
  if (cardWrapper) {
    const videoElement = cardWrapper.querySelector("video");
    if (videoElement) {
      const videoSrc = videoElement.src;
      const sourceElement = videoElement.querySelector('source');
      return (sourceElement ? sourceElement.src : null) || videoSrc;
    }
  }
  return null;
}
async function getMainVideoUrlFromParent() {
  const videoElement = (await new Promise(resolve => {
    waitForElement(".index_module__mainContent___ac928", resolve);
  })).querySelector('video');
  if (!videoElement) {
    return void alert("未找到视频元素");
  }
  const videoSrc = videoElement.src;
  return videoSrc ? (console.log("获取到视频源:", videoSrc), videoSrc) : null;
}
async function downloadResource(url, filename, directory = '') {
  const fullPath = directory ? directory + '/' + filename : filename;
  try {
    if (!url || !url.startsWith("http")) {
      throw new Error("无效的URL: " + url);
    }
    console.log("开始下载: " + fullPath);
    const response = await fetch(url, {
      'method': "GET",
      'mode': "cors",
      'credentials': "same-origin"
    });
    if (!response.ok) {
      throw new Error("下载失败: " + response.status + " " + response.statusText);
    }
    const contentType = response.headers.get("Content-Type");
    const contentLength = response.headers.get("Content-Length");
    console.log("info", '响应信息：类型=' + contentType + '，预计大小=' + (contentLength ? (contentLength / 0x400 / 0x400).toFixed(0x2) + 'MB' : '未知'));
    if (!contentType?.["startsWith"]('video/')) {
      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = fullPath;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
      }, 0x3e8);
      return {
        'success': true,
        'filename': fullPath
      };
    }
    const reader = response.body.getReader();
    const chunks = [];
    let bytesRead = 0x0;
    for (console.log("info", '开始分块读取数据...');;) {
      const {
        done,
        value
      } = await reader.read();
      if (done) {
        break;
      }
      chunks.push(value);
      bytesRead += value.byteLength;
      if (contentLength) {
        const progress = bytesRead / contentLength * 0x64;
        if (progress % 0xa < 0.1 || bytesRead % 0x500000 < 0x400) {
          console.log("info", "下载进度: " + progress.toFixed(0x1) + "% (" + (bytesRead / 0x400 / 0x400).toFixed(0x2) + "MB/" + (contentLength / 0x400 / 0x400).toFixed(0x2) + "MB)");
        }
      } else {
        console.log("info", "已读取: " + (bytesRead / 0x400 / 0x400).toFixed(0x2) + 'MB');
      }
    }
    if (contentLength && bytesRead !== parseInt(contentLength)) {
      throw new Error("数据不完整：实际读取" + bytesRead + "字节，预期" + contentLength + '字节');
    }
    console.log("info", '分块读取完成，共' + chunks.length + '块，开始合并为Blob');
    const blob = new Blob(chunks, {
      'type': contentType
    });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fullPath;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    }, 0x3e8);
    return {
      'success': true,
      'filename': fullPath
    };
  } catch (error) {
    console.error("下载 " + fullPath + " 失败:", error);
    return {
      'success': false,
      'filename': fullPath,
      'error': error.message
    };
  }
}
window.addEventListener("DOMContentLoaded", loadSharedData);
let image_is_down = false;
async function downImage() {
  if (productInfo.userId) {
    if (productInfo.excuteTime) {
      if (!image_is_down) {
        getBaiyingImageUrls().forEach(async (imageUrl, index) => {
          const filename = productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + "_image_" + (index + 0x1) + ".jpg";
          await downloadResource(imageUrl, filename);
        });
        image_is_down = true;
      }
    } else {
      alert('执行批次不正确，请检查');
    }
  } else {
    alert("用户标识缺失，请刷新后重试");
  }
}
async function downMainVideo() {
  if (!productInfo.userId) {
    productInfo.userId = "anonymous";
  }
  if (!productInfo.excuteTime) {
    return void alert("执行批次不正确，请检查");
  }
  let videoUrl = await getMainVideoUrlFromParent();
  if (videoUrl) {
    await downloadResource(videoUrl, productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + "_video_1.mp4");
  }
}
async function extractPageResources(event, videoNumber) {
  if (!productInfo.userId) {
    productInfo.userId = "anonymous";
  }
  if (!productInfo.excuteTime) {
    return void alert('执行批次不正确，请检查');
  }
  let videoUrl = getVideoUrlFromParent(event.target);
  if (videoUrl) {
    await downloadResource(videoUrl, productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + '_video_' + videoNumber + '.mp4');
  }
  await downImage();
}
function getMidnightTimestamp() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
}
function triggerButtonClick() {
  const actionButtonsContainer = document.querySelector(".index_module__actionButtons____2fbb");
  if (actionButtonsContainer) {
    const primaryButton = actionButtonsContainer.querySelector(".auxo-btn-primary");
    if (primaryButton) {
      primaryButton.click();
      console.log('已触发按钮点击事件');
    } else {
      console.error("未找到class为\"auxo-btn-primary\"的按钮元素");
    }
  } else {
    console.error("未找到class为\"index_module__actionButtons____2fbb\"的父容器元素");
  }
}
async function checkTitleText(callback) {
  if (!product_id) {
    return void alert('商品id数据缺失，请刷新后重试');
  }
  const titleElement = document.querySelector('.index_module__title____450e');
  if (!titleElement.textContent.trim()) {
    return void alert("没有产品名称");
  }
  // NOTE: 原实现会在此处调用远端服务做“违规词/违规商品”检测。
  // 当前版本移除了对外部服务（zmapi.umyw.cn）的依赖；后续可在此处接入自建检测服务。
  await callback();
}
async function saveProject() {
  // NOTE: 原实现会把选品数据保存到远端服务（zmapi.umyw.cn）。
  // 当前版本仅保留本地下载能力；后续可在此处接入自建后端。
  return;
}
async function downRes(event, videoNumber) {
  await checkTitleText(async () => {
    await saveProject();
    await extractPageResources(event, videoNumber);
  });
}
async function insertStringToCardWrappers() {
  let cardContainer = document.querySelector('.index_module__cardContainer____3c42');
  if (!cardContainer) {
    for (await delay(0x64); !cardContainer;) {
      await delay(0x64);
      cardContainer = document.querySelector('.index_module__cardContainer____3c42');
    }
  }
  let contentCards = cardContainer.querySelectorAll(".index_module__contentCard____1821");
  if (!contentCards) {
    for (await delay(0x64); !contentCards;) {
      await delay(0x64);
      contentCards = cardContainer.querySelectorAll('.index_module__contentCard____1821');
    }
  }
  for (let i = 0x0; i < contentCards.length; i++) {
    const contentCard = contentCards[i];
    if (contentCard.querySelector('.param-style')) {
      continue;
    }
    await delay(0x64);
    let nameElement = contentCard.querySelector('.index_module__name____1821');
    for (; !nameElement;) {
      await delay(0x64);
      nameElement = contentCard.querySelector('.index_module__name____1821');
    }
    const publishTimeElement = contentCard.querySelector(".index_module__publishTime____1821");
    const descLineElement = contentCard.querySelector(".index_module__descLine____1821");
    if (!customEncode(nameElement.textContent.trim() + publishTimeElement.textContent.trim() + descLineElement.textContent.trim())) {
      continue;
    }
    const download1Btn = document.createElement('button');
    download1Btn.textContent = "下载1";
    download1Btn.classList.add("select-button-style");
    download1Btn.addEventListener('click', async event => {
      download1Btn.disabled = true;
      download1Btn.innerHTML = "<span>下载中...</span>";
      await downRes(event, 0x1);
      download1Btn.disabled = false;
      download1Btn.innerHTML = "<span>下载1</span>";
    });
    const download2Btn = document.createElement("button");
    download2Btn.textContent = '下载2';
    download2Btn.classList.add("select-button-style");
    download2Btn.addEventListener('click', async event => {
      download2Btn.disabled = true;
      download2Btn.innerHTML = "<span>下载中...</span>";
      await downRes(event, 0x2);
      download2Btn.disabled = false;
      download2Btn.innerHTML = "<span>下载2</span>";
    });
    const download3Btn = document.createElement("button");
    download3Btn.textContent = "下载3";
    download3Btn.classList.add("select-button-style");
    download3Btn.addEventListener('click', async event => {
      download3Btn.disabled = true;
      download3Btn.innerHTML = "<span>下载中...</span>";
      await downRes(event, 0x3);
      download3Btn.disabled = false;
      download3Btn.innerHTML = "<span>下载3</span>";
    });
    const buttonContainer = document.createElement("div");
    buttonContainer.classList.add("param-container");
    buttonContainer.appendChild(download1Btn);
    buttonContainer.appendChild(download2Btn);
    buttonContainer.appendChild(download3Btn);
    contentCard.prepend(buttonContainer);
  }
  const downloadAllBtn = document.createElement("button");
  downloadAllBtn.textContent = '下载全部视频';
  downloadAllBtn.classList.add("select-button-style");
  downloadAllBtn.classList.add('download-all-videos-button');
  const downloadCurrentPageBtn = document.createElement("button");
  async function downloadSingleVideo(cardElement, videoIndex) {
    if (!productInfo.userId) {
      productInfo.userId = "anonymous";
    }
    if (!productInfo.excuteTime) {
      alert("执行批次不正确，请检查");
      return false;
    }
    try {
      const videoElement = cardElement.querySelector('video');
      let videoUrl = null;
      if (videoElement) {
        const videoSrc = videoElement.src;
        const sourceElement = videoElement.querySelector("source");
        videoUrl = sourceElement ? sourceElement.src : videoSrc;
      }
      if (videoUrl && videoUrl.startsWith("http")) {
        await downloadResource(videoUrl, productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + "_video_" + videoIndex + ".mp4");
        return true;
      }
      throw new Error('未找到有效的视频URL');
    } catch (error) {
      console.error("下载第 " + videoIndex + " 个视频失败:", error);
      return false;
    }
  }
  async function downloadAllVideosOnPage(indexOffset = 0x0) {
    let successCount = 0x0;
    let failCount = 0x0;
    let videoCards = [];
    try {
      console.log("开始下载全部视频，起始索引偏移: " + indexOffset);
      const cardContainer = document.querySelector('.index_module__cardContainer____3c42');
      if (!cardContainer) {
        alert("未找到视频卡片容器");
        return {
          'successCount': successCount,
          'failCount': failCount,
          'totalCount': 0x0
        };
      }
      videoCards = cardContainer.querySelectorAll('.index_module__contentCard____1821');
      let retryCount = 0x0;
      for (; 0x0 === videoCards.length && retryCount < 0x5;) {
        await delay(0x64);
        videoCards = cardContainer.querySelectorAll('.index_module__contentCard____1821');
        retryCount++;
      }
      if (0x0 === videoCards.length) {
        alert("未找到视频卡片");
        return {
          'successCount': successCount,
          'failCount': failCount,
          'totalCount': 0x0
        };
      }
      console.log("找到 " + videoCards.length + " 个视频卡片，开始批量下载");
      for (let i = 0x0; i < videoCards.length; i++) {
        const currentCard = videoCards[i];
        const videoIndex = indexOffset + i + 0x1;
        try {
          if (await downloadSingleVideo(currentCard, videoIndex)) {
            successCount++;
          } else {
            failCount++;
          }
        } catch (error) {
          failCount++;
          console.error("下载第 " + videoIndex + " 个视频失败:", error);
        }
        await delay(0x1f4);
      }
      return {
        'successCount': successCount,
        'failCount': failCount,
        'totalCount': videoCards.length
      };
    } catch (error) {
      console.error("批量下载过程中出错:", error);
      return {
        'successCount': successCount,
        'failCount': failCount,
        'totalCount': videoCards.length,
        'error': error.message
      };
    }
  }
  async function downloadAllVideosAcrossPages() {
    console.log("开始分页下载所有视频");
    let totalVideoCount = 0x0;
    totalVideoCount += (await downloadAllVideosOnPage(totalVideoCount)).totalCount;
    const paginationContainer = document.querySelector(".auxo-pagination");
    if (!paginationContainer) {
      return void console.log("未找到分页元素");
    }
    const paginationItems = paginationContainer.querySelectorAll(".auxo-pagination-item");
    const pageLinks = [];
    for (let i = 0x0; i < paginationItems.length; i++) {
      if (paginationItems[i].classList.contains("auxo-pagination-item-1")) {
        continue;
      }
      const pageLink = paginationItems[i].querySelector('a');
      if (pageLink) {
        pageLinks.push(pageLink);
      }
    }
    console.log("找到 " + pageLinks.length + " 个分页标签需要处理");
    for (let pageIndex = 0x0; pageIndex < pageLinks.length; pageIndex++) {
      console.log("处理第 " + (pageIndex + 0x1) + " 个分页标签");
      pageLinks[pageIndex].click();
      await delay(0x7d0);
      totalVideoCount += (await downloadAllVideosOnPage(totalVideoCount)).totalCount;
    }
    console.log("所有分页的视频下载完成");
    alert("所有分页的视频下载完成！");
  }
  downloadCurrentPageBtn.textContent = "下载当前页面视频";
  downloadCurrentPageBtn.classList.add("select-button-style");
  downloadCurrentPageBtn.classList.add('download-all-videos-button');
  downloadAllBtn.addEventListener('click', async () => {
    downloadAllBtn.disabled = true;
    downloadAllBtn.innerHTML = "<span>分页下载中...</span>";
    try {
      await downloadAllVideosAcrossPages();
    } catch (error) {
      console.error('分页下载过程中出错:', error);
      alert("分页下载过程中发生错误，请重试");
    } finally {
      downloadAllBtn.disabled = false;
      downloadAllBtn.innerHTML = "<span>下载全部视频</span>";
    }
  });
  downloadCurrentPageBtn.addEventListener("click", async () => {
    downloadCurrentPageBtn.disabled = true;
    downloadCurrentPageBtn.innerHTML = '<span>分页下载中...</span>';
    try {
      await downloadAllVideosAcrossPages();
    } catch (error) {
      console.error('分页下载过程中出错:', error);
      alert("分页下载过程中发生错误，请重试");
    } finally {
      downloadCurrentPageBtn.disabled = false;
      downloadCurrentPageBtn.innerHTML = "<span>下载全部视频</span>";
    }
  });
}

*/
