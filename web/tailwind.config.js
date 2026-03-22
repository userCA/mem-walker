/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#faf9f7',
        card: '#ffffff',
        'text-primary': '#1a1a1a',
        'text-secondary': '#64748b',
        'text-muted': '#8b8680',
        border: '#e2ddd8',
        'border-light': '#f0eeeb',
        amber: {
          highlight: '#fef3c7',
          DEFAULT: '#f59e0b',
        },
        success: '#22c55e',
        category: {
          work: '#ecfdf5',
          personal: '#fce7f3',
          project: '#e0f2fe',
          study: '#f0fdf4',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 2s ease-in-out infinite',
      },
      boxShadow: {
        'card': '0 2px 8px rgba(0,0,0,0.06)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08)',
        'amber': '0 2px 8px rgba(245, 158, 11, 0.15)',
      },
    },
  },
  plugins: [],
}
