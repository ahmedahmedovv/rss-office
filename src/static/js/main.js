$(document).ready(function() {
    // Wait for all managers to be available
    if (typeof articleManager === 'undefined' || 
        typeof categoryManager === 'undefined' || 
        typeof uiManager === 'undefined') {
        console.error('Required managers not initialized');
        return;
    }

    // Initial load
    async function initialize() {
        try {
            console.log('Starting initialization...');
            
            // Show loading state
            $('#loading').show();
            $('#articles').hide();
            
            // Load read articles and feeds in parallel
            const [readArticlesResponse, feedsResponse] = await Promise.all([
                articleManager.loadReadArticles(),
                $.get('/api/feeds')
            ]);
            
            // Check for the data property in the response
            if (!feedsResponse || !feedsResponse.data || !Array.isArray(feedsResponse.data)) {
                throw new Error(`Invalid response format: ${JSON.stringify(feedsResponse)}`);
            }

            console.log('Received articles:', feedsResponse.data.length); // Debug log
            
            // Use feedsResponse.data instead of feedsResponse directly
            articleManager.allArticles = feedsResponse.data;
            
            // Process categories and update counts
            setTimeout(() => {
                feedsResponse.data.forEach(article => {
                    if (article.category) {
                        categoryManager.categories.add(article.category);
                    }
                });
                categoryManager.updateCategoryFilters();
                uiManager.updateCategoryCounts();
            }, 0);
            
            // Show articles
            $('#loading').hide();
            $('#articles').show();
            uiManager.filterArticles();
            
        } catch (error) {
            console.error('Detailed initialization error:', error);
            $('#loading').hide();
            $('#articles').html(`
                <div class="flash flash-error">
                    <h3>Error loading articles</h3>
                    <p>${error.message}</p>
                    <pre>${error.stack}</pre>
                </div>
            `);
        }
    }

    // Start the application
    initialize();
}); 