/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary
        primary: {
          DEFAULT: '#FFC93C',
          yellow: '#FFC93C',
        },
        // Background
        background: {
          main: '#1E1E1E',
          surface: '#2C2C2C',
        },
        // Border
        border: {
          DEFAULT: '#3A3A3A',
        },
        // Secondary
        secondary: {
          DEFAULT: '#007AFF',
          blue: '#007AFF',
          'tech-blue': '#007AFF',
        },
        // Status
        success: '#32D296',
        warning: '#FFB347',
        danger: '#E63946',
        // Text
        text: {
          primary: '#FFFFFF',
          secondary: '#B0B0B0',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Roboto Mono', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '12px',
      },
    },
  },
  plugins: [],
}

