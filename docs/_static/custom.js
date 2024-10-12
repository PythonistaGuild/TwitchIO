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
	pre_.classList.add("admonition", "codeW");
}

document.addEventListener("DOMContentLoaded", (e) => {
	const search = document.getElementById("search-form");
	search.id = "search-form_";

	const button = search.querySelector(".input-group>.input-group-prepend");
	button.addEventListener("click", (e) => {
		const inp = document.getElementById("searchinput");
		if (!inp.textContent) {
			return;
		}

		search.submit();
	});
});
