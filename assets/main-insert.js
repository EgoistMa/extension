function addXMLRequestCallback(_0x5743de) {
  var _0x398b7f;
  var _0x6296f5;
  if (XMLHttpRequest.callbacks) {
    XMLHttpRequest.callbacks.push(_0x5743de);
  } else {
    XMLHttpRequest.callbacks = [_0x5743de];
    _0x398b7f = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function () {
      for (_0x6296f5 = 0x0; _0x6296f5 < XMLHttpRequest.callbacks.length; _0x6296f5++) {
        XMLHttpRequest.callbacks[_0x6296f5](this);
      }
      _0x398b7f.apply(this, arguments);
    };
  }
}
function getUrlParams(_0x4a3a6b) {
  let _0x7c23c = {};
  _0x4a3a6b.replace(/[?&]+([^=&]+)=([^&]*)/gi, (_0x506d45, _0x3f50c0, _0x3bb14a) => {
    _0x7c23c[_0x3f50c0] = function (_0xe0d08) {
      return decodeURIComponent(String(_0xe0d08).replace(/%(?![\da-f]{2})/gi, () => "%25").replace(/\+/g, '%20'));
    }(_0x3bb14a);
  });
  return _0x7c23c;
}