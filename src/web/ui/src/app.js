import React from 'react';
import { FooterBanner, HeaderNavigationBar } from './components/layout';
import './style/style.css';

function App() {
  return (
    <div className="page-container">
      <div className="content-wrap">
        <HeaderNavigationBar brand="PANIC" />
      </div>
      <FooterBanner
        text="Developed by Simply VC"
        href="https://simply-vc.com.mt"
      />
    </div>
  );
}

export default App;
