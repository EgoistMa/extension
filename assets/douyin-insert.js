window.addEventListener('message', function (event) {
  const action = event.data.action;
  const actionRes = event.data.actionRes;
  const trigger = event.data.trigger;
  if (action && 'DBDY_ACCQURE2' === action) {
    let url = event.data.url;
    let options = event.data.options;
    fetch(url, options).then(response => response.json()).then(result => {
      window.postMessage({
        'action': actionRes,
        'trigger': trigger,
        'res': result
      }, '*');
    })["catch"](error => {
      console.error(error);
    });
  }
}, false);
(function () {
  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method, url, ...args) {
    this._url = url;
    return originalOpen.apply(this, [method, url, ...args]);
  };
  XMLHttpRequest.prototype.send = function (body) {
    this.addEventListener("readystatechange", function () {
      console.log('xml监听到===========>', this._url);
      if (0x4 === this.readyState && 0xc8 === this.status) {
        try {
          if (this._url && this._url.indexOf('aweme/v1/web/general/search/single') > -0x1) {
            console.log("搜索加载监听到===========>", this._url);
            (function (responseText) {
              let data = JSON.parse(responseText);
              if (data) {
                window.postMessage({
                  'action': "DBDY_SEARCH_ACCQURE_RES",
                  'sources': 'aweme/v1/web/general/search/single',
                  'trigger': 'auto',
                  'res': data
                }, '*');
              }
            })(this.responseText);
          }
          if (this._url && this._url.indexOf("aweme/v1/web/aweme/detail") > -0x1) {
            console.log('详情加载监听到===========>', this._url);
            (function (responseText) {
              let data = JSON.parse(responseText);
              if (data) {
                window.postMessage({
                  'action': "DBDY_INFO_ACCQURE_RES",
                  'sources': 'aweme/v1/web/general/search/single',
                  'trigger': "auto",
                  'res': data
                }, '*');
              }
            })(this.responseText);
          }
        } catch (error) {
          console.error("Error modifying response:", error);
        }
      }
    });
    return originalSend.apply(this, [body]);
  };
  const originalFetch = window.fetch;
  window.fetch = async function (url, options = {}) {
    const response = await originalFetch.apply(this, [url, options]);
    const clonedResponse = response.clone();
    try {
      if ("string" == typeof url && url.indexOf('aweme/v1/web/general/search/stream') > -0x1) {
        console.log("搜索首次加载监听到===========>", url);
        const text = await clonedResponse.text();
        window.postMessage({
          'action': "DBDY_SEARCH_FIRST_ACCQURE_RES",
          'sources': "fetch:aweme/v1/web/general/search/stream",
          'trigger': 'auto',
          'res': text
        }, '*');
      }
    } catch (error) {
      console.error("Fetch处理错误:", error);
    }
    return response;
  };
})();