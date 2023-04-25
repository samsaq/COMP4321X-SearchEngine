// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries
// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional

// Lazy load Firebase Analytics library
/**
 * @type {import("@firebase/analytics").Analytics}
 */
let analytics;

async function getAnalytics() {
  if (!analytics) {
    const { getAnalytics } = await import('firebase/analytics');
    analytics = getAnalytics(app);
  }
  return analytics;
}

const firebaseConfig = {
    apiKey: "AIzaSyBwszMK55_f_pJ3VQispij78HSFooUwdlQ",
    authDomain: "search-engine-website-d8d1b.firebaseapp.com",
    projectId: "search-engine-website-d8d1b",
    storageBucket: "search-engine-website-d8d1b.appspot.com",
    messagingSenderId: "436631317354",
    appId: "1:436631317354:web:75a8bea1d6d99525ed1313",
    measurementId: "G-J5VE9262E2"
};
// Initialize Firebase
const app = initializeApp(firebaseConfig);
export {app, getAnalytics};