import React, { useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Model } from './Model'; 
import '../../index.css'

function ThreeDLogo() {

  const [fov, setFov] = useState(90);

  useEffect(() => {
    const handleResize = () => {
      setFov(window.innerWidth < 768 ? 90 : 50);
    };
    window.addEventListener('resize', handleResize);
    handleResize(); 
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <Canvas
      shadows
      camera={{ position: [0, 0, 5], fov: fov }}
      style={{ height: '100vh' }}
    >
      {/* Lighting */}
      <ambientLight intensity={1} />
      <directionalLight position={[10, 10, 10]} intensity={5} castShadow />
      
      {/* The Model */}
      <Model scale={1.5} position={[0, 0, 0]} />

      {/* Controls to move around */}
      <OrbitControls enabled={false}/>
    </Canvas>
  );
}

export default ThreeDLogo;
