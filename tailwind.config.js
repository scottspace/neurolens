/** @type {import('tailwindcss').Config} */
const plugin = require('tailwindcss/plugin')

module.exports = {
    content: ["./templates/**/*.html",
	      "./static/src/**/*.js"
	     ],
  theme: {
    extend: {},
  },
  plugins: [
        require('flowbite/plugin')
  ]
}

