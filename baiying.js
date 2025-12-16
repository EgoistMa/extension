let aalock = false;
let product_id = null;
function earlyInjectScript() {
  try {
    if ("loading" === document.readyState) {
      document.addEventListener('DOMContentLoaded', injectScriptToPage);
    } else {
      injectScriptToPage();
    }
  } catch (_0x379329) {
    console.error('【智能选品】初始化注入脚本失败:', _0x379329);
    setTimeout(earlyInjectScript, 0x64);
  }
}
function injectScriptToPage() {
  try {
    if (!document.head && !document.documentElement) {
      console.warn('【智能选品】DOM元素尚未准备好，稍后重试');
      return void setTimeout(injectScriptToPage, 0xa);
    }
    const _0x3cfd59 = document.createElement("script");
    _0x3cfd59.src = chrome.runtime.getURL('assets/insert.js');
    (document.head || document.documentElement).appendChild(_0x3cfd59);
    _0x3cfd59.onload = function () {
      console.info('【智能选品】插入的脚本加载成功.');
      _0x3cfd59.remove();
    };
    _0x3cfd59.onerror = function () {
      console.error("【智能选品】插入的脚本加载失败.");
      setTimeout(injectScriptToPage, 0x3e8);
    };
  } catch (_0x411c52) {
    console.error('【智能选品】注入脚本过程出错:', _0x411c52);
  }
}
earlyInjectScript();
window.addEventListener('message', function (_0x388bf0) {
  try {
    if (_0x388bf0.data && _0x388bf0.data.action && 'onPackDetail' === _0x388bf0.data.action) {
      console.log("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", _0x388bf0.data);
      if (!product_id) {
        product_id = _0x388bf0.data.data.product_id;
        checkUpdateProjectElment();
      }
    }
  } catch (_0x269956) {
    console.error("【智能选品】处理页面脚本消息失败:", _0x269956);
  }
}, false);
chrome.runtime.onMessage.addListener(function (_0x52ea0b, _0x3ccf02, _0xe77407) {
  if ("dataUpdated" === _0x52ea0b.action) {
    window.location.reload();
  }
});
let user = null;
function loadUser(_0x90be6d) {
  user = null;
  chrome.storage.local.get('xuanpin_user', function (_0x28a850) {
    if (_0x28a850.xuanpin_user) {
      user = JSON.parse(_0x28a850.xuanpin_user);
      console.log("xuanpin_user======>", user);
      _0x90be6d();
    }
  });
}
function loadSharedData() {
  loadUser(init);
}
class DouyinWordDetector {
  constructor(_0x3a94c5) {
    this.apiUrl = _0x3a94c5;
  }
  async ["checkText"](_0x20f0e0, _0x5d0784) {
    try {
      const _0x1b1738 = await fetch(this.apiUrl, {
        'method': "POST",
        'headers': {
          'Content-Type': 'application/json'
        },
        'body': JSON.stringify({
          'text': _0x20f0e0,
          'product_id': _0x5d0784
        })
      });
      if (!_0x1b1738.ok) {
        throw new Error("HTTP error! status: " + _0x1b1738.status);
      }
      return await _0x1b1738.json();
    } catch (_0x2853ed) {
      console.error("检测过程中发生错误:", _0x2853ed);
      return {
        'hasViolation': false,
        'error': _0x2853ed.message
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
  const _0x5c5453 = document.querySelector(".index_module__title____450e");
  return _0x5c5453 ? _0x5c5453.textContent.trim() : '';
}
function getProductInfo() {
  productInfo = {};
  if (!user || !user.id) {
    return void alert("没有登录");
  }
  const _0x1c8283 = getUrlParam('id');
  productInfo.userId = user.id;
  productInfo.excuteTime = getMidnightTimestamp();
  productInfo.noSelectSevenDay = false;
  productInfo.deleted = 0x0;
  productInfo.promotion_id = _0x1c8283;
  productInfo.product_id = product_id;
  console.log('bbbbbbbbbbbbb==>productInfo', productInfo);
  const _0x3f755c = document.querySelector(".index_module__dataCardContainer____0bd5");
  if (_0x3f755c) {
    _0x3f755c.querySelectorAll(".index_module__dataItem____0bd5").forEach(_0x208bb2 => {
      let _0x16f6da = _0x208bb2.querySelector('.index_module__dataTitle____0bd5');
      let _0x2c8f1d = null;
      let _0x490d65 = null;
      if (_0x16f6da) {
        _0x2c8f1d = _0x16f6da.textContent.trim();
        const _0x33efa4 = _0x208bb2.querySelector(".index_module__dataContent____0bd5");
        if (!_0x33efa4) {
          return;
        }
        _0x490d65 = _0x33efa4.textContent.trim();
      } else {
        const _0x40e655 = _0x208bb2.querySelector(".index_module__dataContent____0bd5");
        if (!_0x40e655) {
          return;
        }
        _0x16f6da = _0x40e655.querySelector('span:nth-of-type(1)');
        if (!_0x16f6da) {
          return;
        }
        _0x2c8f1d = _0x16f6da.textContent.trim();
        const _0x2a48cf = _0x40e655.querySelector("span:nth-of-type(2)");
        if (!_0x2a48cf) {
          return;
        }
        _0x490d65 = _0x2a48cf.textContent.trim();
      }
      switch (_0x2c8f1d) {
        case '到手价':
          const _0x5c54b3 = _0x490d65.match(/¥\d+(\.\d+)?/);
          productInfo.product_price = _0x5c54b3 ? _0x5c54b3[0x0] : '0';
          break;
        case "团长高佣":
        case '专属高佣':
        case '佣金':
          const _0x531f31 = _0x490d65.match(/\d+(\.\d+)?%/);
          const _0x46d3aa = _0x490d65.match(/赚\d+(\.\d+)?/);
          productInfo.cos_ratio = _0x531f31 ? _0x531f31[0x0] : '0';
          productInfo.cos_fee = _0x46d3aa ? _0x46d3aa[0x0].replace('赚', '¥') : '0';
          break;
        case '好评率':
          productInfo.good_ratio = _0x490d65 || '0';
          break;
        case '已售':
          if (_0x490d65 && _0x490d65.includes('万+')) {
            const _0x1510fa = _0x490d65.replace('万+', '');
            productInfo.sell_num = (0x2710 * parseFloat(_0x1510fa)).toString();
          } else {
            productInfo.sell_num = _0x490d65 || '0';
          }
          break;
        case "带货人数":
          if (_0x490d65 && _0x490d65.includes('万+')) {
            const _0x41b1c1 = _0x490d65.replace('万+', '');
            productInfo.author_num = (0x2710 * parseFloat(_0x41b1c1)).toString();
          } else {
            productInfo.author_num = _0x490d65 || '0';
          }
      }
    });
    if (!productInfo.product_price) {
      const _0x5ec135 = document.querySelector(".index_module__dataContent____0bd5 span:nth-child(2)");
      if (_0x5ec135) {
        productInfo.product_price = _0x5ec135.textContent.replace('¥', '');
        console.log('新元素中包含价格', productInfo.product_price);
      } else {
        console.log("未找到价格元素");
      }
    }
  } else {
    console.error('未找到数据容器，请检查HTML结构或类名是否正确');
  }
  const _0x438e23 = document.querySelector(".index_module__scoreContainer____1d3f");
  if (_0x438e23) {
    const _0x56a633 = _0x438e23.querySelector('.index_module__totalScore____1d3f');
    if (_0x56a633) {
      const _0x385c0e = _0x56a633.querySelector('.index_module__bigNum____1d3f');
      productInfo.service_score = _0x385c0e ? _0x385c0e.textContent.trim() + '分' : '0';
    } else {
      productInfo.service_score = '0';
    }
    const _0x4632e7 = _0x438e23.querySelectorAll(".index_module__detailItem____1d3f");
    if (_0x4632e7.length > 0x0) {
      _0x4632e7.forEach(_0xd5d874 => {
        const _0x274d0a = _0xd5d874.querySelector(".index_module__smallNum____1d3f");
        const _0x371948 = _0x274d0a ? _0x274d0a.textContent.trim() + '分' : "未获取到分数";
        const _0x1a1151 = _0xd5d874.querySelector(".index_module__textLine____1d3f");
        switch (_0x1a1151 ? _0x1a1151.textContent.trim() : '') {
          case '商品':
            productInfo.goods_score = _0x371948;
            break;
          case '物流':
            productInfo.logistics_score = _0x371948;
            break;
          case '商家':
            productInfo.exper_score = _0x371948;
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
    const _0x3ef873 = document.querySelector(".index_module__dataItemContainer____2d98");
    if (_0x3ef873) {
      _0x3ef873.querySelectorAll(".index_module__dataItem____45dd").forEach(_0x188980 => {
        const _0x3a8fa0 = _0x188980.querySelector(".index_module__title____45dd");
        if (!_0x3a8fa0) {
          return;
        }
        if ("出单达人数" === _0x3a8fa0.textContent.trim()) {
          const _0x10201f = _0x188980.querySelectorAll(".index_module__contentItem____45dd");
          if (!_0x10201f) {
            return;
          }
          _0x10201f.forEach(_0x347b17 => {
            if ('视频' === _0x347b17.querySelector('.index_module__contentType____45dd').textContent.trim()) {
              const _0x31a008 = _0x347b17.querySelector(".index_module__num____45dd");
              if (_0x31a008) {
                productInfo.by30.video_match_order_num = _0x31a008.textContent.trim();
              }
            }
          });
        }
      });
      const _0x4f3356 = document.querySelectorAll(".index_module__dataCardContainer____0bd5");
      const _0x263617 = (productInfo.by30.video_match_order_num / productInfo.author_num).toFixed(0x2);
      console.log('出单率=====》', productInfo.by30.video_match_order_num, productInfo.author_num);
      const _0x25bce5 = "\n\t\t\t<div class=\"index_module__dataItem____0bd5\" elementtiming=\"element-timing\" style=\"max-width: 150px; flex: 1 0 auto;\">\n\t\t\t  <div class=\"index_module__dataTitle____0bd5\" elementtiming=\"element-timing\">出单率</div>\n\t\t\t  <div class=\"index_module__dataContent____0bd5\" elementtiming=\"element-timing\">\n\t\t\t    <div elementtiming=\"element-timing\">" + _0x263617 + "</div>\n\t\t\t    <div class=\"index_module__suffix____0bd5 index_module__gap____0bd5\" elementtiming=\"element-timing\" style=\"position: relative; top: 2px;\"></div>\n\t\t\t  </div>\n\t\t\t</div>\n\t\t\t";
      _0x4f3356.forEach(_0x6f5be8 => {
        _0x6f5be8.insertAdjacentHTML("beforeend", _0x25bce5);
      });
    } else {
      console.error('未找到出单达人数据容器，请检查HTML类名是否正确');
    }
  }, 0x7d0);
}
function getUrlParam(_0xabb760) {
  const _0x87fad1 = window.location.search.slice(0x1).split('&');
  for (let _0x5f6f9f of _0x87fad1) {
    const [_0x5fff9c, _0x42e0ce] = _0x5f6f9f.split('=');
    if (decodeURIComponent(_0x5fff9c) === _0xabb760) {
      return decodeURIComponent(_0x42e0ce || '');
    }
  }
  return null;
}
function createButton(_0xc4116a, _0x34cd2d) {
  const _0x4df3cf = document.createElement("button");
  _0x4df3cf.textContent = _0xc4116a;
  _0x4df3cf.className = "your-custom-button-class";
  _0x4df3cf.addEventListener('click', _0x34cd2d);
  return _0x4df3cf;
}
async function bindTabsClick() {
  let _0x24ff62 = document.querySelectorAll(".auxo-tabs-tab");
  for (; !_0x24ff62;) {
    await delay(0x3e8);
    _0x24ff62 = document.querySelectorAll(".auxo-tabs-tab");
    console.log("等待tab出现");
  }
  _0x24ff62.forEach(_0x2c38de => {
    _0x2c38de.addEventListener("click", async () => {
      const _0x3732b5 = _0x2c38de.querySelector(".auxo-tabs-tab-btn").textContent.trim();
      console.log("点击了选项卡：" + _0x3732b5);
      if ("带货内容" == _0x3732b5) {
        if (aalock) {
          return;
        }
        aalock = true;
        await insertStringToCardWrappers();
        await insertAiAudioBtn();
        let _0x39f60b = document.querySelectorAll(".auxo-pagination-item");
        console.log("pageItems", _0x39f60b.length);
        _0x39f60b.forEach(_0x53be43 => {
          _0x53be43.addEventListener("click", async () => {
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
  const _0x481a62 = await versionChecker.checkVersion();
  console.log('canContinue', _0x481a62);
  if (_0x481a62.enable) {
    console.log('版本检查通过');
    waitForElement(".index_module__actionButtons____2fbb", async function (_0x2e90ba) {
      getProductInfo();
      const _0xd562c2 = document.createElement('button');
      _0xd562c2.style.marginRight = '10px';
      _0xd562c2.style.marginTop = "6px";
      _0xd562c2.style.borderColor = "green";
      _0xd562c2.style.color = 'green';
      _0xd562c2.className = "auxo-btn auxo-btn-dashed";
      _0xd562c2.innerHTML = "<i class=\"fas fa-download mr-1\"></i> 下载图片";
      const _0x2cd111 = document.createElement('button');
      _0x2cd111.style.marginRight = "10px";
      _0x2cd111.style.marginTop = '6px';
      _0x2cd111.style.borderColor = 'orange';
      _0x2cd111.style.color = 'orange';
      _0x2cd111.className = "auxo-btn auxo-btn-dashed";
      _0x2cd111.innerHTML = "<i class=\"fas fa-download mr-1\"></i> 下载图片(加购物车)";
      const _0x3aa45e = document.createElement('button');
      _0x3aa45e.style.marginRight = "10px";
      _0x3aa45e.style.marginTop = '6px';
      _0x3aa45e.className = "auxo-btn auxo-btn-dashed";
      _0x3aa45e.innerHTML = "<i class=\"fas fa-download mr-1\"></i> 下载视频";
      let _0x36fb36 = getBaiyingImageUrls()[0x0];
      let _0x1e14a7 = getProductName();
      let _0x3332de = {
        'product_id': product_id,
        'product_name': _0x1e14a7,
        'cover': _0x36fb36
      };
      console.log('baiying_project_info', _0x3332de);
      _0xd562c2.addEventListener("click", async () => {
        _0xd562c2.disabled = true;
        _0xd562c2.innerHTML = "<span>下载中...</span>";
        try {
          chrome.storage.local.set({
            'baiying_project_info': _0x3332de
          }, async () => {
            await checkTitleText(async () => {
              console.log("product_id数据已保存:" + product_id);
              await saveProject();
              await downImage();
            });
          });
        } catch (_0x2b0be8) {
          console.log('error', _0x2b0be8);
        }
        _0xd562c2.disabled = false;
        _0xd562c2.innerHTML = '<span>下载图片</span>';
      });
      _0x2cd111.addEventListener("click", async () => {
        _0x2cd111.disabled = true;
        _0x2cd111.innerHTML = "<span>下载中...</span>";
        try {
          chrome.storage.local.set({
            'baiying_project_info': _0x3332de
          }, async () => {
            await checkTitleText(async () => {
              console.log("product_id数据已保存:" + product_id);
              await saveProject();
              await downImage();
              triggerButtonClick();
            });
          });
        } catch (_0xc4e1e8) {
          console.log("error", _0xc4e1e8);
        }
        _0x2cd111.disabled = false;
        _0x2cd111.innerHTML = "<span>下载图片(加购物车)</span>";
      });
      _0x3aa45e.addEventListener("click", async () => {
        _0x3aa45e.disabled = true;
        _0x3aa45e.innerHTML = "<span>下载中...</span>";
        try {
          chrome.storage.local.set({
            'baiying_project_info': _0x3332de
          }, async () => {
            await checkTitleText(async () => {
              await saveProject();
              await downMainVideo();
            });
          });
        } catch (_0x469804) {
          console.log('error', _0x469804);
        }
        _0x3aa45e.disabled = false;
        _0x3aa45e.innerHTML = '<span>下载视频</span>';
      });
      const _0x1b0d89 = document.createElement('button');
      _0x1b0d89.style.marginRight = "10px";
      _0x1b0d89.style.marginTop = '6px';
      _0x1b0d89.style.borderColor = "red";
      _0x1b0d89.style.color = 'red';
      _0x1b0d89.className = "auxo-btn auxo-btn-dashed";
      _0x1b0d89.innerHTML = "<i class=\"fas fa-volume-up mr-1\"></i> 去考古加";
      _0x1b0d89.addEventListener("click", async () => {
        const _0x3ec8d2 = document.querySelector(".index_module__title____450e");
        if (!_0x3ec8d2.textContent.trim()) {
          return void alert("没有产品名称");
        }
        if (_0x3ec8d2.textContent.trim().replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, '')) {
          chrome.storage.local.set({
            'baiying_project_info': _0x3332de
          }, async () => {
            window.open("https://www.kaogujia.com/darenSquare/videoList?keyword=" + encodeURIComponent("https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?id=" + product_id + "%26origin_type=pc_buyin_selection_decision"), "_blank");
          });
        } else {
          alert('产品名称不合法');
        }
      });
      const _0x248086 = document.createElement('button');
      _0x248086.style.marginRight = "10px";
      _0x248086.style.marginTop = '6px';
      _0x248086.style.borderColor = 'red';
      _0x248086.style.color = 'red';
      _0x248086.className = "auxo-btn auxo-btn-dashed";
      _0x248086.innerHTML = "<i class=\"fas fa-volume-up mr-1\"></i> 去抖音";
      _0x248086.addEventListener("click", async () => {
        const _0x22dc60 = document.querySelector('.index_module__title____450e');
        if (!_0x22dc60.textContent.trim()) {
          return void alert("没有产品名称");
        }
        const _0x7703bb = _0x22dc60.textContent.trim().replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, '');
        if (_0x7703bb) {
          chrome.storage.local.set({
            'baiying_project_info': _0x3332de
          }, async () => {
            window.open("https://www.douyin.com/root/search/" + encodeURIComponent(_0x7703bb) + "?aid=745ad0ce-6c4e-4551-94eb-71a2a0a0f48e&type=general", '_blank');
          });
        } else {
          alert("产品名称不合法");
        }
      });
      _0x2e90ba.insertBefore(_0x248086, _0x2e90ba.firstChild);
      if (user && 0x1 == user.show_daren_listen) {
        _0x2e90ba.insertBefore(_0x1b0d89, _0x2e90ba.firstChild);
      }
      _0x2e90ba.insertBefore(_0xd562c2, _0x2e90ba.firstChild);
      _0x2e90ba.insertBefore(_0x2cd111, _0x2e90ba.firstChild);
      _0x2e90ba.insertBefore(_0x3aa45e, _0x2e90ba.firstChild);
    });
  } else {
    console.log("版本检查未通过");
  }
}
function checkUpdateProjectElment() {
  let _0x4d1c9f;
  _0x4d1c9f = setInterval(async function () {
    if (document.querySelector(".index_module__titleContainer____450e")) {
      console.log('商品id目标元素已加载');
      bindTabsClick();
      insertParamsToNode();
      await insertDownBtns();
      let _0x116b3d = getBaiyingImageUrls()[0x0];
      let _0x5c51d4 = getProductName();
      let _0x1ef068 = {
        'product_id': product_id,
        'product_name': _0x5c51d4,
        'cover': _0x116b3d
      };
      console.log("checkParamsElement baiying_project_info", _0x1ef068);
      chrome.storage.local.set({
        'baiying_project_info': _0x1ef068
      }, () => {
        console.log("product_id数据已保存:" + product_id);
      });
      clearInterval(_0x4d1c9f);
    } else {
      console.log("商品id模板元素未加载");
    }
  }, 0x3e8);
  setTimeout(() => {
    clearInterval(_0x4d1c9f);
    console.log('清理商品id目标元素');
  }, 0x7530);
}
async function init() {
  product_id = getUrlParam("product_id");
  if (product_id) {
    console.log("获取链接中的id", product_id);
    checkUpdateProjectElment();
  } else {
    let _0x7288b2;
    _0x7288b2 = setInterval(function () {
      const _0x4c6ff0 = document.querySelector('.index_module__copyId____0e09');
      if (_0x4c6ff0) {
        console.log("目标元素已加载");
        _0x4c6ff0.click();
        setTimeout(async () => {
          await document.body.focus();
          const _0x51d53d = await navigator.clipboard.readText();
          console.log('当前剪贴板内容：', _0x51d53d);
          if (!product_id) {
            product_id = _0x51d53d;
            checkUpdateProjectElment();
          }
        }, 0x7d0);
        clearInterval(_0x7288b2);
      } else {
        console.log("模板元素未加载");
      }
    }, 0x64);
    setTimeout(() => {
      clearInterval(_0x7288b2);
      console.log("清理目标元素");
    }, 0x7530);
  }
}
const waitForElement = (_0x422052, _0x90fe1d) => {
  const _0x269991 = document.querySelector(_0x422052);
  if (_0x269991) {
    return void _0x90fe1d(_0x269991);
  }
  const _0x235ac3 = new MutationObserver(_0x4a82b4 => {
    const _0x17d11c = document.querySelector(_0x422052);
    if (_0x17d11c) {
      _0x90fe1d(_0x17d11c);
      _0x235ac3.disconnect();
    }
  });
  _0x235ac3.observe(document.body, {
    'childList': true,
    'subtree': true
  });
};
async function callDoubaoAPI2(_0x50254f) {
  const _0x161ad6 = "请根据商品名称，生成一份300字以内的口播文案：参考下面这个文案风格（自然亲切，避免硬广词汇），不要带家人们这种套近乎的词，也不需要提醒赶紧入手：\n\t参考文案：不要再买169一个的坐姿椅了， 科轩尼联合敦煌博物馆一起宠粉了 升级的新款新色， 不仅颜色温柔好看， 支撑力和舒适性也做了提升， 就算200斤也能牢牢撑住！ 人体工学设计， 坐上瞬间就能把腰背给你好好托住， 久坐不会伤腰累腰。 整体克重也做了减轻， 单只手就能轻松提握， 不管是放在椅子上、地上， 甚至躺床上刷手机， 都能垫一个。 有了它， 就算久坐8小时也很轻松刷到！ 活动还在的赶紧来冲！\n商品名称：\n" + _0x50254f;
  try {
    const _0x4a980f = await fetch("https://ark.cn-beijing.volces.com/api/v3/chat/completions", {
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
          'content': _0x161ad6
        }],
        'temperature': 0.7,
        'max_tokens': 0x12c
      })
    });
    if (!_0x4a980f.ok) {
      throw new Error("HTTP错误! 状态码: " + _0x4a980f.status);
    }
    return (await _0x4a980f.json()).choices[0x0].message.content;
  } catch (_0x543832) {
    console.error("调用API时出错:", _0x543832);
    throw _0x543832;
  }
}
async function callDoubaoAPI(_0x5a8abd) {
  const _0x3df0bc = "请根据以下参考文案，生成一份70秒以内的口播文案。内容要口语化、有感染力，能够突出产品特点和促销信息：\n    \n参考文案：\n" + _0x5a8abd;
  try {
    const _0x52634a = await fetch('https://ark.cn-beijing.volces.com/api/v3/chat/completions', {
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
          'content': _0x3df0bc
        }],
        'temperature': 0.7,
        'max_tokens': 0x12c
      })
    });
    if (!_0x52634a.ok) {
      throw new Error("HTTP错误! 状态码: " + _0x52634a.status);
    }
    return (await _0x52634a.json()).choices[0x0].message.content;
  } catch (_0x3b6cc5) {
    console.error("调用API时出错:", _0x3b6cc5);
    throw _0x3b6cc5;
  }
}
async function callTtsApi(_0x4b2635) {
  try {
    if (!productInfo.userId) {
      return void alert("未登录，请重新登录");
    }
    if (!productInfo.excuteTime) {
      return void alert("执行批次不正确，请检查");
    }
    const _0x454783 = await fetch('https://zmapi.umyw.cn/tts_proxy.php', {
      'method': "POST",
      'headers': {
        'Content-Type': "application/json"
      },
      'body': JSON.stringify({
        'text': _0x4b2635 || "字节跳动语音合成"
      })
    });
    if (!_0x454783.ok) {
      throw new Error("HTTP错误! 状态码: " + _0x454783.status);
    }
    const _0x10009a = await _0x454783.json();
    console.log("API响应:", _0x10009a);
    if (_0x10009a && _0x10009a.data) {
      const _0x46c388 = atob(_0x10009a.data);
      const _0x19869c = new ArrayBuffer(_0x46c388.length);
      const _0x2ee2dd = new Uint8Array(_0x19869c);
      for (let _0x4a18b9 = 0x0; _0x4a18b9 < _0x46c388.length; _0x4a18b9++) {
        _0x2ee2dd[_0x4a18b9] = _0x46c388.charCodeAt(_0x4a18b9);
      }
      const _0xc7777f = new Blob([_0x19869c], {
        'type': "audio/mp3"
      });
      const _0x46c27e = URL.createObjectURL(_0xc7777f);
      const _0x1725c0 = document.createElement('a');
      _0x1725c0.href = _0x46c27e;
      _0x1725c0.download = productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + '_audio_1.mp3';
      document.body.appendChild(_0x1725c0);
      _0x1725c0.click();
      setTimeout(() => {
        document.body.removeChild(_0x1725c0);
        URL.revokeObjectURL(_0x46c27e);
      }, 0x64);
    }
  } catch (_0x19ed27) {
    console.error("调用API时出错:", _0x19ed27);
    throw _0x19ed27;
  }
}
async function insertAiAudioBtn() {
  const _0x1d3261 = document.querySelectorAll(".index_module__leftButton____1821");
  if (_0x1d3261.length > 0x0) {
    _0x1d3261.forEach((_0x4274c4, _0x3c0b01) => {
      _0x4274c4.addEventListener("click", function () {
        waitForElement(".auxo-modal-footer", _0x43858a => {
          const _0xee5f7 = document.createElement("button");
          _0xee5f7.type = "button";
          _0xee5f7.className = "auxo-btn auxo-btn-primary";
          _0xee5f7.innerHTML = "<span>生成AI音频</span>";
          _0x43858a.insertBefore(_0xee5f7, _0x43858a.firstChild);
          _0xee5f7.addEventListener("click", async () => {
            try {
              _0xee5f7.disabled = true;
              _0xee5f7.innerHTML = '<span>生成中...</span>';
              const _0x4060ef = document.querySelectorAll('.index_module__actionRow___b5587');
              let _0xbd4da2 = '';
              if (_0x4060ef.length >= 0x2) {
                const _0x4e9f1a = _0x4060ef[0x1].querySelector(".index_module__contentArea___b5587");
                if (_0x4e9f1a) {
                  _0x4e9f1a.querySelectorAll("[elementtiming=\"element-timing\"]").forEach(_0x22bbd6 => {
                    _0xbd4da2 += _0x22bbd6.textContent.trim() + "\n";
                  });
                  _0xbd4da2 = _0xbd4da2.slice(0x0, -0x1);
                }
              }
              console.log(_0xbd4da2);
              const _0x507469 = await callDoubaoAPI(_0xbd4da2);
              console.log("result", _0x507469);
              await callTtsApi(_0x507469);
              _0xee5f7.disabled = false;
              _0xee5f7.innerHTML = "<span>生成AI音频</span>";
            } catch (_0x533c87) {
              console.error("生成口播失败:", _0x533c87);
              alert("生成口播失败: " + _0x533c87.message);
              _0xee5f7.disabled = false;
              _0xee5f7.innerHTML = "<span>生成AI音频</span>";
            }
          });
          const _0x2e1314 = document.createElement("button");
          _0x2e1314.type = "button";
          _0x2e1314.className = "auxo-btn auxo-btn-primary";
          _0x2e1314.innerHTML = "<span>生成音频</span>";
          _0x43858a.insertBefore(_0x2e1314, _0x43858a.firstChild);
          _0x2e1314.addEventListener("click", async () => {
            try {
              _0x2e1314.disabled = true;
              _0x2e1314.innerHTML = "<span>生成中...</span>";
              const _0xc2938e = document.querySelectorAll(".index_module__actionRow___b5587");
              let _0x2f2f3f = '';
              if (_0xc2938e.length >= 0x2) {
                const _0x89e552 = _0xc2938e[0x1].querySelector(".index_module__contentArea___b5587");
                if (_0x89e552) {
                  _0x89e552.querySelectorAll("[elementtiming=\"element-timing\"]").forEach(_0xac4d42 => {
                    _0x2f2f3f += _0xac4d42.textContent.trim() + "\n";
                  });
                  _0x2f2f3f = _0x2f2f3f.slice(0x0, -0x1);
                }
              }
              console.log(_0x2f2f3f);
              await callTtsApi(_0x2f2f3f);
              _0xee5f7.disabled = false;
              _0xee5f7.innerHTML = "<span>生成音频</span>";
            } catch (_0x3b6895) {
              console.error("生成口播文案失败:", _0x3b6895);
              alert("生成口播文案失败: " + _0x3b6895.message);
              _0xee5f7.disabled = false;
              _0xee5f7.innerHTML = "<span>生成音频</span>";
            }
          });
        });
      });
    });
  } else {
    console.warn("未找到任何左侧按钮元素");
  }
}
function showCopySuccessAlert(_0x19afa1) {
  const _0x599d55 = document.createElement("div");
  _0x599d55.textContent = _0x19afa1;
  _0x599d55.classList.add('copy-success-alert');
  document.body.appendChild(_0x599d55);
  setTimeout(() => {
    _0x599d55.remove();
  }, 0xbb8);
}
function showCopyErrorAlert(_0x441265) {
  const _0x56d63e = document.createElement("div");
  _0x56d63e.textContent = _0x441265;
  _0x56d63e.classList.add('copy-error-alert');
  document.body.appendChild(_0x56d63e);
  setTimeout(() => {
    _0x56d63e.remove();
  }, 0xbb8);
}
function insertParamsToNode() {
  const _0x17eab6 = document.querySelector(".index_module__titleContainer____450e");
  if (_0x17eab6) {
    const _0x370645 = document.createElement("span");
    _0x370645.textContent = '' + product_id;
    _0x370645.classList.add("param-style");
    _0x370645.addEventListener("click", () => {
      navigator.clipboard.writeText(_0x370645.textContent).then(() => {
        console.log("复制成功");
        showCopySuccessAlert(_0x370645.textContent + "复制成功");
      })["catch"](_0x5cf3da => {
        console.error("复制失败:", _0x5cf3da);
      });
    });
    const _0x565715 = document.createElement("div");
    _0x565715.textContent = "修改下载目录";
    _0x565715.classList.add("delete-button-style");
    _0x565715.addEventListener("click", async () => {
      console.log("修改下载目录");
      chrome.runtime.sendMessage({
        'action': "setDirectory"
      }, _0x52be46 => {
        console.log("setDirectory Response:", _0x52be46);
      });
    });
    const _0x4c8288 = document.createElement("div");
    _0x4c8288.textContent = '删除';
    _0x4c8288.classList.add("delete-button-style");
    _0x4c8288.addEventListener("click", async () => {
      console.log("开始删除");
      try {
        if (!user || !user.id) {
          return void alert("没有登录");
        }
        const _0x15c921 = await fetch("https://zmapi.umyw.cn/delete_data.php?userId=" + user.id + "&product_id=" + product_id);
        if (!_0x15c921.ok) {
          throw new Error("请求失败");
        }
        if ("success" === (await _0x15c921.json()).status) {
          showCopySuccessAlert(product_id + "删除成功");
        }
      } catch (_0x5ce56a) {
        console.error("查询失败: " + _0x5ce56a.message);
      }
    });
    const _0x15de38 = document.createElement("div");
    _0x15de38.classList.add("param-container");
    _0x15de38.appendChild(_0x370645);
    _0x15de38.appendChild(_0x4c8288);
    _0x15de38.appendChild(_0x565715);
    _0x17eab6.appendChild(_0x15de38);
  }
}
function customEncode(_0x203b20) {
  const _0x163df2 = Array.from(_0x203b20).map(_0x23e107 => _0x23e107.charCodeAt(0x0));
  const _0x660218 = new Array(0x10).fill(0x0);
  _0x163df2.forEach((_0x54c9d0, _0x194d2d) => {
    const _0x528549 = _0x194d2d % 0x10;
    _0x660218[_0x528549] = (_0x660218[_0x528549] + _0x54c9d0) % 0x100;
  });
  return _0x660218.map(_0x29bb48 => _0x29bb48.toString(0x10).padStart(0x2, '0')).join('').substring(0x0, 0x10);
}
function getBaiyingImageUrls() {
  try {
    const _0x1226a0 = [];
    const _0x44cc0f = document.querySelector("div.slick-track");
    if (_0x44cc0f) {
      const _0x28b741 = _0x44cc0f.querySelectorAll("img");
      console.log("获取到图片标签数: " + _0x28b741.length);
      const _0x1e5139 = document.querySelector("div.index_module__mainContent___ac928");
      const _0x5118b3 = !!_0x1e5139 && null !== _0x1e5139.querySelector('video');
      let _0x41a9c7 = false;
      _0x28b741.forEach((_0x50b361, _0x381b31) => {
        if (_0x5118b3 && 0x0 === _0x381b31 && !_0x41a9c7) {
          console.log('跳过第一个图片，因为主内容区域包含视频元素');
          return void (_0x41a9c7 = true);
        }
        const _0x5e422c = _0x50b361.getAttribute("src");
        if (_0x5e422c) {
          const _0x4c520c = new URL(_0x5e422c, window.location.href).href;
          _0x1226a0.push(_0x4c520c);
        } else {
          console.log('未获取到img_src属性');
        }
      });
    } else {
      console.log("未获取到slick-track元素");
    }
    return _0x1226a0;
  } catch (_0x314e0c) {
    console.error("发生错误:", _0x314e0c);
    return [];
  }
}
function getVideoUrlFromParent(_0x2aa723) {
  const _0x3d37cb = _0x2aa723.closest(".index_module__cardWrapper____3c42");
  if (_0x3d37cb) {
    const _0x37782e = _0x3d37cb.querySelector("video");
    if (_0x37782e) {
      const _0x26eb87 = _0x37782e.src;
      const _0x253345 = _0x37782e.querySelector('source');
      return (_0x253345 ? _0x253345.src : null) || _0x26eb87;
    }
  }
  return null;
}
async function getMainVideoUrlFromParent() {
  const _0x2ab56c = (await new Promise(_0x1cec1c => {
    waitForElement(".index_module__mainContent___ac928", _0x1cec1c);
  })).querySelector('video');
  if (!_0x2ab56c) {
    return void alert("未找到视频元素");
  }
  const _0x1fb756 = _0x2ab56c.src;
  return _0x1fb756 ? (console.log("获取到视频源:", _0x1fb756), _0x1fb756) : null;
}
async function downloadResource(_0x5c16f7, _0x2cc97b, _0x32c80f = '') {
  const _0x20cc42 = _0x32c80f ? _0x32c80f + '/' + _0x2cc97b : _0x2cc97b;
  try {
    if (!_0x5c16f7 || !_0x5c16f7.startsWith("http")) {
      throw new Error("无效的URL: " + _0x5c16f7);
    }
    console.log("开始下载: " + _0x20cc42);
    const _0x31420a = await fetch(_0x5c16f7, {
      'method': "GET",
      'mode': "cors",
      'credentials': "same-origin"
    });
    if (!_0x31420a.ok) {
      throw new Error("下载失败: " + _0x31420a.status + " " + _0x31420a.statusText);
    }
    const _0x1f4138 = _0x31420a.headers.get("Content-Type");
    const _0x166a78 = _0x31420a.headers.get("Content-Length");
    console.log("info", '响应信息：类型=' + _0x1f4138 + '，预计大小=' + (_0x166a78 ? (_0x166a78 / 0x400 / 0x400).toFixed(0x2) + 'MB' : '未知'));
    if (!_0x1f4138?.["startsWith"]('video/')) {
      const _0x3326bd = await _0x31420a.blob();
      const _0x4af81c = document.createElement('a');
      _0x4af81c.href = URL.createObjectURL(_0x3326bd);
      _0x4af81c.download = _0x20cc42;
      _0x4af81c.style.display = 'none';
      document.body.appendChild(_0x4af81c);
      _0x4af81c.click();
      setTimeout(() => {
        document.body.removeChild(_0x4af81c);
        URL.revokeObjectURL(_0x4af81c.href);
      }, 0x3e8);
      return {
        'success': true,
        'filename': _0x20cc42
      };
    }
    const _0x7d53a1 = _0x31420a.body.getReader();
    const _0x97af4c = [];
    let _0x559604 = 0x0;
    for (console.log("info", '开始分块读取数据...');;) {
      const {
        done: _0x26f0e0,
        value: _0xff65fe
      } = await _0x7d53a1.read();
      if (_0x26f0e0) {
        break;
      }
      _0x97af4c.push(_0xff65fe);
      _0x559604 += _0xff65fe.byteLength;
      if (_0x166a78) {
        const _0xb7f72 = _0x559604 / _0x166a78 * 0x64;
        if (_0xb7f72 % 0xa < 0.1 || _0x559604 % 0x500000 < 0x400) {
          console.log("info", "下载进度: " + _0xb7f72.toFixed(0x1) + "% (" + (_0x559604 / 0x400 / 0x400).toFixed(0x2) + "MB/" + (_0x166a78 / 0x400 / 0x400).toFixed(0x2) + "MB)");
        }
      } else {
        console.log("info", "已读取: " + (_0x559604 / 0x400 / 0x400).toFixed(0x2) + 'MB');
      }
    }
    if (_0x166a78 && _0x559604 !== parseInt(_0x166a78)) {
      throw new Error("数据不完整：实际读取" + _0x559604 + "字节，预期" + _0x166a78 + '字节');
    }
    console.log("info", '分块读取完成，共' + _0x97af4c.length + '块，开始合并为Blob');
    const _0x31e381 = new Blob(_0x97af4c, {
      'type': _0x1f4138
    });
    const _0x46757d = document.createElement('a');
    _0x46757d.href = URL.createObjectURL(_0x31e381);
    _0x46757d.download = _0x20cc42;
    _0x46757d.style.display = 'none';
    document.body.appendChild(_0x46757d);
    _0x46757d.click();
    setTimeout(() => {
      document.body.removeChild(_0x46757d);
      URL.revokeObjectURL(_0x46757d.href);
    }, 0x3e8);
    return {
      'success': true,
      'filename': _0x20cc42
    };
  } catch (_0x49bf4f) {
    console.error("下载 " + _0x20cc42 + " 失败:", _0x49bf4f);
    return {
      'success': false,
      'filename': _0x20cc42,
      'error': _0x49bf4f.message
    };
  }
}
window.addEventListener("DOMContentLoaded", loadSharedData);
let image_is_down = false;
async function downImage() {
  if (productInfo.userId) {
    if (productInfo.excuteTime) {
      if (!image_is_down) {
        getBaiyingImageUrls().forEach(async (_0x2e20c2, _0x433b07) => {
          const _0x6bef2e = productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + "_image_" + (_0x433b07 + 0x1) + ".jpg";
          await downloadResource(_0x2e20c2, _0x6bef2e);
        });
        image_is_down = true;
      }
    } else {
      alert('执行批次不正确，请检查');
    }
  } else {
    alert("未登录，请重新登录");
  }
}
async function downMainVideo() {
  if (!productInfo.userId) {
    return void alert("未登录，请重新登录");
  }
  if (!productInfo.excuteTime) {
    return void alert("执行批次不正确，请检查");
  }
  let _0x3ea2cc = await getMainVideoUrlFromParent();
  if (_0x3ea2cc) {
    await downloadResource(_0x3ea2cc, productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + "_video_1.mp4");
  }
}
async function extractPageResources(_0x28f269, _0x5528d3) {
  if (!productInfo.userId) {
    return void alert("未登录，请重新登录");
  }
  if (!productInfo.excuteTime) {
    return void alert('执行批次不正确，请检查');
  }
  let _0x139352 = getVideoUrlFromParent(_0x28f269.target);
  if (_0x139352) {
    await downloadResource(_0x139352, productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + '_video_' + _0x5528d3 + '.mp4');
  }
  await downImage();
}
function getMidnightTimestamp() {
  const _0x324a10 = new Date();
  return new Date(_0x324a10.getFullYear(), _0x324a10.getMonth(), _0x324a10.getDate()).getTime();
}
function triggerButtonClick() {
  const _0x3c9eb3 = document.querySelector(".index_module__actionButtons____2fbb");
  if (_0x3c9eb3) {
    const _0xdd681d = _0x3c9eb3.querySelector(".auxo-btn-primary");
    if (_0xdd681d) {
      _0xdd681d.click();
      console.log('已触发按钮点击事件');
    } else {
      console.error("未找到class为\"auxo-btn-primary\"的按钮元素");
    }
  } else {
    console.error("未找到class为\"index_module__actionButtons____2fbb\"的父容器元素");
  }
}
async function checkTitleText(_0x1ff2a9) {
  if (!product_id) {
    return void alert('商品id数据缺失，请刷新后重试');
  }
  const _0x490ddf = document.querySelector('.index_module__title____450e');
  if (!_0x490ddf.textContent.trim()) {
    return void alert("没有产品名称");
  }
  const _0x5abe44 = new DouyinWordDetector("http://zmapi.umyw.cn/word_filter_api.php");
  console.log('产品名:', _0x490ddf.textContent.trim());
  const _0x4a6ffa = await _0x5abe44.checkText(_0x490ddf.textContent.trim(), product_id);
  console.log("检测结果:", _0x4a6ffa);
  let _0xde72c8 = '';
  if (_0x4a6ffa.hasWordViolation) {
    _0xde72c8 += "检测到违规词[" + _0x4a6ffa.matchedWord + "]，是否继续执行？";
  }
  if (_0x4a6ffa.hasProductViolation) {
    _0xde72c8 += "检测到违规产品[" + _0x4a6ffa.matchedProductId + "]，是否继续执行？";
  }
  if (_0xde72c8) {
    const _0x2850de = document.createElement('div');
    _0x2850de.style.cssText = "\n\t\t    position: fixed;\n\t\t    top: 50%;\n\t\t    left: 50%;\n\t\t    transform: translate(-50%, -50%);\n\t\t    background: white;\n\t\t    padding: 20px;\n\t\t    border-radius: 8px;\n\t\t    box-shadow: 0 4px 16px rgba(0,0,0,0.2);\n\t\t    z-index: 9999;\n\t\t    min-width: 300px;\n\t\t    font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif;\n\t\t  ";
    const _0x2f6caf = document.createElement('p');
    _0x2f6caf.textContent = _0xde72c8;
    _0x2f6caf.style.cssText = "margin: 0 0 15px; font-size: 15px;";
    const _0x514e46 = document.createElement('div');
    _0x514e46.style.cssText = "display: flex; justify-content: flex-end; gap: 10px;";
    const _0x5c0bda = document.createElement("button");
    _0x5c0bda.textContent = '继续';
    _0x5c0bda.style.cssText = "\n\t\t    background: #4CAF50;\n\t\t    color: white;\n\t\t    border: none;\n\t\t    padding: 8px 16px;\n\t\t    border-radius: 4px;\n\t\t    cursor: pointer;\n\t\t    font-size: 14px;\n\t\t  ";
    const _0x51aaf1 = document.createElement("button");
    _0x51aaf1.textContent = '取消';
    _0x51aaf1.style.cssText = "\n\t\t    background: #f44336;\n\t\t    color: white;\n\t\t    border: none;\n\t\t    padding: 8px 16px;\n\t\t    border-radius: 4px;\n\t\t    cursor: pointer;\n\t\t    font-size: 14px;\n\t\t  ";
    _0x514e46.appendChild(_0x51aaf1);
    _0x514e46.appendChild(_0x5c0bda);
    _0x2850de.appendChild(_0x2f6caf);
    _0x2850de.appendChild(_0x514e46);
    const _0x4bdbb7 = document.createElement('div');
    _0x4bdbb7.style.cssText = "\n\t\t    position: fixed;\n\t\t    top: 0;\n\t\t    left: 0;\n\t\t    width: 100%;\n\t\t    height: 100%;\n\t\t    background: rgba(0,0,0,0.5);\n\t\t    z-index: 9998;\n\t\t  ";
    document.body.appendChild(_0x4bdbb7);
    document.body.appendChild(_0x2850de);
    _0x51aaf1.addEventListener('click', () => {
      document.body.removeChild(_0x4bdbb7);
      document.body.removeChild(_0x2850de);
      throw new Error("用户取消操作");
    });
    _0x5c0bda.addEventListener("click", () => {
      document.body.removeChild(_0x4bdbb7);
      document.body.removeChild(_0x2850de);
      _0x1ff2a9();
    });
  } else {
    await _0x1ff2a9();
  }
}
async function saveProject() {
  if (!user || !user.id) {
    alert("没有登录");
    throw Error("没有登录");
  }
  productInfo.by30 = JSON.stringify(productInfo.by30);
  try {
    const _0x2a99e6 = await fetch("https://zmapi.umyw.cn/save_data.php", {
      'method': "POST",
      'headers': {
        'Authorization': "Bearer " + user.token,
        'Content-Type': "application/json"
      },
      'body': JSON.stringify(productInfo)
    });
    const _0x395bfa = await _0x2a99e6.json();
    if ("success" === _0x395bfa.status) {
      console.log("【智能选品】数据保存成功！ID：" + _0x395bfa.data.id);
      showCopySuccessAlert('成功');
    } else {
      console.error("【智能选品】保存错误：", _0x395bfa.message);
      showCopyErrorAlert(_0x395bfa.message);
      if (_0x395bfa.code && 0x191 == _0x395bfa.code) {
        chrome.storage.local.remove('xuanpin_user', function () {
          console.log("已删除 xuanpin_user");
          user = null;
          getProductInfo();
        });
      }
    }
  } catch (_0x34ba12) {
    console.error('【智能选品】捕获到异常：', _0x34ba12.message);
    showCopyErrorAlert(_0x34ba12.message);
  }
}
async function downRes(_0x57c41d, _0x258a5a) {
  await checkTitleText(async () => {
    await saveProject();
    await extractPageResources(_0x57c41d, _0x258a5a);
  });
}
async function insertStringToCardWrappers() {
  let _0x51ec11 = document.querySelector('.index_module__cardContainer____3c42');
  if (!_0x51ec11) {
    for (await delay(0x64); !_0x51ec11;) {
      await delay(0x64);
      _0x51ec11 = document.querySelector('.index_module__cardContainer____3c42');
    }
  }
  let _0xb8ec84 = _0x51ec11.querySelectorAll(".index_module__contentCard____1821");
  if (!_0xb8ec84) {
    for (await delay(0x64); !_0xb8ec84;) {
      await delay(0x64);
      _0xb8ec84 = _0x51ec11.querySelectorAll('.index_module__contentCard____1821');
    }
  }
  for (let _0x112088 = 0x0; _0x112088 < _0xb8ec84.length; _0x112088++) {
    const _0x5f1027 = _0xb8ec84[_0x112088];
    if (_0x5f1027.querySelector('.param-style')) {
      continue;
    }
    await delay(0x64);
    let _0x24593d = _0x5f1027.querySelector('.index_module__name____1821');
    for (; !_0x24593d;) {
      await delay(0x64);
      _0x24593d = _0x5f1027.querySelector('.index_module__name____1821');
    }
    const _0xe1610c = _0x5f1027.querySelector(".index_module__publishTime____1821");
    const _0x1563a6 = _0x5f1027.querySelector(".index_module__descLine____1821");
    if (!customEncode(_0x24593d.textContent.trim() + _0xe1610c.textContent.trim() + _0x1563a6.textContent.trim())) {
      continue;
    }
    const _0x55d1d0 = document.createElement('button');
    _0x55d1d0.textContent = "下载1";
    _0x55d1d0.classList.add("select-button-style");
    _0x55d1d0.addEventListener('click', async _0x27788f => {
      _0x55d1d0.disabled = true;
      _0x55d1d0.innerHTML = "<span>下载中...</span>";
      await downRes(_0x27788f, 0x1);
      _0x55d1d0.disabled = false;
      _0x55d1d0.innerHTML = "<span>下载1</span>";
    });
    const _0x548678 = document.createElement("button");
    _0x548678.textContent = '下载2';
    _0x548678.classList.add("select-button-style");
    _0x548678.addEventListener('click', async _0x3aed29 => {
      _0x548678.disabled = true;
      _0x548678.innerHTML = "<span>下载中...</span>";
      await downRes(_0x3aed29, 0x2);
      _0x548678.disabled = false;
      _0x548678.innerHTML = "<span>下载2</span>";
    });
    const _0x3c448d = document.createElement("button");
    _0x3c448d.textContent = "下载3";
    _0x3c448d.classList.add("select-button-style");
    _0x3c448d.addEventListener('click', async _0x5b0c44 => {
      _0x3c448d.disabled = true;
      _0x3c448d.innerHTML = "<span>下载中...</span>";
      await downRes(_0x5b0c44, 0x3);
      _0x3c448d.disabled = false;
      _0x3c448d.innerHTML = "<span>下载3</span>";
    });
    const _0x3cafa5 = document.createElement("div");
    _0x3cafa5.classList.add("param-container");
    _0x3cafa5.appendChild(_0x55d1d0);
    _0x3cafa5.appendChild(_0x548678);
    _0x3cafa5.appendChild(_0x3c448d);
    _0x5f1027.prepend(_0x3cafa5);
  }
  const _0x4c0592 = document.createElement("button");
  _0x4c0592.textContent = '下载全部视频';
  _0x4c0592.classList.add("select-button-style");
  _0x4c0592.classList.add('download-all-videos-button');
  const _0x4c6c56 = document.createElement("button");
  async function _0x39f0c2(_0x482427, _0x4e1c7d) {
    if (!productInfo.userId) {
      alert('未登录，请重新登录');
      return false;
    }
    if (!productInfo.excuteTime) {
      alert("执行批次不正确，请检查");
      return false;
    }
    try {
      const _0x22b585 = _0x482427.querySelector('video');
      let _0xa59fc0 = null;
      if (_0x22b585) {
        const _0xaf3fd4 = _0x22b585.src;
        const _0xa85b26 = _0x22b585.querySelector("source");
        _0xa59fc0 = _0xa85b26 ? _0xa85b26.src : _0xaf3fd4;
      }
      if (_0xa59fc0 && _0xa59fc0.startsWith("http")) {
        await downloadResource(_0xa59fc0, productInfo.userId + '_' + productInfo.excuteTime + '_' + product_id + "_video_" + _0x4e1c7d + ".mp4");
        return true;
      }
      throw new Error('未找到有效的视频URL');
    } catch (_0xc74db8) {
      console.error("下载第 " + _0x4e1c7d + " 个视频失败:", _0xc74db8);
      return false;
    }
  }
  async function _0x449301(_0x44507e = 0x0) {
    let _0x2a11b6 = 0x0;
    let _0x2d9e73 = 0x0;
    let _0x5bef09 = [];
    try {
      console.log("开始下载全部视频，起始索引偏移: " + _0x44507e);
      const _0x413503 = document.querySelector('.index_module__cardContainer____3c42');
      if (!_0x413503) {
        alert("未找到视频卡片容器");
        return {
          'successCount': _0x2a11b6,
          'failCount': _0x2d9e73,
          'totalCount': 0x0
        };
      }
      _0x5bef09 = _0x413503.querySelectorAll('.index_module__contentCard____1821');
      let _0x3c9f8b = 0x0;
      for (; 0x0 === _0x5bef09.length && _0x3c9f8b < 0x5;) {
        await delay(0x64);
        _0x5bef09 = _0x413503.querySelectorAll('.index_module__contentCard____1821');
        _0x3c9f8b++;
      }
      if (0x0 === _0x5bef09.length) {
        alert("未找到视频卡片");
        return {
          'successCount': _0x2a11b6,
          'failCount': _0x2d9e73,
          'totalCount': 0x0
        };
      }
      console.log("找到 " + _0x5bef09.length + " 个视频卡片，开始批量下载");
      for (let _0x516ebc = 0x0; _0x516ebc < _0x5bef09.length; _0x516ebc++) {
        const _0xbcab6f = _0x5bef09[_0x516ebc];
        const _0x246f7c = _0x44507e + _0x516ebc + 0x1;
        try {
          if (await _0x39f0c2(_0xbcab6f, _0x246f7c)) {
            _0x2a11b6++;
          } else {
            _0x2d9e73++;
          }
        } catch (_0x5c678e) {
          _0x2d9e73++;
          console.error("下载第 " + _0x246f7c + " 个视频失败:", _0x5c678e);
        }
        await delay(0x1f4);
      }
      return {
        'successCount': _0x2a11b6,
        'failCount': _0x2d9e73,
        'totalCount': _0x5bef09.length
      };
    } catch (_0x17ea6c) {
      console.error("批量下载过程中出错:", _0x17ea6c);
      return {
        'successCount': _0x2a11b6,
        'failCount': _0x2d9e73,
        'totalCount': _0x5bef09.length,
        'error': _0x17ea6c.message
      };
    }
  }
  async function _0x338061() {
    console.log("开始分页下载所有视频");
    let _0x2f0f34 = 0x0;
    _0x2f0f34 += (await _0x449301(_0x2f0f34)).totalCount;
    const _0x408448 = document.querySelector(".auxo-pagination");
    if (!_0x408448) {
      return void console.log("未找到分页元素");
    }
    const _0x56fcd2 = _0x408448.querySelectorAll(".auxo-pagination-item");
    const _0x3414c6 = [];
    for (let _0x365548 = 0x0; _0x365548 < _0x56fcd2.length; _0x365548++) {
      if (_0x56fcd2[_0x365548].classList.contains("auxo-pagination-item-1")) {
        continue;
      }
      const _0x2f14e6 = _0x56fcd2[_0x365548].querySelector('a');
      if (_0x2f14e6) {
        _0x3414c6.push(_0x2f14e6);
      }
    }
    console.log("找到 " + _0x3414c6.length + " 个分页标签需要处理");
    for (let _0x1007e4 = 0x0; _0x1007e4 < _0x3414c6.length; _0x1007e4++) {
      console.log("处理第 " + (_0x1007e4 + 0x1) + " 个分页标签");
      _0x3414c6[_0x1007e4].click();
      await delay(0x7d0);
      _0x2f0f34 += (await _0x449301(_0x2f0f34)).totalCount;
    }
    console.log("所有分页的视频下载完成");
    alert("所有分页的视频下载完成！");
  }
  _0x4c6c56.textContent = "下载当前页面视频";
  _0x4c6c56.classList.add("select-button-style");
  _0x4c6c56.classList.add('download-all-videos-button');
  _0x4c0592.addEventListener('click', async () => {
    _0x4c0592.disabled = true;
    _0x4c0592.innerHTML = "<span>分页下载中...</span>";
    try {
      await _0x338061();
    } catch (_0x3a2675) {
      console.error('分页下载过程中出错:', _0x3a2675);
      alert("分页下载过程中发生错误，请重试");
    } finally {
      _0x4c0592.disabled = false;
      _0x4c0592.innerHTML = "<span>下载全部视频</span>";
    }
  });
  _0x4c6c56.addEventListener("click", async () => {
    _0x4c6c56.disabled = true;
    _0x4c6c56.innerHTML = '<span>分页下载中...</span>';
    try {
      await _0x338061();
    } catch (_0x508bdb) {
      console.error('分页下载过程中出错:', _0x508bdb);
      alert("分页下载过程中发生错误，请重试");
    } finally {
      _0x4c6c56.disabled = false;
      _0x4c6c56.innerHTML = "<span>下载全部视频</span>";
    }
  });
}