import React, { useState, useEffect } from "react";
import { ChevronDown } from "lucide-react";

const PrivacyPolicy = () => {
  const [navOpen, setNavOpen] = useState(false);
  const [activeSection, setActiveSection] = useState(null);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
      const sections = document.querySelectorAll("h2");
      let currentSection = null;
      sections.forEach((section) => {
        const sectionTop = section.offsetTop - 100;
        if (window.scrollY >= sectionTop) {
          currentSection = section.textContent;
        }
      });
      setActiveSection(currentSection);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);
  const scrollToContent = () => {
    window.scrollTo({ top: window.innerHeight, behavior: "smooth" });
  };
  return (
    <div className="bg-[#000000] text-white min-h-screen">
      {" "}
      {/* Hero Section */}{" "}
      <div className="h-screen flex flex-col justify-center items-center p-8 relative">
        {" "}
        <h1 className="text-4xl md:text-6xl font-bold mb-4">
          Privacy Policy
        </h1>{" "}
        <p className="text-xl md:text-2xl text-center max-w-2xl">
          {" "}
          Your privacy is important to us. Learn how we collect, use, and
          protect your information.{" "}
        </p>{" "}
        <button
          onClick={scrollToContent}
          className="mt-12 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full p-2 transition-all duration-300 ease-in-out animate-bounce"
        >
          {" "}
          <ChevronDown size={24} />{" "}
        </button>{" "}
      </div>{" "}
      {/* Content Section */}{" "}
      <div className="container mx-auto px-4 py-16">
        {" "}
        <div className="max-w-3xl mx-auto">
          {" "}
          <section id="introduction">
            {" "}
            <h2 className="text-3xl font-bold mb-8">1. Introduction</h2>{" "}
            <p className="mb-6"> Last updated: August 23, 2024 </p>{" "}
            <p className="mb-6">
              {" "}
              This Privacy Policy describes Our policies and procedures on the
              collection, use and disclosure of Your information when You use
              the Service and tells You about Your privacy rights and how the
              law protects You.{" "}
            </p>{" "}
            <p className="mb-6">
              {" "}
              We use Your Personal data to provide and improve the Service. By
              using the Service, You agree to the collection and use of
              information in accordance with this Privacy Policy.{" "}
            </p>{" "}
          </section>{" "}
          <section id="personal-data">
            {" "}
            <h2 className="text-3xl font-bold mt-12 mb-8">
              2. Collecting and Using Your Personal Data
            </h2>{" "}
            <h3 className="text-2xl font-semibold mb-4">
              Types of Data Collected
            </h3>{" "}
            <h4 className="text-xl font-semibold mb-2">Personal Data</h4>{" "}
            <p className="mb-4">
              {" "}
              While using Our Service, We may ask You to provide Us with certain
              personally identifiable information that can be used to contact or
              identify You. Personally identifiable information may include, but
              is not limited to:{" "}
            </p>{" "}
            <ul className="list-disc list-inside mb-6">
              {" "}
              <li>Email address</li> <li>First name and last name</li>{" "}
              <li>Phone number</li> <li>Usage Data</li>{" "}
            </ul>{" "}
          </section>{" "}
          <section id="contact">
            {" "}
            <h2 className="text-3xl font-bold mt-12 mb-8">Contact Us</h2>{" "}
            <p className="mb-6">
              {" "}
              If you have any questions about this Privacy Policy, You can
              contact us:{" "}
            </p>{" "}
            <ul className="list-disc list-inside mb-6">
              {" "}
              <li>By email: info@toteminteractive.in</li>{" "}
              <li>
                By visiting this page on our website:{" "}
                <a
                  href="https://toteminteractive.in/"
                  className="text-[#008ACB] hover:underline"
                >
                  https://toteminteractive.in/
                </a>
              </li>{" "}
            </ul>{" "}
          </section>{" "}
        </div>{" "}
      </div>{" "}
    </div>
  );
};
export default PrivacyPolicy;
