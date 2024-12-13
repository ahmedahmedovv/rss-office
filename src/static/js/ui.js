class UIManager {
    constructor() {
        this.currentArticleIndex = -1;
        this.visibleArticles = [];
        this.showOnlyUnread = $('#showOnlyUnread').is(':checked');
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.initializeKeyboardNavigation();
        this.initializeToggleHandlers();
        this.initializeSortingHandlers();
        this.initializeMarkAllReadHandler();
    }

    showToast(message, type = 'info') {
        const toast = $(`<div class="toast ${type}">${message}</div>`);
        $('body').append(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    updateVisibleArticles() {
        this.visibleArticles = $('.article-box:visible').toArray();
        this.currentArticleIndex = -1;
    }

    scrollToArticle(article) {
        if (!article) return;

        article.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
        
        $('.article-box').removeClass('border-green');
        $(article).addClass('border-green');
        
        const $article = $(article);
        const link = $article.data('link');
        articleManager.markAsRead(link);
    }

    initializeKeyboardNavigation() {
        $(document).keydown((e) => {
            if ($(e.target).is('input, textarea')) return;

            if (e.key === 'n' || e.key === 'k') {
                e.preventDefault();
                this.handleKeyboardNavigation(e.key);
            }
        });
    }

    handleKeyboardNavigation(key) {
        if (this.currentArticleIndex === -1) {
            this.updateVisibleArticles();
            this.currentArticleIndex = key === 'n' ? 0 : this.visibleArticles.length - 1;
        } else {
            this.currentArticleIndex = key === 'n' 
                ? Math.min(this.currentArticleIndex + 1, this.visibleArticles.length - 1)
                : Math.max(this.currentArticleIndex - 1, 0);
        }
        this.scrollToArticle(this.visibleArticles[this.currentArticleIndex]);
    }

    initializeToggleHandlers() {
        $('#showOnlyUnread').change(() => {
            this.showOnlyUnread = $('#showOnlyUnread').is(':checked');
            const currentCategory = $('.category-filter.active').data('category');
            this.filterArticles(currentCategory);
        });
    }

    initializeSortingHandlers() {
        $('.BtnGroup-item').click(function() {
            const sortType = $(this).data('sort');
            $('.BtnGroup-item').removeClass('selected');
            $(this).addClass('selected');
            this.handleArticleSorting(sortType);
        });
    }

    handleArticleSorting(sortType) {
        // Sorting logic implementation
    }
}

const uiManager = new UIManager(); 