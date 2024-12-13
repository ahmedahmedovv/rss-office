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

    initializeMarkAllReadHandler() {
        $('#markAllRead').change(async (e) => {
            const isChecked = $(e.target).is(':checked');
            const currentCategory = $('.category-filter.active').data('category');
            
            if (isChecked) {
                const visibleArticles = $('.article-box:visible');
                for (const article of visibleArticles) {
                    const link = $(article).data('link');
                    await articleManager.markAsRead(link);
                }
            }
            
            this.filterArticles(currentCategory);
        });
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

    filterArticles(category) {
        console.log('Starting filterArticles:', {
            totalArticles: articleManager.allArticles.length,
            category: category,
            showOnlyUnread: this.showOnlyUnread,
            articleManagerState: articleManager
        });

        if (!Array.isArray(articleManager.allArticles)) {
            console.error('allArticles is not an array:', articleManager.allArticles);
            $('#articles').html(`
                <div class="flash flash-error">
                    Error: Invalid articles data structure
                </div>
            `);
            return;
        }

        this.updateCategoryCounts();

        const filteredArticles = articleManager.allArticles.filter(article => {
            if (category && article.category !== category) return false;
            if (this.showOnlyUnread && articleManager.isArticleRead(article.link)) {
                console.log('Filtering out read article:', article.link);
                return false;
            }
            return true;
        });

        console.log('Filtered articles count:', filteredArticles.length);

        if (filteredArticles.length === 0) {
            $('#articles').html(`
                <div class="flash flash-warn">
                    No articles found${category ? ` in category "${category}"` : ''}
                    ${this.showOnlyUnread ? ' (showing only unread)' : ''}
                </div>
            `);
        } else {
            const articlesHtml = filteredArticles.map(article => {
                try {
                    return articleManager.createArticleHtml(article);
                } catch (error) {
                    console.error('Error creating HTML for article:', article, error);
                    return '';
                }
            }).join('');
            
            $('#articles').html(articlesHtml);
        }
        
        this.updateVisibleArticles();
    }

    updateCategoryCounts() {
        console.log('Updating category counts...');
        const categoryCounts = {};
        
        articleManager.allArticles.forEach(article => {
            if (article.category) {
                if (!categoryCounts[article.category]) {
                    categoryCounts[article.category] = 0;
                }
                if (!this.showOnlyUnread || !articleManager.isArticleRead(article.link)) {
                    categoryCounts[article.category]++;
                }
            }
        });

        $('.category-filter').each(function() {
            const category = $(this).data('category');
            const count = categoryCounts[category] || 0;
            $(this).find('.category-count').text(count);
        });

        const totalUnread = Object.values(categoryCounts).reduce((a, b) => a + b, 0);
        $('#total-unread-count').text(totalUnread);
        
        console.log('Category counts updated:', categoryCounts);
    }
}

window.uiManager = new UIManager(); 