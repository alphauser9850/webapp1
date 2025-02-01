class TableSearch {
    constructor(searchInputId, tableId, searchColumns) {
        this.searchInput = document.getElementById(searchInputId);
        this.table = document.getElementById(tableId);
        this.searchColumns = searchColumns;
        this.initializeSearch();
    }

    initializeSearch() {
        this.searchInput.addEventListener('keyup', () => this.performSearch());
    }

    performSearch() {
        const searchText = this.searchInput.value.toLowerCase();
        const rows = this.table.getElementsByTagName('tr');

        for (let i = 1; i < rows.length; i++) {
            let found = false;
            for (let col of this.searchColumns) {
                const cellText = rows[i].cells[col].textContent.toLowerCase();
                if (cellText.includes(searchText)) {
                    found = true;
                    break;
                }
            }
            rows[i].style.display = found ? '' : 'none';
        }
    }
} 