import React from 'react';
import Header from './components/Header';
import Footer from './components/Footer';

function App() {
  return (
    <div className="min-h-screen bg-orchid-100 flex flex-col items-center justify-center text-violet-800">
      <Header />
      <main className="p-4 bg-white rounded shadow-lg max-w-lg w-full">
        <h2 className="text-2xl font-semibold text-center mb-4">Welcome to FixGuide</h2>
        <p className="text-center text-gray-700">Retro pastel‑orchid & deep‑violet theme. Add your components here.</p>
      </main>
      <Footer />
    </div>
  );
}

export default App;
