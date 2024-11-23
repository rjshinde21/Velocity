import React, { useState, useEffect } from "react";
import { ChevronDown } from "lucide-react";

const TermsConditions = () => {
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
          Terms & Conditions
        </h1>{" "}
        <p className="text-xl md:text-2xl text-center max-w-2xl">
          {" "}
          Understand the terms under which we provide our services and protect your interests.{" "}
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
            <h2 className="text-3xl font-bold mb-8">1. Acceptance of Terms</h2>{" "}
            {/* <p className="mb-6"> Last updated: August 23, 2024 </p>{" "} */}
            <p className="mb-6">
              {" "}
              Welcome to our Service. By accessing or using our platform, you agree to be bound by these Terms and Conditions. If you do not agree with any part of these terms, you must discontinue using the Service immediately.{" "}
            </p>{" "}
            {/* <p className="mb-6">
              {" "}
              We use Your Personal data to provide and improve the Service. By
              using the Service, You agree to the collection and use of
              information in accordance with this Privacy Policy.{" "}
            </p>{" "} */}
          </section>{" "}
          <section id="personal-data">
            {" "}
            <h2 className="text-3xl font-bold mt-12 mb-8">
              2. Use of the Service
            </h2>{" "}
            {/* <h3 className="text-2xl font-semibold mb-4">
              Types of Data Collected
            </h3>{" "}
            <h4 className="text-xl font-semibold mb-2">Personal Data</h4>{" "}
            <p className="mb-4">
              {" "}
              While using Our Service, We may ask You to provide Us with certain
              personally identifiable information that can be used to contact or
              identify You. Personally identifiable information may include, but
              is not limited to:{" "}
            </p>{" "} */}
            <ul className="list-disc list-inside mb-6">
              {" "}
              <li>The Service is provided for lawful purposes only.</li> <li>You are responsible for maintaining the confidentiality of your login credentials under your account.</li>{" "}
              <li>Any misuse or unauthorized access may result in the termination of your account.</li>{" "}
            </ul>{" "}
          </section>{" "}
          <section id="personal-data">
            {" "}
            <h2 className="text-3xl font-bold mt-12 mb-8">
              3. Intellectual Property
            </h2>{" "}
            {/* <h3 className="text-2xl font-semibold mb-4">
              Types of Data Collected
            </h3>{" "}
            <h4 className="text-xl font-semibold mb-2">Personal Data</h4>{" "}
            <p className="mb-4">
              {" "}
              While using Our Service, We may ask You to provide Us with certain
              personally identifiable information that can be used to contact or
              identify You. Personally identifiable information may include, but
              is not limited to:{" "}
            </p>{" "} */}
            <p>All content provided on the Service, including text, graphics, logos, and software, is the exclusive property of the Company or its licensors and is protected by intellectual property laws. Reproduction, distribution, or unauthorized use of any content is prohibited.</p>
          </section>{" "}
          <section id="personal-data">
            {" "}
            <h2 className="text-3xl font-bold mt-12 mb-8">
              4. Payment and Refund Policy
            </h2>{" "}
            {/* <h3 className="text-2xl font-semibold mb-4">
              Types of Data Collected
            </h3>{" "}
            <h4 className="text-xl font-semibold mb-2">Personal Data</h4>{" "}
            <p className="mb-4">
              {" "}
              While using Our Service, We may ask You to provide Us with certain
              personally identifiable information that can be used to contact or
              identify You. Personally identifiable information may include, but
              is not limited to:{" "}
            </p>{" "} */}
            <ul className="list-disc list-inside mb-6">
              {" "}
              <li>All payments made for the Service are final and <b>non-refundable.</b></li> <li>By completing a purchase, you acknowledge and accept this no-refund policy</li>{" "}
              <li>If a payment issue arises, please contact us to resolve it promptly.</li>{" "}
            </ul>
          </section>
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
              <li>By email: <a
                  href="info@toteminteractive.in"
                  className="text-[#008ACB] hover:underline"
                >
                  info@toteminteractive.in
                </a> </li>{" "}
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
export default TermsConditions;
