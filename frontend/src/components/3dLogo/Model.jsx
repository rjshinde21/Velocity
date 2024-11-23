import React, { useRef } from 'react';
import { useGLTF } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';

export function Model(props) {
  const { nodes, materials } = useGLTF('./logo_velocity_blue.glb');
  const group = useRef(); 
  useFrame(() => {
    if (group.current) {
      group.current.rotation.y += 0.02; 
      // group.current.rotation.x += 0.01; 
    }
  });

  return (
    <group ref={group} {...props} dispose={null}>
      <mesh
        castShadow
        receiveShadow
        geometry={nodes.Plane.geometry}
        material={materials.Velocity_Icon}
      />
    </group>
  );
}

useGLTF.preload('./logo_velocity_blue.glb');
