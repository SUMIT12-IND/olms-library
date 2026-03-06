// ── Advanced Search with Autocomplete ─────────────
(function() {
    const input = document.getElementById('searchInput');
    const dropdown = document.getElementById('autoDropdown');
    if (!input || !dropdown) return;

    let debounceTimer;

    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        if (query.length < 2) {
            dropdown.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(function() {
            fetch('/user/api/search?q=' + encodeURIComponent(query))
                .then(r => r.json())
                .then(data => {
                    if (data.length === 0) {
                        dropdown.style.display = 'none';
                        return;
                    }
                    dropdown.innerHTML = data.map(b =>
                        `<div class="auto-item" onclick="selectAutoItem('${b.title.replace(/'/g, "\\'")}')">
                            <span class="auto-title">${b.title}</span>
                            <span class="auto-meta">${b.author} · ${b.category}</span>
                        </div>`
                    ).join('');
                    dropdown.style.display = 'block';
                });
        }, 300);
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });
})();

function selectAutoItem(title) {
    document.getElementById('searchInput').value = title;
    document.getElementById('autoDropdown').style.display = 'none';
    // Submit the form
    document.querySelector('.advanced-search-form').submit();
}
