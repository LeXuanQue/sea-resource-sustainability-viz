// Paths are relative to src/index.html. On GitHub Pages
// (https://<user>.github.io/<repo>/src/index.html) "../data/" resolves to
// /<repo>/data/, so the data/ folder must be committed at the repo root.
const DATA_DIR = "../data/";

/**
 * Loads values, snapshot, and coverage data once at page load.
 * @returns {Promise<Object|null>} {values, snapshot, coverage}, or null on error.
 */
async function loadData() {
    try {
        const [values, snapshot, coverage] = await Promise.all([
            d3.json(DATA_DIR + "values.json"),
            d3.json(DATA_DIR + "snapshot.json"),
            d3.json(DATA_DIR + "coverage.json")
        ]);
        return { values, snapshot, coverage };
    } catch (error) {
        // Developer details go to the console only.
        console.error("Error loading data:", error);
        console.error(
            "Dev hint: run `python3 -m http.server 8000` in the repo root and open " +
            "http://localhost:8000/src/index.html (opening the HTML via file:// cannot load JSON). " +
            "On GitHub Pages, check that data/*.json is committed and the path '" + DATA_DIR + "' is correct."
        );
        showLoadError();
        return null;
    }
}

/**
 * Shows a short, user-facing error on the page (no white screen).
 */
function showLoadError() {
    if (document.getElementById("load-error")) return; // avoid duplicates

    const div = document.createElement("div");
    div.id = "load-error";
    div.setAttribute("role", "alert");
    div.style.cssText = "color:#b00020;padding:20px;font-weight:600;";
    div.textContent = "Could not load the data. Please reload the page.";
    document.body.prepend(div);
}