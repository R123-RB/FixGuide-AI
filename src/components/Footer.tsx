import React from 'react';

export default function Footer() {
  return (
    <footer className="w-full bg-orchid-200 text-violet-900 py-4 mt-12">
      <div className="max-w-5xl mx-auto px-4 text-center">
        <p className="text-sm">© 2026 FixGuide • All rights reserved.</p>
        <div className="flex justify-center space-x-4 mt-2">
          <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:underline">GitHub</a>
          <a href="mailto:info@fixguide.com" className="hover:underline">Contact</a>
        </div>
      </div>
    </footer>
  );
}
