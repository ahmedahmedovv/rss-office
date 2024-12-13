let readFeeds = new Set(JSON.parse(localStorage.getItem('readFeeds') || '[]'));
let currentCategory = 'all';

function loadFeeds() {
    $.ajax({
        url: '/api/feeds',
        method: 'GET',
        success: (feeds) => {
            // Calculate unread counts per category
            const unreadCounts = {};
            feeds.forEach(feed => {
                const category = feed.category || 'uncategorized';
                if (!readFeeds.has(feed.id)) {
                    unreadCounts[category] = (unreadCounts[category] || 0) + 1;
                    unreadCounts['all'] = (unreadCounts['all'] || 0) + 1;
                }
            });

            // Extract unique categories
            const categories = ['all', ...new Set(feeds.map(feed => feed.category || 'uncategorized'))];
            
            // Update category sidebar with unread counts
            const categoryHtml = categories.map(category => `
                <div class="category-item ${category === currentCategory ? 'active' : ''}" 
                     data-category="${category}">
                    ${category.charAt(0).toUpperCase() + category.slice(1)}
                    ${unreadCounts[category] ? 
                        `<span class="unread-count">${unreadCounts[category]}</span>` : 
                        ''}
                </div>
            `).join('');
            $('#category-list').html(categoryHtml);

            // Filter feeds by category
            const filteredFeeds = currentCategory === 'all' 
                ? feeds 
                : feeds.filter(feed => feed.category === currentCategory);

            // Update feed count and list
            $('#feed-count').text(filteredFeeds.length);
            const html = filteredFeeds.map(feed => `
                <div class="feed-item ${readFeeds.has(feed.id) ? 'read' : ''}" 
                     data-id="${feed.id}">
                    <h4><a href="${feed.link}" target="_blank">${feed.title}</a></h4>
                    <p class="color-fg-muted">${feed.summary || ''}</p>
                </div>
            `).join('');
            $('#feed-list').html(html);
        },
        error: () => {
            $('#feed-list').html(
                '<div class="flash flash-error">Failed to load feeds</div>'
            );
        }
    });
}

$(document).ready(() => {
    loadFeeds();

    // Mark as read
    $(document).on('click', '.feed-item', function() {
        const id = $(this).data('id');
        $(this).toggleClass('read');
        readFeeds.has(id) ? readFeeds.delete(id) : readFeeds.add(id);
        localStorage.setItem('readFeeds', JSON.stringify([...readFeeds]));
    });

    // Category selection
    $(document).on('click', '.category-item', function() {
        currentCategory = $(this).data('category');
        $('.category-item').removeClass('active');
        $(this).addClass('active');
        loadFeeds();
    });

    // Refresh
    $('#refresh-btn').click(loadFeeds);
}); 