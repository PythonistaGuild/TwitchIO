
const funcHeaders = document.querySelectorAll(".pythonista-func-header");

for (let header of funcHeaders) {
    let signature = header.querySelectorAll(".doc-signature.highlight > pre > code")[0];
    signature.classList += "highlight"
    header.replaceWith(signature);
}
