/**
 * borkert.dev — Minimalist Editorial Script
 * Handles subtle theme toggling with preference persistence.
 */

(() => {
  'use strict';

  const themeToggleBtn = document.getElementById('theme-toggle');
  const storedTheme = localStorage.getItem('digplan-theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  // Initialize theme
  if (storedTheme) {
    document.documentElement.setAttribute('data-theme', storedTheme);
    updateToggleLabel(storedTheme);
  } else {
    updateToggleLabel(systemPrefersDark ? 'dark' : 'light');
  }

  function updateToggleLabel(theme) {
    if (themeToggleBtn) {
      themeToggleBtn.textContent = theme === 'dark' ? 'light mode' : 'dark mode';
    }
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || (systemPrefersDark ? 'dark' : 'light');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('digplan-theme', newTheme);
      updateToggleLabel(newTheme);
    });
  }
})();
