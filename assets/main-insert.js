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