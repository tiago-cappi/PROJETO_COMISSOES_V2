import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const appBootstrapStart = performance.now();
console.log('[DEBUG STARTUP] index.js carregado');

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

requestAnimationFrame(() => {
  const elapsedMs = performance.now() - appBootstrapStart;
  console.log(`[DEBUG STARTUP] primeiro frame após render em ${elapsedMs.toFixed(1)}ms`);
});

window.addEventListener('load', () => {
  const elapsedMs = performance.now() - appBootstrapStart;
  console.log(`[DEBUG STARTUP] evento load da janela em ${elapsedMs.toFixed(1)}ms`);
});

