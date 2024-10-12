const tables = document.querySelectorAll(
	".py-attribute-table[data-move-to-id]",
);
for (const table of tables) {
	const element = document.getElementById(
		table.getAttribute("data-move-to-id"),
	);
	const parent = element.parentNode;

	// insert ourselves after the element
	parent.insertBefore(table, element.nextSibling);
}

const pres = document.querySelectorAll("pre");
for (const pre_ of pres) {
	pre_.classList.add("admonition");
	pre_.insertAdjacentHTML(
		"afterbegin",
		`<span class="admonition-title codeB">Code</span>`,
	);
}
