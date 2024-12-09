// import React from "react";
// import velocitylogo from "../assets/velocitylogo.png";
// import { FaInstagram, FaLinkedin, FaYoutube } from "react-icons/fa";
// import { Link } from "react-router-dom";

// const Footer = () => {
//   return (
//     <footer class="bg-black w-full mt-6 sm:mt-16">
//       <div class="w-full p-8 sm:p-16 py-6 lg:py-8">
//         <div class="md:flex md:justify-between">
//           <div class="mb-6 md:mb-0">
//             <a href="#" class="flex items-center mb">
//               <img
//                 src={velocitylogo}
//                 class="h-8 sm:h-12 me-3"
//                 alt="Velocity Logo"
//               />
//             </a>
//             <p class="self-center text-2xl font-semibold whitespace-nowrap font-[Inter] my-4 bg-gradient-text">
//             Transform ideas into  <br /> impactful prompts with ease!
//             </p>
//             <p className="text-md bg-gradient-text mb-8 sm:mb-0">
//               Velocity, 2024
//             </p>
//           </div>
//           <div class="grid grid-cols-2 gap-8 sm:gap-6 sm:grid-cols-3">
//             <div>
//               <h2 class="mb-6 text-sm font-semibold text-primary uppercase">
//                 Resources
//               </h2>
//               <ul class="text-gray-500 dark:text-gray-400 font-medium">
//                 <li class="mb-4">
//                   <a href="#" class="hover:underline hover:text-gray-100">
//                     Velocity
//                   </a>
//                 </li>
//                 {/* <li>
//                   <a
//                     href="https://tailwindcss.com/"
//                     class="hover:underline hover:text-gray-100"
//                   >
//                     Tailwind CSS
//                   </a>
//                 </li> */}
//               </ul>
//             </div>
//             <div>
//               <h2 class="mb-6 text-sm font-semibold text-primary uppercase">
//                 Follow us
//               </h2>
//               <ul class="text-gray-500 dark:text-gray-400 font-medium">
//                 <li class="mb-4">
//                   <a
//                     href="https://www.instagram.com/totem.interactive?igsh=MXRscW14NDNwOGdtbA=="
//                     class="hover:underline hover:text-gray-100"
//                   >
//                     Instagram
//                   </a>
//                 </li>
//                 <li class="mb-4">
//                   <a
//                     href="https://www.linkedin.com/company/totem-interactive/posts/?feedView=all"
//                     class="hover:underline hover:text-gray-100"
//                   >
//                     LinkedIn
//                   </a>
//                 </li>
//                 <li>
//                   <a
//                     href="https://youtube.com/@toteminteractive?si=b7fqsL9zkOS4QQmn"
//                     class="hover:underline hover:text-gray-100"
//                   >
//                     YouTube
//                   </a>
//                 </li>
//               </ul>
//             </div>
//             <div>
//               <h2 class="mb-6 text-sm font-semibold text-primary uppercase">
//                 Legal
//               </h2>
//               <ul class="text-gray-500 dark:text-gray-400 font-medium">
//                 <li class="mb-4" onClick={()=>window.scrollTo({top: 0, behavior: 'smooth'})}>
//                   <Link to="/privacypolicy" class="hover:underline hover:text-gray-100">
//                     Privacy Policy
//                   </Link>
//                 </li>
//                 <li onClick={()=>window.scrollTo({top: 0, behavior: 'smooth'})}>
//                   <Link to="/terms-and-conditions" class="hover:underline hover:text-gray-100">
//                     Terms &amp; Conditions
//                   </Link>
//                 </li>
//               </ul>
//             </div>
//           </div>
//         </div>
//         <hr class="my-6 border-gray-200 sm:mx-auto dark:border-gray-700 lg:my-8" />
//         <div class="sm:flex sm:items-center sm:justify-between">
//           <span class="text-sm text-gray-500 sm:text-center dark:text-gray-400">
//             © 2024{" "}
//             <a href="#" class="hover:underline">
//               Velocity™
//             </a>
//             . All Rights Reserved.
//           </span>
//           <div className="flex space-x-4 mt-4">
//             {" "}
//             <a
//               href="https://www.instagram.com/totem.interactive?igsh=MXRscW14NDNwOGdtbA=="
//               className="text-gray-500 hover:text-gray-100 transition-colors"
//               target="_blank"
//               rel="noopener noreferrer"
//             >
//               {" "}
//               <FaInstagram className="h-6 w-6" />{" "}
//             </a>{" "}
//             <a
//               href="https://www.linkedin.com/company/totem-interactive/posts/?feedView=all"
//               className="text-gray-500 hover:text-gray-100 transition-colors"
//               target="_blank"
//               rel="noopener noreferrer"
//             >
//               {" "}
//               <FaLinkedin className="h-6 w-6" />{" "}
//             </a>{" "}
//             <a
//               href="https://youtube.com/@toteminteractive?si=b7fqsL9zkOS4QQmn"
//               className="text-gray-500 hover:text-gray-100 transition-colors"
//               target="_blank"
//               rel="noopener noreferrer"
//             >
//               {" "}
//               <FaYoutube className="h-6 w-6" />{" "}
//             </a>{" "}
//           </div>
//         </div>
//       </div>
//     </footer>
//   );
// };

// export default Footer;


import React from 'react';
import { Instagram, Linkedin } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-black text-gray-400 py-8 sm:py-16">
      <div className="container mx-auto px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          {/* Main content */}
          <div className="mb-8 sm:mb-12 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 sm:gap-8">
            <div className="flex flex-col gap-4 items-start">
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold leading-tight">
                GENERATE SMARTER<br />
                PROMPTS. FASTER.
              </h1>
              <p className="text-sm sm:text-base text-gray-700 leading-relaxed">
                Transform your ideas with precision and creativity
              </p>
            </div>
            <button className="bg-black text-white px-4 sm:px-6 py-3 sm:py-4 rounded-full border border-gray-700 hover:bg-gray-900 transition-colors whitespace-nowrap">
              Get Started
            </button>
          </div>

          {/* Designer credit and logo section */}
          <div className="space-y-6 sm:space-y-0">
            <p className="text-xs sm:text-sm text-center sm:text-left">
              Designed by TOTEM INTERACTIVE
            </p>

            {/* Logo and social icons */}
            <div className="relative flex flex-col sm:flex-row items-center sm:items-center justify-between gap-4 sm:gap-6 px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
  {/* VELOCITY Text */}
  <div className="font-[Amenti] text-[2.5rem] sm:text-[4rem] md:text-[6rem] lg:text-[8rem] xl:text-[10rem] 
                  font-bold tracking-wider leading-none text-center sm:text-left
                  transform transition-transform duration-300">
    VELOCITY
  </div>
  
  {/* Social Icons */}
  <div className="absolute bottom-8 sm:bottom-12 lg:bottom-16 
                right-2 sm:right-4 lg:right-6 
                flex gap-2 sm:gap-3 lg:gap-4">
    <a
      href="https://www.instagram.com/totem.interactive?igsh=MXRscW14NDNwOGdtbA=="
      className="hover:text-white transition-colors p-1 sm:p-1.5"
      target="_blank"
      rel="noopener noreferrer"
    >
      <Instagram className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
    </a>
    <a
      href="https://www.linkedin.com/company/totem-interactive/posts/?feedView=all"
      className="hover:text-white transition-colors p-1 sm:p-1.5"
      target="_blank"
      rel="noopener noreferrer"
    >
      <Linkedin className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
    </a>
  </div>
</div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

