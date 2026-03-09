// PWA Registration Script for Agri-Nexus
// This script registers the service worker for offline support

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/service-worker.js')
      .then((registration) => {
        console.log('✅ Service Worker registered successfully:', registration.scope);
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          console.log('🔄 Service Worker update found');
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              console.log('✨ New content available, please refresh');
              
              // Optionally show a notification to the user
              if (confirm('New version available! Reload to update?')) {
                newWorker.postMessage({ type: 'SKIP_WAITING' });
                window.location.reload();
              }
            }
          });
        });
      })
      .catch((error) => {
        console.error('❌ Service Worker registration failed:', error);
      });
    
    // Handle service worker updates
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (!refreshing) {
        refreshing = true;
        window.location.reload();
      }
    });
  });
  
  // Listen for online/offline events
  window.addEventListener('online', () => {
    console.log('📡 Back online');
    document.body.classList.remove('offline');
  });
  
  window.addEventListener('offline', () => {
    console.log('📡 Gone offline');
    document.body.classList.add('offline');
  });
  
  // Check if app is installed
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('💾 App can be installed');
    // Store the event for later use
    window.deferredPrompt = e;
  });
  
  window.addEventListener('appinstalled', () => {
    console.log('✅ App installed successfully');
  });
} else {
  console.warn('⚠️ Service Workers not supported in this browser');
}

// Add PWA install button functionality
function showInstallPrompt() {
  if (window.deferredPrompt) {
    window.deferredPrompt.prompt();
    window.deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the install prompt');
      }
      window.deferredPrompt = null;
    });
  }
}

console.log('🌾 Agri-Nexus PWA initialized');
