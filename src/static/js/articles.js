class ArticleManager {
    constructor() {
        this.allArticles = [];
        this.readArticles = new Set();
    }

    async loadReadArticles() {
        try {
            const response = await $.get('/api/articles/read');
            this.readArticles = new Set(response.read_articles);
            return this.readArticles;
        } catch (error) {
            console.error('Error loading read articles:', error);
            throw error;
        }
    }

    isArticleRead(link) {
        return this.readArticles.has(link);
    }

    async markAsRead(link) {
        const $article = this.getArticleElement(link);
        if ($article.hasClass('loading')) return;
        
        try {
            $article.addClass('loading');
            const response = await $.ajax({
                url: '/api/articles/read',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ link: link })
            });
            
            if (response.is_read !== undefined) {
                this.updateArticleReadStatus(response.link, response.is_read);
            }
        } catch (error) {
            console.error('Error marking as read:', error);
            showToast('Failed to update article status', 'error');
        } finally {
            $article.removeClass('loading');
        }
    }

    getArticleElement(link) {
        return $(`.article-box[data-link="${link}"]`);
    }

    updateArticleReadStatus(link, isRead) {
        const $article = this.getArticleElement(link);
        if (isRead) {
            this.readArticles.add(link);
            $article.addClass('read fade-transition');
        } else {
            this.readArticles.delete(link);
            $article.removeClass('read fade-transition');
        }
    }

    createArticleHtml(article) {
        const formattedDate = this.formatArticleDate(article.pub_date);
        const isRead = this.isArticleRead(article.link);
        
        return `
            <div class="Box mb-3 article-box ${isRead ? 'read' : ''}" data-link="${article.link}">
                <div class="Box-header d-flex flex-items-center">
                    <h3 class="Box-title flex-auto">
                        <a href="${article.link}" class="Link--primary" target="_blank">
                            ${article.ai_title || article.title || 'Not available'}
                        </a>
                    </h3>
                    <span class="text-small color-fg-muted">${formattedDate}</span>
                </div>
                <div class="Box-body">
                    <p class="text-small color-fg-muted mb-0">
                        ${article.summary || article.description || 'No summary available'}
                    </p>
                </div>
            </div>
        `;
    }

    formatArticleDate(pubDate) {
        if (!pubDate) return 'Not available';
        const date = new Date(pubDate);
        return date.toLocaleDateString('en-GB', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }
}

const articleManager = new ArticleManager(); 