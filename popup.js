async function getLogs() {
  return new Promise(resolve => {
    chrome.storage.local.get('filterRecords', result => {
      resolve(result.filterRecords || []);
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
  const user = await getUser();
  console.log("user", user);
  if (user && user.expires > Date.now()) {
    usernameDisplay.textContent = "欢迎 " + user.username;
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
  const storage = await getStorage("xuanpin_user");
  return storage.xuanpin_user ? (console.log("userStr", storage.xuanpin_user), JSON.parse(storage.xuanpin_user)) : null;
}
function getStorage(key) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.get(key, result => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve(result);
      }
    });
  });
}
async function verify_user() {
  const user = await getUser();
  if (user) {
    const formData = new URLSearchParams();
    formData.append("action", "verify_user");
    formData.append("username", user.username);
    formData.append('token', user.token);
    console.log("formData", formData, user);
    try {
      const response = await fetch("https://zmapi.umyw.cn/auto_douyin_video.php?action=verify_user", {
        'method': 'POST',
        'headers': {
          'Authorization': "Bearer " + user.token
        },
        'body': formData
      });
      if (0xc8 === response.status) {
        const data = await response.json();
        console.log('response', data);
        if ("error" != data.status) {
          loadFilterRecords();
          return void console.log('加载筛选记录');
        }
      }
    } catch (error) {
      console.error("请求服务器验证时出错: " + error);
      console.error(error.stack);
    }
    chrome.storage.local.remove('xuanpin_user', function () {
      console.log("旧数据已删除");
    });
  }
  checkLoginStatus();
}
async function down(excuteTime) {
  try {
    const user = await getUser();
    if (!user || !user.id) {
      return void alert("没有登录");
    }
    const response = await fetch("https://zmapi.umyw.cn/query_data.php?userId=" + user.id + "&excuteTime=" + excuteTime);
    if (!response.ok) {
      throw new Error("请求失败");
    }
    const result = await response.json();
    if ("success" === result.status) {
      downloadFile(convertToCsv(result.data), "sales_data.csv");
    }
  } catch (error) {
    console.error("查询失败: " + error.message);
  }
}
function convertToCsv(data) {
  const rows = [['商品ID', '组合', "话题1", '话题2', "话题3", "话题4", "话题5", '商品链接', "小黄车", "产品名", '口播', "新标题", '序号', "商品名称", '产品价格', "佣金费用", "佣金比例", '好评率', "销售数量", "商品评分", "物流评分", "商家分", "创建时间"].join(',')];
  console.log("convertToCsv data", data);
  data.forEach((item, index) => {
    console.log('item.sales', item.sales, item.lvs);
    let tagArr = item.hot_tags ? JSON.parse(item.hot_tags) : [];
    console.log("tag_arr", tagArr, tagArr.length);
    const row = ["=\"" + item.product_id + "\"", item.new_title + item.product_name + item.broadcast_script, tagArr.length > 0x0 ? tagArr[0x0] : '', tagArr.length > 0x1 ? tagArr[0x1] : '', tagArr.length > 0x2 ? tagArr[0x2] : '', tagArr.length > 0x3 ? tagArr[0x3] : '', tagArr.length > 0x4 ? tagArr[0x4] : '', item.detail_url, "视频同款" + item.product_shortname, item.product_name, item.broadcast_script, item.new_title, '' + (index + 0x1), item.product_name, item.product_price, item.cos_fee, item.cos_ratio + '%', parseFloat(item.good_ratio).toFixed(0x2) + '%', item.sell_num, item.goods_score, item.logistics_score, item.service_score, item.create_time];
    rows.push(row.join(','));
  });
  return "﻿" + rows.join("\n");
}
function downloadFile(content, filename) {
  const blob = new Blob([content], {
    'type': "application/vnd.ms-excel;charset=utf-8"
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute("href", url);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
function hideFilterRecordModal() {
  document.getElementById('filterRecordModal').style.display = 'none';
}
async function loadFilterRecords() {
  const user = await getUser();
  if (!user || !user.id) {
    return void alert("没有登录");
  }
  const xhr = new XMLHttpRequest();
  xhr.open("GET", "https://zmapi.umyw.cn/filter_record_api.php?userId=" + encodeURIComponent(user.id), true);
  xhr.onreadystatechange = function () {
    if (0x4 === xhr.readyState && 0xc8 === xhr.status) {
      renderFilterRecords(JSON.parse(xhr.responseText));
    }
  };
  xhr.send();
}
async function renderFilterRecords(records) {
  const tbody = document.getElementById("filterRecordTable").getElementsByTagName("tbody")[0x0];
  tbody.innerHTML = '';
  const user = await getUser();
  if (user && user.id) {
    records.forEach(record => {
      const row = document.createElement('tr');
      row.innerHTML = "\n            <td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;\">" + formatDateTime(record.excuteTime) + "</td>\n            <td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;\">" + (user.id + '_' + record.excuteTime) + "</td>\n            <td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;\">" + record.count + "</td>\n            <td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;width: 100px;\">\n                <button class=\"download-btn\" data-time=\"" + record.excuteTime + "\">下载</button> \n\t\t\t\t<button class=\"info-btn\" data-time=\"" + record.excuteTime + "\">详情</button>\n            </td>\n        ";
      tbody.appendChild(row);
      row.querySelector(".download-btn").addEventListener('click', function () {
        down(record.excuteTime);
      });
      row.querySelector('.info-btn').addEventListener("click", function () {
        window.open("https://zmapi.umyw.cn/product_filter.php?userid=" + user.id + "&page=1&excuteTime=" + record.excuteTime, "_blank");
      });
    });
  }
}
function formatDateTime(timeStr) {
  console.log("timeStr", timeStr);
  const timestamp = Number(timeStr);
  return new Date(timestamp).toLocaleString();
}
document.addEventListener('DOMContentLoaded', async function () {
  const versionCheck = await versionChecker.checkVersion();
  console.log("canContinue", versionCheck);
  if (versionCheck.enable) {
    document.getElementById("version_name").textContent = versionCheck.version_name;
    verify_user();
    checkLoginStatus();
    userStatus.addEventListener("click", async event => {
      if (!event.target.closest("#logout-btn") && !event.target.closest("#filter-btn")) {
        const user = await getUser();
        if (!user || user.expires <= Date.now()) {
          return void (loginModal.style.display = 'flex');
        }
      }
    });
    loginBtn.addEventListener("click", async () => {
      const username = document.getElementById("login-username").value;
      const password = document.getElementById("login-password").value;
      console.log("login-btn");
      if (!username || !password) {
        loginError.textContent = "请输入用户名和密码";
        return void (loginError.style.display = 'block');
      }
      try {
        const response = await fetch('https://zmapi.umyw.cn/login.php', {
          'method': "POST",
          'headers': {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          'body': "username=" + encodeURIComponent(username) + '&password=' + encodeURIComponent(password) + "&software_type=3"
        });
        if (!response.ok) {
          throw new Error("网络响应错误");
        }
        const data = await response.json();
        if (data.success) {
          console.log("show_daren_listen: data.show_daren_listen", data.user.show_daren_listen);
          chrome.storage.local.set({
            'xuanpin_user': JSON.stringify({
              'username': data.user.username,
              'id': data.user.id,
              'token': data.token,
              'show_daren_listen': data.user.show_daren_listen,
              'expires': Date.now() + 0x5265c00
            })
          }, function () {
            console.log("数据已保存到共享存储");
            chrome.tabs.query({}, function (tabs) {
              tabs.forEach(tab => {
                chrome.tabs.sendMessage(tab.id, {
                  'action': "dataUpdated"
                });
              });
            });
          });
          checkLoginStatus();
          loginModal.style.display = "none";
          loginError.style.display = "none";
        } else {
          loginError.textContent = data.message || "登录失败，请重试";
          loginError.style.display = 'block';
        }
      } catch (error) {
        console.error('登录请求失败:', error);
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