$(document).ready(function() {
    // Initialize managers
    const article = articleManager;
    const category = categoryManager;
    const ui = uiManager;

    // Initial load
    async function initialize() {
        try {
            await article.loadReadArticles();
            
            const response = await $.get('/api/feeds');
            $('#loading').hide();
            article.allArticles = response;
            
            response.forEach(article => {
                if (article.category) {
                    category.categories.add(article.category);
                }
            });
            
            // Initialize category order if empty
            if (category.categoryOrder.length === 0) {
                category.categoryOrder = Array.from(category.categories);
                localStorage.setItem('categoryOrder', JSON.stringify(category.categoryOrder));
            }
            
            category.updateCategoryFilters();
            $('#articles').html('');
        } catch (error) {
            $('#loading').hide();
            $('#articles').html(`
                <div class="flash flash-error">
                    Error loading articles: ${error}
                </div>
            `);
        }
    }

    // Start the application
    initialize();
}); 