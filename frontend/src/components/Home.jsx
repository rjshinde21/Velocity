import React, { useEffect, useState } from 'react';
import { useCallback } from 'react';
import Particles from "react-tsparticles";
import { loadFull } from "tsparticles";
import star from "../assets/Home/star.png";
import HomeCards from "./HomeCards";
import { Link } from "react-router-dom";
import supabase from '../config/supabaseClient';
import Analytics from '../config/analytics';

const Home = () => {3
  useEffect(() => {
    Analytics.track('Page View', {
      page: 'Home'
    });
  }, []);

  const [user, setUser] = useState(null);

  const particlesInit = useCallback(async (engine) => {
    console.log("Initializing particles");
    try {
      await loadFull(engine);
    } catch (error) {
      console.error("Error loading particles:", error);
    }
  }, []);

  const particlesLoaded = useCallback(async (container) => {
    console.log("Particles loaded:", container);
  }, []);

  const particlesConfig = {
    autoPlay: true,
    background: {
      color: {
        value: "#000000"
      },
      opacity: 1
    },
    fullScreen: {
      enable: false, // Disable full-screen effect
    },
    detectRetina: true,
    fpsLimit: 120,
    particles: {
      color: {
        value: "#ffffff"
      },
      links: {
        color: "#ffffff",
        distance: 150,
        enable: true,
        opacity: 0.2,
        width: 1
      },
      move: {
        direction: "none",
        enable: true,
        outModes: {
          default: "bounce"
        },
        random: true,
        speed: 1,
        straight: false
      },
      number: {
        density: {
          enable: true,
          area: 800
        },
        value: 80
      },
      opacity: {
        value: 0.3
      },
      shape: {
        type: "circle"
      },
      size: {
        value: { min: 1, max: 3 }
      }
    }
  };

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
    <div className="relative min-h-screen">
      {/* Particles container in the background */}
      <div className="absolute inset-0 z-0">
        <Particles
          id="tsparticles"
          init={particlesInit}
          loaded={particlesLoaded}
          options={particlesConfig}
          className="w-full h-full" // Full width and height
        />
      </div>

      <div className="absolute left-20 top-0 h-full w-[2px] bg-gradient-to-b from-[#1E1E1E] to-[#6ACFFF] opacity-20 hidden sm:block z-10" />
      <div className="absolute right-20 top-0 h-full w-[2px] bg-gradient-to-b from-[#1E1E1E] to-[#6ACFFF] opacity-20 hidden sm:block z-10" />

      {/* Content layer above particles */}
      <div className="relative flex items-center justify-center flex-col pt-40 lg:pt-56 z-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#008ACB_0%,_transparent_40%)] opacity-30 animate-gradient-move" />
        
        <div className="font-[Amenti] relative z-10 flex flex-col items-center justify-center">
          <h1 className="bg-gradient-text pt-10 text-4xl sm:text-6xl pb-4 text-center">
            Makes everyone a <br />
            <span className="block text-center">Prompt Expert</span>
          </h1>
          <p className="text-[#999999] font-[Inter] text-base sm:text-xl">
            Redefine the way you generate AI-driven ideas
          </p>
        </div>

        <HomeCards />
        
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent via-[12%] bottom-0" />
      </div>
    </div>
  );
};

export default Home;
