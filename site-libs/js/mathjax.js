MathJax.Hub.Config({
  extensions: ["tex2jax.js"],
  jax: ["input/TeX", "output/HTML-CSS"],
  tex2jax: {
    inlineMath: [ ['$','$'], ["\\\\(","\\\\)"] ],
    displayMath: [ ['$$','$$'], ["\\\\[","\\\\]"] ],
    processEscapes: true
  },
  "HTML-CSS": {
    preferredFont: "TeX",
    availableFonts: ["TeX"],
    styles: {
      scale: 110,
      ".MathJax_Display": {
        "font-size": "110%",
      }
    }
  }
});