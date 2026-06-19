import { useEffect } from "react";
import Navbar from "../components/Navbar";
import Hero from "../components/Hero";
import TrustBar from "../components/TrustBar";
import DarkPanel from "../components/DarkPanel";
import Features from "../components/Features";
import Scenarios from "../components/Scenarios";
import Scoring from "../components/Scoring";
import RiskDashboard from "../components/RiskDashboard";
import WorkflowDashboard from "../components/WorkflowDashboard";
import TerminalTrace from "../components/TerminalTrace";
import Faq from "../components/Faq";
import Footer from "../components/Footer";

export default function Landing() {
  useEffect(() => {
    const revealEls = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.08, rootMargin: "0px 0px -8% 0px" },
      );

      revealEls.forEach((el) => observer.observe(el));
      return () => observer.disconnect();
    }
    revealEls.forEach((el) => el.classList.add("is-visible"));
    return undefined;
  }, []);

  return (
    <>
      <Navbar />
      <main id="main">
        <Hero />
        <TrustBar />
        <DarkPanel />
        <Features />
        <Scenarios />
        <Scoring />
        <RiskDashboard />
        <WorkflowDashboard />
        <TerminalTrace />
        <Faq />
      </main>
      <Footer />
    </>
  );
}
