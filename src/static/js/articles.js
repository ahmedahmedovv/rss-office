class ArticleManager {
    constructor() {
        this.allArticles = [];
        this.readArticles = new Set();
    }

    async loadReadArticles() {
        try {
            const response = await $.get('/api/articles/read');
            this.readArticles = new Set(response.read_articles);
            console.log('Loaded read articles:', this.readArticles);
            return this.readArticles;
        } catch (error) {
            console.error('Error loading read articles:', error);
            throw error;
        }
    }

    async markAsRead(link, openInNewTab = false) {
        console.log('Marking article as read:', link);
        const $article = this.getArticleElement(link);
        
        if ($article.hasClass('loading')) {
            console.log('Article is already being processed');
            return;
        }
        
        try {
            $article.addClass('loading');
            
            // Make the API call first
            const response = await $.ajax({
                url: '/api/articles/read',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ link: link })
            });
            
            if (response.is_read !== undefined) {
                // Update the UI
                this.updateArticleReadStatus(link, response.is_read);
                
                // Update category counts
                if (window.uiManager) {
                    window.uiManager.updateCategoryCounts();
                }
                
                // Only open in new tab if explicitly requested (when clicking the title)
                if (openInNewTab && response.is_read) {
                    window.open(link, '_blank');
                }
            }
        } catch (error) {
            console.error('Error marking as read:', error);
            if (window.uiManager) {
                window.uiManager.showToast('Failed to update article status', 'error');
            }
        } finally {
            $article.removeClass('loading');
        }
    }

    getArticleElement(link) {
        return $(`.article-box[data-link="${link}"]`);
    }

    updateArticleReadStatus(link, isRead) {
        console.log('Updating article read status:', { link, isRead });
        const $article = this.getArticleElement(link);
        
        if (isRead) {
            this.readArticles.add(link);
            $article.addClass('read');
        } else {
            this.readArticles.delete(link);
            $article.removeClass('read');
        }
        
        // Remove immediate hiding of articles
        // The filtering will happen when changing categories or toggling show/unread
    }

    isArticleRead(link) {
        return this.readArticles.has(link);
    }

    createArticleHtml(article) {
        const formattedDate = this.formatArticleDate(article.pub_date);
        const isRead = this.isArticleRead(article.link);
        const escapedLink = article.link.replace(/'/g, '\\\'');
        
        return `
            <div class="Box mb-3 article-box ${isRead ? 'read' : ''}" 
                 data-link="${escapedLink}"
                 onclick="articleManager.markAsRead('${escapedLink}', false)"
                 style="cursor: pointer">
                <div class="Box-header d-flex flex-items-center">
                    <h3 class="Box-title flex-auto">
                        <span class="Link--primary" 
                              onclick="event.stopPropagation(); articleManager.markAsRead('${escapedLink}', true)">
                            ${article.ai_title || article.title || 'Not available'}
                        </span>
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

window.articleManager = new ArticleManager(); 