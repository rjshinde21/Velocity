import React from "react";
import velocitylogo from "../assets/velocitylogo.png";
import { FaInstagram, FaLinkedin, FaYoutube } from "react-icons/fa";

const Footer = () => {
  return (
    <footer class="bg-black w-full mt-6 sm:mt-16">
      <div class="w-full p-8 sm:p-16 py-6 lg:py-8">
        <div class="md:flex md:justify-between">
          <div class="mb-6 md:mb-0">
            <a href="#" class="flex items-center mb">
              <img
                src={velocitylogo}
                class="h-8 sm:h-12 me-3"
                alt="Velocity Logo"
              />
            </a>
            <p class="self-center text-xl sm:text-2xl font-semibold whitespace-nowrap font-[Inter] my-4 bg-gradient-text">
              We grow up your business <br /> with personal AI manager.
            </p>
            <p className="text-md bg-gradient-text mb-8 sm:mb-0">
              Velocity, 2024
            </p>
          </div>
          <div class="grid grid-cols-2 gap-8 sm:gap-6 sm:grid-cols-3">
            <div>
              <h2 class="mb-6 text-sm font-semibold text-primary uppercase">
                Resources
              </h2>
              <ul class="text-gray-500 dark:text-gray-400 font-medium">
                <li class="mb-4">
                  <a href="#" class="hover:underline hover:text-gray-100">
                    Velocity
                  </a>
                </li>
                <li>
                  <a
                    href="https://tailwindcss.com/"
                    class="hover:underline hover:text-gray-100"
                  >
                    Tailwind CSS
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h2 class="mb-6 text-sm font-semibold text-primary uppercase">
                Follow us
              </h2>
              <ul class="text-gray-500 dark:text-gray-400 font-medium">
                <li class="mb-4">
                  <a
                    href="https://www.instagram.com/totem.interactive?igsh=MXRscW14NDNwOGdtbA=="
                    class="hover:underline hover:text-gray-100"
                  >
                    Instagram
                  </a>
                </li>
                <li class="mb-4">
                  <a
                    href="https://www.linkedin.com/company/totem-interactive/posts/?feedView=all"
                    class="hover:underline hover:text-gray-100"
                  >
                    LinkedIn
                  </a>
                </li>
                <li>
                  <a
                    href="https://youtube.com/@toteminteractive?si=b7fqsL9zkOS4QQmn"
                    class="hover:underline hover:text-gray-100"
                  >
                    YouTube
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h2 class="mb-6 text-sm font-semibold text-primary uppercase">
                Legal
              </h2>
              <ul class="text-gray-500 dark:text-gray-400 font-medium">
                <li class="mb-4">
                  <a href="#" class="hover:underline hover:text-gray-100">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="#" class="hover:underline hover:text-gray-100">
                    Terms &amp; Conditions
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <hr class="my-6 border-gray-200 sm:mx-auto dark:border-gray-700 lg:my-8" />
        <div class="sm:flex sm:items-center sm:justify-between">
          <span class="text-sm text-gray-500 sm:text-center dark:text-gray-400">
            © 2024{" "}
            <a href="#" class="hover:underline">
              Velocity™
            </a>
            . All Rights Reserved.
          </span>
          <div className="flex space-x-4 mt-4">
            {" "}
            <a
              href="https://www.instagram.com/totem.interactive?igsh=MXRscW14NDNwOGdtbA=="
              className="text-gray-500 hover:text-gray-100 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              {" "}
              <FaInstagram className="h-6 w-6" />{" "}
            </a>{" "}
            <a
              href="https://www.linkedin.com/company/totem-interactive/posts/?feedView=all"
              className="text-gray-500 hover:text-gray-100 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              {" "}
              <FaLinkedin className="h-6 w-6" />{" "}
            </a>{" "}
            <a
              href="https://youtube.com/@toteminteractive?si=b7fqsL9zkOS4QQmn"
              className="text-gray-500 hover:text-gray-100 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              {" "}
              <FaYoutube className="h-6 w-6" />{" "}
            </a>{" "}
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
