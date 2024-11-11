import React from 'react';
// import { User, Coins } from 'lucide-react';

const TokenDetails = () => {
  return (
    <div className="bg-gray-900 p-4">
      <div className="flex gap-4">
        {/* Coins/Points Container */}
        <div className="flex items-center gap-2 bg-amber-800/60 text-amber-300 px-4 py-2 rounded-full">
          <Coins size={20} />
          <span className="font-semibold">40</span>
        </div>

        {/* Greeting Container */}
        <div className="flex items-center gap-2 bg-blue-600/40 text-blue-100 px-4 py-2 rounded-full">
          <User size={20} />
          <span className="font-semibold">Hi Aakash!</span>
        </div>
      </div>
    </div>
  );
};

export default TokenDetails;