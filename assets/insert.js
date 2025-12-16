function addXMLRequestCallback(callback) {
  var originalSend;
  var i;
  if (XMLHttpRequest.callbacks) {
    XMLHttpRequest.callbacks.push(callback);
  } else {
    XMLHttpRequest.callbacks = [callback];
    originalSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function () {
      for (i = 0x0; i < XMLHttpRequest.callbacks.length; i++) {
        XMLHttpRequest.callbacks[i](this);
      }
      originalSend.apply(this, arguments);
    };
  }
}
function getUrlParams(url) {
  let params = {};
  url.replace(/[?&]+([^=&]+)=([^&]*)/gi, (_match, key, value) => {
    params[key] = function (encodedValue) {
      return decodeURIComponent(String(encodedValue).replace(/%(?![\da-f]{2})/gi, () => "%25").replace(/\+/g, '%20'));
    }(value);
  });
  return params;
}
addXMLRequestCallback(function (xhr) {
  xhr.addEventListener('load', function () {
    if (0x4 == xhr.readyState && 0xc8 == xhr.status && xhr.responseURL.indexOf("/pc/selection/decision/pack_detail") > -0x1) {
      if (0x0 == getUrlParams(xhr.responseURL).status) {
        return;
      }
      let {
        data: packData
      } = JSON.parse(xhr.response);
      console.log("【智能选品】onPackDetail postMessage", packData);
      window.postMessage({
        'action': "onPackDetail",
        'data': packData
      }, '*');
    }
  });
});