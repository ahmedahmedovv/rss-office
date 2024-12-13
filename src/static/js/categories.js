class CategoryManager {
    constructor() {
        this.categories = new Set();
        this.favoriteCategories = new Set(JSON.parse(localStorage.getItem('favoriteCategories') || '[]'));
        this.categoryOrder = JSON.parse(localStorage.getItem('categoryOrder') || '[]');
    }

    initializeSortable() {
        const categoriesList = document.getElementById('categories-list');
        if (!categoriesList) return;

        const existingInstance = Sortable.get(categoriesList);
        if (existingInstance) {
            existingInstance.destroy();
        }

        new Sortable(categoriesList, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            handle: '.drag-handle',
            forceFallback: false,
            onEnd: (evt) => this.handleSortEnd(evt)
        });
    }

    handleSortEnd(evt) {
        const newOrder = Array.from(evt.to.children).map(
            el => this.decodeHtml(el.dataset.category)
        );
        this.categoryOrder = newOrder;
        localStorage.setItem('categoryOrder', JSON.stringify(this.categoryOrder));
        this.updateCategoryFilters();
    }

    sortCategories() {
        return Array.from(this.categories).sort((a, b) => {
            const aFav = this.favoriteCategories.has(a);
            const bFav = this.favoriteCategories.has(b);
            
            if (aFav !== bFav) return bFav ? 1 : -1;
            return this.compareCategoryOrder(a, b);
        });
    }

    compareCategoryOrder(a, b) {
        const aIndex = this.categoryOrder.indexOf(a);
        const bIndex = this.categoryOrder.indexOf(b);
        
        if (aIndex === -1 && bIndex === -1) return a.localeCompare(b);
        if (aIndex === -1) return 1;
        if (bIndex === -1) return -1;
        return aIndex - bIndex;
    }

    decodeHtml(html) {
        const txt = document.createElement("textarea");
        txt.innerHTML = html;
        return txt.value;
    }

    toggleFavorite(category) {
        if (this.favoriteCategories.has(category)) {
            this.favoriteCategories.delete(category);
        } else {
            this.favoriteCategories.add(category);
        }
        localStorage.setItem('favoriteCategories', 
            JSON.stringify(Array.from(this.favoriteCategories)));
    }
}

const categoryManager = new CategoryManager(); 