window.addEventListener('message', function (_0x5e5c05) {
  const _0x5af16c = _0x5e5c05.data.action;
  const _0x2ba504 = _0x5e5c05.data.actionRes;
  const _0x35d797 = _0x5e5c05.data.trigger;
  if (_0x5af16c && 'DBDY_ACCQURE2' === _0x5af16c) {
    let _0x4d85c1 = _0x5e5c05.data.url;
    let _0x51cf0b = _0x5e5c05.data.options;
    fetch(_0x4d85c1, _0x51cf0b).then(_0xd7f4f9 => _0xd7f4f9.json()).then(_0x4551f1 => {
      window.postMessage({
        'action': _0x2ba504,
        'trigger': _0x35d797,
        'res': _0x4551f1
      }, '*');
    })["catch"](_0xc2f3b6 => {
      console.error(_0xc2f3b6);
    });
  }
}, false);
(function () {
  const _0x4202c0 = XMLHttpRequest.prototype.open;
  const _0x24acdc = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (_0x2aa08e, _0x54f39e, ..._0x3004a7) {
    this._url = _0x54f39e;
    return _0x4202c0.apply(this, [_0x2aa08e, _0x54f39e, ..._0x3004a7]);
  };
  XMLHttpRequest.prototype.send = function (_0x29b1c2) {
    this.addEventListener("readystatechange", function () {
      console.log('xml监听到===========>', this._url);
      if (0x4 === this.readyState && 0xc8 === this.status) {
        try {
          if (this._url && this._url.indexOf('aweme/v1/web/general/search/single') > -0x1) {
            console.log("搜索加载监听到===========>", this._url);
            (function (_0x185aee) {
              let _0x55b891 = JSON.parse(_0x185aee);
              if (_0x55b891) {
                window.postMessage({
                  'action': "DBDY_SEARCH_ACCQURE_RES",
                  'sources': 'aweme/v1/web/general/search/single',
                  'trigger': 'auto',
                  'res': _0x55b891
                }, '*');
              }
            })(this.responseText);
          }
          if (this._url && this._url.indexOf("aweme/v1/web/aweme/detail") > -0x1) {
            console.log('详情加载监听到===========>', this._url);
            (function (_0x2257aa) {
              let _0x21b02d = JSON.parse(_0x2257aa);
              if (_0x21b02d) {
                window.postMessage({
                  'action': "DBDY_INFO_ACCQURE_RES",
                  'sources': 'aweme/v1/web/general/search/single',
                  'trigger': "auto",
                  'res': _0x21b02d
                }, '*');
              }
            })(this.responseText);
          }
        } catch (_0x4ccb36) {
          console.error("Error modifying response:", _0x4ccb36);
        }
      }
    });
    return _0x24acdc.apply(this, [_0x29b1c2]);
  };
  const _0x4daf82 = window.fetch;
  window.fetch = async function (_0x9aabea, _0xcb6c9c = {}) {
    const _0x1d9b0f = await _0x4daf82.apply(this, [_0x9aabea, _0xcb6c9c]);
    const _0x439b38 = _0x1d9b0f.clone();
    try {
      if ("string" == typeof _0x9aabea && _0x9aabea.indexOf('aweme/v1/web/general/search/stream') > -0x1) {
        console.log("搜索首次加载监听到===========>", _0x9aabea);
        const _0x5c02b2 = await _0x439b38.text();
        window.postMessage({
          'action': "DBDY_SEARCH_FIRST_ACCQURE_RES",
          'sources': "fetch:aweme/v1/web/general/search/stream",
          'trigger': 'auto',
          'res': _0x5c02b2
        }, '*');
      }
    } catch (_0x4228de) {
      console.error("Fetch处理错误:", _0x4228de);
    }
    return _0x1d9b0f;
  };
})();