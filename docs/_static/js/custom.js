const loadCSS = function(){
    let cssLink = document.createElement('link');
    cssLink.rel = 'stylesheet';
    cssLink.href = '_static/css/custom.css';

    let head = document.getElementsByTagName('head')[0];
    head.parentNode.insertBefore(cssLink, head);
};

//call function on window load
window.addEventListener('load', loadCSS);