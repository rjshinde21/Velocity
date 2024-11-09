import './App.css'
import Navbar from './components/Navbar'
import Home from './components/Home'
import Card from './components/Card'
import FreeTrial from './components/FreeTrial'
import Pricing from './components/PricingSection/Pricing'
import Carousel from './components/Carousel'
import Login from './components/Login'
import { useState } from 'react'
import Register from './components/Register'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

function App() {
  const [showLogin, setShowLogin] = useState(false);

  const handleClick = () => {
    setShowLogin(prev => !prev);
  };

  return (
    <Router>
      <main className='bg-primary overflow-hidden'>
        <Navbar handleClick={handleClick} />
        <Routes>
          <Route path="/" element={
            <>
              <Home />
              {showLogin && <Register />}
              <FreeTrial />
              <Pricing />
              <Carousel speed={20000} />
            </>
          } />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </main>
    </Router>
  )
}

export default App