import React from 'react';
import { Link } from 'react-router-dom'; // optional, if routing later

export default function Header() {
  return (
    <header className="w-full bg-orchid-200 text-violet-900 shadow-md">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">FixGuide</h1>
        <nav className="space-x-4">
          <a href="#" className="hover:underline">Home</a>
          <a href="#features" className="hover:underline">Features</a>
          <a href="#contact" className="hover:underline">Contact</a>
        </nav>
      </div>
    </header>
  );
}
