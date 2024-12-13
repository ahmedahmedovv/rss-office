class ReadManager {
    constructor() {
        this.readArticles = new Set(this.loadReadArticles());
    }

    loadReadArticles() {
        const stored = localStorage.getItem('readArticles');
        return stored ? JSON.parse(stored) : [];
    }

    saveReadArticles() {
        localStorage.setItem('readArticles', JSON.stringify([...this.readArticles]));
    }

    markAsRead(articleLink) {
        this.readArticles.add(articleLink);
        this.saveReadArticles();
    }

    markAsUnread(articleLink) {
        this.readArticles.delete(articleLink);
        this.saveReadArticles();
    }

    isRead(articleLink) {
        return this.readArticles.has(articleLink);
    }

    async markAllAsRead(articles) {
        try {
            // Convert jQuery object to array if needed
            const articleElements = articles instanceof jQuery ? articles.toArray() : articles;
            
            for (const article of articleElements) {
                const $article = $(article);
                const link = $article.data('link');
                
                if (link && !this.isRead(link)) {
                    this.markAsRead(link);
                    $article.addClass('read');
                    
                    // Update article appearance
                    $article.find('.Link--primary').addClass('read');
                }
            }
            
            // Save changes to localStorage
            this.saveReadArticles();
            
            return true;
        } catch (error) {
            console.error('Error in markAllAsRead:', error);
            return false;
        }
    }

    getUnreadCount(articles) {
        return articles.filter(article => !this.isRead(article.link)).length;
    }

    areAllRead(articles) {
        const articleElements = articles instanceof jQuery ? articles.toArray() : articles;
        return articleElements.every(article => {
            const link = $(article).data('link');
            return this.isRead(link);
        });
    }

    async toggleReadStatus(articles) {
        try {
            const articleElements = articles instanceof jQuery ? articles.toArray() : articles;
            const markAsRead = !this.areAllRead(articleElements);

            for (const article of articleElements) {
                const $article = $(article);
                const link = $article.data('link');
                
                if (link) {
                    if (markAsRead) {
                        this.markAsRead(link);
                        $article.addClass('read');
                        $article.find('.Link--primary').addClass('read');
                    } else {
                        this.markAsUnread(link);
                        $article.removeClass('read');
                        $article.find('.Link--primary').removeClass('read');
                    }
                }
            }
            
            this.saveReadArticles();
            return { success: true, action: markAsRead ? 'read' : 'unread' };
        } catch (error) {
            console.error('Error in toggleReadStatus:', error);
            return { success: false, error };
        }
    }
}

window.readManager = new ReadManager(); 