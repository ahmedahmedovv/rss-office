class UIManager {
    constructor() {
        this.currentArticleIndex = -1;
        this.visibleArticles = [];
        this.showOnlyUnread = $('#showOnlyUnread').is(':checked');
        this.currentSortDirection = 'newest';
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
        $('#showOnlyUnread').change((e) => {
            this.showOnlyUnread = $(e.target).is(':checked');
            const currentCategory = $('.category-filter.active').data('category');
            this.updateCategoryCounts();
            this.filterArticles(currentCategory);
        });
    }

    initializeSortingHandlers() {
        $('.BtnGroup-item').click((e) => {
            const $button = $(e.currentTarget);
            $('.BtnGroup-item').removeClass('selected');
            $button.addClass('selected');
            
            this.currentSortDirection = $button.data('sort');
            
            const currentCategory = $('.category-filter.active').data('category');
            this.filterArticles(currentCategory);
        });
    }

    filterArticles(category = null) {
        if (!category) {
            $('#articles').html(`
                <div class="blankslate">
                    <h3>Select a Category</h3>
                    <p>Choose a category from the sidebar to view articles.</p>
                </div>
            `);
            return;
        }

        let filteredArticles = [...articleManager.allArticles];
        
        if (category) {
            filteredArticles = filteredArticles.filter(article => article.category === category);
        }
        
        if (this.showOnlyUnread) {
            filteredArticles = filteredArticles.filter(article => 
                !articleManager.isArticleRead(article.link)
            );
        }
        
        filteredArticles.sort((a, b) => {
            const dateA = new Date(a.pub_date || 0);
            const dateB = new Date(b.pub_date || 0);
            
            return this.currentSortDirection === 'newest' ? dateB - dateA : dateA - dateB;
        });

        const headerText = category ? `${category} Articles` : 'All Articles';
        $('#content-header').text(headerText);

        if (filteredArticles.length === 0) {
            $('#articles').html(`
                <div class="blankslate">
                    <h3>No articles found</h3>
                    <p>Try changing your filters or check back later for new articles.</p>
                </div>
            `);
            return;
        }

        const BATCH_SIZE = 50;
        const batches = Math.ceil(filteredArticles.length / BATCH_SIZE);
        
        let currentBatch = 0;
        $('#articles').empty();

        const renderNextBatch = () => {
            if (currentBatch >= batches) {
                this.updateVisibleArticles();
                return;
            }

            const start = currentBatch * BATCH_SIZE;
            const end = Math.min(start + BATCH_SIZE, filteredArticles.length);
            const fragment = document.createDocumentFragment();

            for (let i = start; i < end; i++) {
                const articleHtml = articleManager.createArticleHtml(filteredArticles[i]);
                const div = document.createElement('div');
                div.innerHTML = articleHtml;
                fragment.appendChild(div.firstElementChild);
            }

            $('#articles').append(fragment);
            currentBatch++;
            requestAnimationFrame(renderNextBatch);
        };

        requestAnimationFrame(renderNextBatch);
    }

    updateCategoryCounts() {
        console.log('Updating category counts...');
        const categoryCounts = {};
        
        articleManager.allArticles.forEach(article => {
            if (article.category) {
                if (!categoryCounts[article.category]) {
                    categoryCounts[article.category] = 0;
                }
                if (!articleManager.isArticleRead(article.link)) {
                    categoryCounts[article.category]++;
                }
            }
        });

        $('.category-filter').each(function() {
            const category = $(this).data('category');
            const count = categoryCounts[category] || 0;
            $(this).find('.category-count').text(count);
            
            if (uiManager.showOnlyUnread) {
                $(this).toggle(count > 0);
            } else {
                $(this).show();
            }
        });

        const totalUnread = Object.values(categoryCounts).reduce((a, b) => a + b, 0);
        $('#total-unread-count').text(totalUnread);
        
        console.log('Category counts updated:', categoryCounts);
    }
}

window.uiManager = new UIManager(); 