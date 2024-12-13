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
            
            console.log('Loading read articles...');
            await articleManager.loadReadArticles();
            console.log('Read articles loaded:', articleManager.readArticles.size);
            
            console.log('Fetching feeds from API...');
            const response = await $.get('/api/feeds');
            console.log('Raw API response:', {
                type: typeof response,
                length: Array.isArray(response) ? response.length : 'not an array',
                sample: Array.isArray(response) && response.length > 0 ? response[0] : null
            });
            
            if (!response || !Array.isArray(response)) {
                throw new Error(`Invalid response format: ${JSON.stringify(response)}`);
            }

            $('#loading').hide();
            articleManager.allArticles = response;
            
            // Process categories
            console.log('Processing categories...');
            response.forEach(article => {
                if (article.category) {
                    categoryManager.categories.add(article.category);
                }
            });
            console.log('Categories found:', Array.from(categoryManager.categories));
            
            // Update UI
            categoryManager.updateCategoryFilters();
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