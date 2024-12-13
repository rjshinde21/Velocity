let mixpanel;

// Initialize Mixpanel in extension
const initMixpanel = () => {
  // Load Mixpanel script
  (function(c,a){window.mixpanel=a;var b,d,h,e;b=c.createElement("script");
  b.type="text/javascript";b.async=!0;b.src=("https:"===c.location.protocol?"https:":"http:")+
  '//cdn.mxpnl.com/libs/mixpanel-2-latest.min.js';d=c.getElementsByTagName("script")[0];
  d.parentNode.insertBefore(b,d);a._i=[];a.init=function(b,c,f){function d(b,h){
  var a=h.split(".");2==a.length&&(b=b[a[0]],h=a[1]);b[h]=function(){b.push([h].concat(
  Array.prototype.slice.call(arguments,0)))}}var g=a;"undefined"!==typeof f?g=a[f]=[]:
  f="mixpanel";g.people=g.people||[];h=['disable','track','track_pageview','track_links',
  'track_forms','register','register_once','unregister','identify','alias','name_tag',
  'set_config','people.set','people.increment'];for(e=0;e<h.length;e++)d(g,h[e]);
  a._i.push([b,c,f])};a.__SV=1.2;})(document,window.mixpanel||[]);

  mixpanel.init('48a67766d0bb1b3399a4f956da9c52da', {
    debug: false,
    track_pageview: true,
    persistence: 'localStorage'
  });
};
const ExtensionAnalytics = {
    init: () => {
      initMixpanel();
    },
  
    track: (eventName, properties = {}) => {
      // Add extension-specific properties
      const eventProps = {
        ...properties,
        platform: 'extension',
        version: chrome.runtime.getManifest().version
      };
      mixpanel.track(eventName, eventProps);
    },
  
    identify: (userId) => {
      mixpanel.identify(userId);
    }
  };
  
  export default ExtensionAnalytics;
  
  