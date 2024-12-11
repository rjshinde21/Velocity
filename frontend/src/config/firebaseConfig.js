import { initializeApp } from 'firebase/app';
import { getAuth,setPersistence,browserLocalPersistence } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyC7UKw2L3gmPrv67Q_9hdyc2ClNiWuDZsg",
  authDomain: "think-velocity.firebaseapp.com",
  projectId: "think-velocity",
  storageBucket: "think-velocity.firebasestorage.app",
  messagingSenderId: "685789956754",
  appId: "1:685789956754:web:d951bff0821fbe2df4744b",
};

const app = initializeApp(firebaseConfig);

// Configure auth persistence
const auth = getAuth(app);
setPersistence(auth, browserLocalPersistence)
  .then(() => console.log('Firebase persistence initialized'))
  .catch((error) => console.error('Firebase initialization error:', error));

  export { auth };