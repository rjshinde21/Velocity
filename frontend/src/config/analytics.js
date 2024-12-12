// config/analytics.js - Create a configuration file for your Mixpanel instance
import mixpanel from 'mixpanel-browser';

const MIXPANEL_TOKEN = '48a67766d0bb1b3399a4f956da9c52da';

// Initialize Mixpanel
mixpanel.init(MIXPANEL_TOKEN, {
  debug: process.env.NODE_ENV !== 'production',
  track_pageview: true,
  persistence: 'localStorage'
});
const Analytics = {
    identify: (id) => {
      mixpanel.identify(id);
    },
  
    alias: (id) => {
      mixpanel.alias(id);
    },
  
    track: (name, props) => {
      mixpanel.track(name, props);
    },
  
    people: {
      set: (props) => {
        mixpanel.people.set(props);
      },
    },
  
    setUserProperties: (props) => {
      mixpanel.people.set(props);
    }
  };
  
  export default Analytics;
