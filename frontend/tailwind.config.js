/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './app/components/**/*.{vue,js,ts}',
    './app/layouts/**/*.{vue,js,ts}',
    './app/pages/**/*.{vue,js,ts}',
    './app/app.vue',
    './app/error.vue',
    './app.vue'
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          DEFAULT: '#0b3022',
          dark: '#123A2C',
          light: '#042718'
        },
        gold: {
          DEFAULT: '#D4AF37',
          light: '#E3B94A'
        },
        cream: {
          DEFAULT: '#FAF6EE',
          soft: '#F3ECDD',
          card: '#FBF8F1'
        }
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        sans: ['Inter', 'sans-serif']
      }
    }
  },
  plugins: []
}