function addXMLRequestCallback(_0x2f014f) {
  var _0x35d793;
  var _0x30c45d;
  if (XMLHttpRequest.callbacks) {
    XMLHttpRequest.callbacks.push(_0x2f014f);
  } else {
    XMLHttpRequest.callbacks = [_0x2f014f];
    _0x35d793 = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function () {
      for (_0x30c45d = 0x0; _0x30c45d < XMLHttpRequest.callbacks.length; _0x30c45d++) {
        XMLHttpRequest.callbacks[_0x30c45d](this);
      }
      _0x35d793.apply(this, arguments);
    };
  }
}
function getUrlParams(_0x2c467c) {
  let _0x1a7cc7 = {};
  _0x2c467c.replace(/[?&]+([^=&]+)=([^&]*)/gi, (_0x293e6e, _0xd9b884, _0x1096c4) => {
    _0x1a7cc7[_0xd9b884] = function (_0x167bcf) {
      return decodeURIComponent(String(_0x167bcf).replace(/%(?![\da-f]{2})/gi, () => "%25").replace(/\+/g, '%20'));
    }(_0x1096c4);
  });
  return _0x1a7cc7;
}
addXMLRequestCallback(function (_0x59ef8d) {
  _0x59ef8d.addEventListener('load', function () {
    if (0x4 == _0x59ef8d.readyState && 0xc8 == _0x59ef8d.status && _0x59ef8d.responseURL.indexOf("/pc/selection/decision/pack_detail") > -0x1) {
      if (0x0 == getUrlParams(_0x59ef8d.responseURL).status) {
        return;
      }
      let {
        data: _0x4fc931
      } = JSON.parse(_0x59ef8d.response);
      console.log("【智能选品】onPackDetail postMessage", _0x4fc931);
      window.postMessage({
        'action': "onPackDetail",
        'data': _0x4fc931
      }, '*');
    }
  });
});