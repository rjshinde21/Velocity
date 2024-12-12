// mixpanel-config.js
const mixpanel = window.mixpanel;

mixpanel.init('48a67766d0bb1b3399a4f956da9c52da', {
    debug: true,
    track_pageview: true
});

export default mixpanel;