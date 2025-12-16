async function getLogs() {
  return new Promise(_0x1ae9da => {
    chrome.storage.local.get('filterRecords', _0x4d2b7b => {
      _0x1ae9da(_0x4d2b7b.filterRecords || []);
    });
  });
}
const userStatus = document.getElementById('user-status');
const loginModal = document.getElementById("login-modal");
const logoutBtn = document.getElementById("logout-btn");
const loginBtn = document.getElementById('login-btn');
const usernameDisplay = document.getElementById("username-display");
const loginError = document.getElementById('login-error');
async function checkLoginStatus() {
  const _0x5edb16 = await getUser();
  console.log("user", _0x5edb16);
  if (_0x5edb16 && _0x5edb16.expires > Date.now()) {
    usernameDisplay.textContent = "欢迎 " + _0x5edb16.username;
    usernameDisplay.style.color = "#165DFF";
    usernameDisplay.style.fontWeight = "500";
    logoutBtn.style.display = "inline";
  } else {
    usernameDisplay.textContent = '请登录';
    usernameDisplay.style.color = "#6B7280";
    usernameDisplay.style.fontWeight = "normal";
    logoutBtn.style.display = 'none';
    chrome.storage.local.remove("xuanpin_user", function () {
      console.log("旧数据已删除");
    });
  }
}
async function getUser() {
  const _0x1ba92d = await getStorage("xuanpin_user");
  return _0x1ba92d.xuanpin_user ? (console.log("userStr", _0x1ba92d.xuanpin_user), JSON.parse(_0x1ba92d.xuanpin_user)) : null;
}
function getStorage(_0x5553d3) {
  return new Promise((_0x1886b9, _0x2d1c16) => {
    chrome.storage.local.get(_0x5553d3, _0x4c0ee1 => {
      if (chrome.runtime.lastError) {
        _0x2d1c16(chrome.runtime.lastError);
      } else {
        _0x1886b9(_0x4c0ee1);
      }
    });
  });
}
async function verify_user() {
  const _0x3f86fb = await getUser();
  if (_0x3f86fb) {
    const _0x1edfe6 = new URLSearchParams();
    _0x1edfe6.append("action", "verify_user");
    _0x1edfe6.append("username", _0x3f86fb.username);
    _0x1edfe6.append('token', _0x3f86fb.token);
    console.log("formData", _0x1edfe6, _0x3f86fb);
    try {
      const _0x128fb5 = await fetch("https://zmapi.umyw.cn/auto_douyin_video.php?action=verify_user", {
        'method': 'POST',
        'headers': {
          'Authorization': "Bearer " + _0x3f86fb.token
        },
        'body': _0x1edfe6
      });
      if (0xc8 === _0x128fb5.status) {
        const _0x313886 = await _0x128fb5.json();
        console.log('response', _0x313886);
        if ("error" != _0x313886.status) {
          loadFilterRecords();
          return void console.log('加载筛选记录');
        }
      }
    } catch (_0x1df018) {
      console.error("请求服务器验证时出错: " + _0x1df018);
      console.error(_0x1df018.stack);
    }
    chrome.storage.local.remove('xuanpin_user', function () {
      console.log("旧数据已删除");
    });
  }
  checkLoginStatus();
}
async function down(_0x2f9700) {
  try {
    const _0x512162 = await getUser();
    if (!_0x512162 || !_0x512162.id) {
      return void alert("没有登录");
    }
    const _0x4e2376 = await fetch("https://zmapi.umyw.cn/query_data.php?userId=" + _0x512162.id + "&excuteTime=" + _0x2f9700);
    if (!_0x4e2376.ok) {
      throw new Error("请求失败");
    }
    const _0x533979 = await _0x4e2376.json();
    if ("success" === _0x533979.status) {
      downloadFile(convertToCsv(_0x533979.data), "sales_data.csv");
    }
  } catch (_0x1d0146) {
    console.error("查询失败: " + _0x1d0146.message);
  }
}
function convertToCsv(_0xeed7a) {
  const _0xd998ca = [['商品ID', '组合', "话题1", '话题2', "话题3", "话题4", "话题5", '商品链接', "小黄车", "产品名", '口播', "新标题", '序号', "商品名称", '产品价格', "佣金费用", "佣金比例", '好评率', "销售数量", "商品评分", "物流评分", "商家分", "创建时间"].join(',')];
  console.log("convertToCsv data", _0xeed7a);
  _0xeed7a.forEach((_0x2c748f, _0x3c1659) => {
    console.log('item.sales', _0x2c748f.sales, _0x2c748f.lvs);
    let _0x3f7536 = _0x2c748f.hot_tags ? JSON.parse(_0x2c748f.hot_tags) : [];
    console.log("tag_arr", _0x3f7536, _0x3f7536.length);
    const _0x2b381e = ["=\"" + _0x2c748f.product_id + "\"", _0x2c748f.new_title + _0x2c748f.product_name + _0x2c748f.broadcast_script, _0x3f7536.length > 0x0 ? _0x3f7536[0x0] : '', _0x3f7536.length > 0x1 ? _0x3f7536[0x1] : '', _0x3f7536.length > 0x2 ? _0x3f7536[0x2] : '', _0x3f7536.length > 0x3 ? _0x3f7536[0x3] : '', _0x3f7536.length > 0x4 ? _0x3f7536[0x4] : '', _0x2c748f.detail_url, "视频同款" + _0x2c748f.product_shortname, _0x2c748f.product_name, _0x2c748f.broadcast_script, _0x2c748f.new_title, '' + (_0x3c1659 + 0x1), _0x2c748f.product_name, _0x2c748f.product_price, _0x2c748f.cos_fee, _0x2c748f.cos_ratio + '%', parseFloat(_0x2c748f.good_ratio).toFixed(0x2) + '%', _0x2c748f.sell_num, _0x2c748f.goods_score, _0x2c748f.logistics_score, _0x2c748f.service_score, _0x2c748f.create_time];
    _0xd998ca.push(_0x2b381e.join(','));
  });
  return "﻿" + _0xd998ca.join("\n");
}
function downloadFile(_0x2f32b6, _0x2aee84) {
  const _0x12cf39 = new Blob([_0x2f32b6], {
    'type': "application/vnd.ms-excel;charset=utf-8"
  });
  const _0x4ac341 = URL.createObjectURL(_0x12cf39);
  const _0x230820 = document.createElement('a');
  _0x230820.setAttribute("href", _0x4ac341);
  _0x230820.setAttribute('download', _0x2aee84);
  document.body.appendChild(_0x230820);
  _0x230820.click();
  document.body.removeChild(_0x230820);
  URL.revokeObjectURL(_0x4ac341);
}
function hideFilterRecordModal() {
  document.getElementById('filterRecordModal').style.display = 'none';
}
async function loadFilterRecords() {
  const _0x426799 = await getUser();
  if (!_0x426799 || !_0x426799.id) {
    return void alert("没有登录");
  }
  const _0x5da979 = new XMLHttpRequest();
  _0x5da979.open("GET", "https://zmapi.umyw.cn/filter_record_api.php?userId=" + encodeURIComponent(_0x426799.id), true);
  _0x5da979.onreadystatechange = function () {
    if (0x4 === _0x5da979.readyState && 0xc8 === _0x5da979.status) {
      renderFilterRecords(JSON.parse(_0x5da979.responseText));
    }
  };
  _0x5da979.send();
}
async function renderFilterRecords(_0x2d75fe) {
  const _0x12c0ae = document.getElementById("filterRecordTable").getElementsByTagName("tbody")[0x0];
  _0x12c0ae.innerHTML = '';
  const _0xce74e9 = await getUser();
  if (_0xce74e9 && _0xce74e9.id) {
    _0x2d75fe.forEach(_0x21cfe7 => {
      const _0x7c7b16 = document.createElement('tr');
      _0x7c7b16.innerHTML = "\n            <td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;\">" + formatDateTime(_0x21cfe7.excuteTime) + "</td>\n            <td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;\">" + (_0xce74e9.id + '_' + _0x21cfe7.excuteTime) + "</td>\n            <td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;\">" + _0x21cfe7.count + "</td>\n            <td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;width: 100px;\">\n                <button class=\"download-btn\" data-time=\"" + _0x21cfe7.excuteTime + "\">下载</button> \n\t\t\t\t<button class=\"info-btn\" data-time=\"" + _0x21cfe7.excuteTime + "\">详情</button>\n            </td>\n        ";
      _0x12c0ae.appendChild(_0x7c7b16);
      _0x7c7b16.querySelector(".download-btn").addEventListener('click', function () {
        down(_0x21cfe7.excuteTime);
      });
      _0x7c7b16.querySelector('.info-btn').addEventListener("click", function () {
        window.open("https://zmapi.umyw.cn/product_filter.php?userid=" + _0xce74e9.id + "&page=1&excuteTime=" + _0x21cfe7.excuteTime, "_blank");
      });
    });
  }
}
function formatDateTime(_0x28f04f) {
  console.log("timeStr", _0x28f04f);
  const _0x23bb14 = Number(_0x28f04f);
  return new Date(_0x23bb14).toLocaleString();
}
document.addEventListener('DOMContentLoaded', async function () {
  const _0x57a0a1 = await versionChecker.checkVersion();
  console.log("canContinue", _0x57a0a1);
  if (_0x57a0a1.enable) {
    document.getElementById("version_name").textContent = _0x57a0a1.version_name;
    verify_user();
    checkLoginStatus();
    userStatus.addEventListener("click", async _0x26c79e => {
      if (!_0x26c79e.target.closest("#logout-btn") && !_0x26c79e.target.closest("#filter-btn")) {
        const _0x1196cf = await getUser();
        if (!_0x1196cf || _0x1196cf.expires <= Date.now()) {
          return void (loginModal.style.display = 'flex');
        }
      }
    });
    loginBtn.addEventListener("click", async () => {
      const _0x71515b = document.getElementById("login-username").value;
      const _0x46814b = document.getElementById("login-password").value;
      console.log("login-btn”");
      if (!_0x71515b || !_0x46814b) {
        loginError.textContent = "请输入用户名和密码";
        return void (loginError.style.display = 'block');
      }
      try {
        const _0x124554 = await fetch('https://zmapi.umyw.cn/login.php', {
          'method': "POST",
          'headers': {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          'body': "username=" + encodeURIComponent(_0x71515b) + '&password=' + encodeURIComponent(_0x46814b) + "&software_type=3"
        });
        if (!_0x124554.ok) {
          throw new Error("网络响应错误");
        }
        const _0x364bc6 = await _0x124554.json();
        if (_0x364bc6.success) {
          console.log("show_daren_listen: data.show_daren_listen", _0x364bc6.user.show_daren_listen);
          chrome.storage.local.set({
            'xuanpin_user': JSON.stringify({
              'username': _0x364bc6.user.username,
              'id': _0x364bc6.user.id,
              'token': _0x364bc6.token,
              'show_daren_listen': _0x364bc6.user.show_daren_listen,
              'expires': Date.now() + 0x5265c00
            })
          }, function () {
            console.log("数据已保存到共享存储");
            chrome.tabs.query({}, function (_0xa67f6) {
              _0xa67f6.forEach(_0x4bce3e => {
                chrome.tabs.sendMessage(_0x4bce3e.id, {
                  'action': "dataUpdated"
                });
              });
            });
          });
          checkLoginStatus();
          loginModal.style.display = "none";
          loginError.style.display = "none";
        } else {
          loginError.textContent = _0x364bc6.message || "登录失败，请重试";
          loginError.style.display = 'block';
        }
      } catch (_0x50e1cc) {
        console.error('登录请求失败:', _0x50e1cc);
        loginError.textContent = "网络错误，请稍后重试";
        loginError.style.display = 'block';
      }
    });
    logoutBtn.addEventListener("click", () => {
      chrome.storage.local.remove('xuanpin_user', function () {
        console.log("旧数据已删除");
      });
      checkLoginStatus();
    });
  } else {
    console.log("版本检查未通过");
  }
});
document.getElementById('refresh-btn').addEventListener("click", loadFilterRecords);