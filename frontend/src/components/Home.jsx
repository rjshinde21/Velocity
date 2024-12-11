import React, { useEffect, useState } from 'react';
import star from "../assets/Home/star.png";
import HomeCards from "./HomeCards";
import { Link } from "react-router-dom";
import supabase from '../config/supabaseClient';

const Home = () => {
  const [user, setUser] = useState(null);

  // useEffect(() => {
  //   // Get initial session
  //   const initializeAuth = async () => {
  //     try {
  //       // Check if there's an active session
  //       const { data: { session } } = await supabase.auth.getSession();
  //       console.log("Current session:", session); // Log the session

  //       if (session) {
  //         const { data: { user }, error } = await supabase.auth.getUser();
  //         console.log("Raw user data:", user); // Log the raw user data

  //         if (user && !error) {
  //           const userData = {
  //             id: user.id,
  //             email: user.email,
  //             name: user.user_metadata?.full_name,
  //             avatar: user.user_metadata?.avatar_url
  //           };
  //           localStorage.setItem('user', JSON.stringify(userData));
  //           setUser(userData);
  //           console.log("Processed user data:", userData); // Log as an object
  //         } else if (error) {
  //           console.error("Error fetching user:", error);
  //         }
  //       } else {
  //         console.log("No active session found");
  //       }
  //     } catch (error) {
  //       console.error("Error in initializeAuth:", error);
  //     }
  //   };

  //   initializeAuth();

  //   const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
  //     console.log('Auth event:', event);
  //     console.log('Session in auth change:', session.user.email); // Log the session

  //     if (event === 'SIGNED_IN') {
  //       try {
  //         const { data: { user }, error } = await supabase.auth.getUser();
  //         console.log("Raw user data from auth change:", user); // Log the raw user data

  //         if (user && !error) {
  //           const userData = {
  //             id: user.id,
  //             email: user.email,
  //             name: user.user_metadata?.full_name,
  //             avatar: user.user_metadata?.avatar_url
  //           };
  //           localStorage.setItem('user', JSON.stringify(userData));
  //           setUser(userData);
  //           console.log("Processed user data from auth change:", userData); // Log as an object
  //         } else if (error) {
  //           console.error("Error fetching user in auth change:", error);
  //         }
  //       } catch (error) {
  //         console.error("Error in auth change handler:", error);
  //       }
  //     } else if (event === 'SIGNED_OUT') {
  //       localStorage.removeItem('user');
  //       setUser(null);
  //       console.log("User signed out, cleared data");
  //     }
  //   });

  //   // Cleanup subscription on unmount
  //   return () => {
  //     subscription.unsubscribe();
  //   };
  // }, []);

  const getUserData = () => {
    const userDataString = localStorage.getItem('user');
    console.log('User data string:', userDataString);
    if (userDataString) {
      try {
        const userData = JSON.parse(userDataString);
        console.log('Parsed user data:', userData);
        return userData;
      } catch (error) {
        console.error('Error parsing user data:', error);
        return null;
      }
    }
    return null;
  };


  return (
    <>
      <div className="absolute left-20 top-0 h-full w-[2px] bg-gradient-to-b from-[#1E1E1E] to-[#6ACFFF] opacity-20 hidden sm:block" />

      <div className="absolute right-20 top-0 h-full w-[2px] bg-gradient-to-b from-[#1E1E1E] to-[#6ACFFF] opacity-20 hidden sm:block" />


      <div className="relative flex items-center justify-center flex-col pt-52 bg-gradient-to-b from-transparent to-[#000000]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#008ACB_0%,_transparent_40%)] opacity-30 animate-gradient-move" />
        <div className="absolute inset-0 bg-black opacity-0 flex" />

        <div className="font-[Amenti] relative z-10 flex flex-col items-center justify-center">
          <h1 className="bg-gradient-text pt-10 text-3xl sm:text-6xl pb-4 text-center">
            Makes everyone a <br />
            <span className="block text-center">Prompt Expert</span>
          </h1>
          <p className="text-[#999999] font-[Inter] text-sm sm:text-lg">
            Redefine the way you generate AI-driven ideas
          </p>
          {/* <a href="https://chromewebstore.google.com/category/extensions?hl=en-US&utm_source=ext_sidebar" target="_blank">
            <button className="glowing-button flex items-center gap-2 sm:mt-12 mt-6">
              <span>Try Now with sample prompt</span>
              <img src={star} alt="Star" />
            </button>
          </a> */}
        </div>
        <HomeCards />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent via-[12%] bottom-0" />
      </div>
    </>
  );
};

export default Home;
