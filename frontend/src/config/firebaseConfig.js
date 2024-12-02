import { initializeApp } from 'firebase/app';
import { getAuth,setPersistence,browserLocalPersistence } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyCCymRQ4dHwaJ4yWg6Kf-_HdnVRdu6CI2Q",
  authDomain: "velocity-totem.firebaseapp.com",
  projectId: "velocity-totem",
  storageBucket: "velocity-totem.firebasestorage.app",
  messagingSenderId: "320011102570",
  appId: "1:320011102570:web:7e3554076f2d2878ff1d13",
};

const app = initializeApp(firebaseConfig);

// Configure auth persistence
const auth = getAuth(app);
await setPersistence(auth, browserLocalPersistence)
  .then(() => console.log('Firebase persistence initialized'))
  .catch(console.error);

auth.useDeviceLanguage();
auth.settings = {
  appVerificationDisabledForTesting: true // Only for development
};

export { auth };

