import React from 'react';
import Navbar from '../components/Navbar';
import AmbientBackground from '../components/AmbientBackground';
import CursorGlow from '../components/CursorGlow';
import HeroSection from '../components/HeroSection';
import MarqueeStrip from '../components/MarqueeStrip';
import FeaturesSection from '../components/FeaturesSection';
import HowItWorksSection from '../components/HowItWorksSection';
import CTASection from '../components/CTASection';
import Footer from '../components/Footer';

const LandingPage = () => {
  return (
    <>
      <AmbientBackground />
      <CursorGlow />
      <Navbar />
      <main>
        <HeroSection />
        <MarqueeStrip />
        <FeaturesSection />
        <HowItWorksSection />
        <CTASection />
      </main>
      <Footer />
    </>
  );
};

export default LandingPage;
