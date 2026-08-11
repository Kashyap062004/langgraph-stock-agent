import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { GoogleOAuthProvider } from '@react-oauth/google';
import App from './App';
import './index.css';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

if (!GOOGLE_CLIENT_ID) {
  // Fail loudly in dev rather than silently rendering a broken/missing
  // Google button with no explanation — this is a required env var.
  console.error(
    'VITE_GOOGLE_CLIENT_ID is not set. Add it to your .env file (see .env.example).'
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID ?? ''}>
      <App />
    </GoogleOAuthProvider>
  </StrictMode>
);
