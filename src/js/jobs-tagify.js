const inputElem = document.querySelector('#id_jobs');

// Initialize Tagify
const tagify = new Tagify(inputElem, {
  enforceWhitelist: false,
  whitelist: [],
  dropdown: {
    enabled: 1, // Show dropdown when typing
    maxItems: 10,
    highlightFirst: true
  },
  maxTags: 10
});

// Cache to store previous API results
const cache = new Map();

// Function to fetch data from API dynamically
async function fetchWhitelist(query) {
  if (cache.has(query)) {
    // console.log('Using cached results for:', query);
    return cache.get(query);
  }

  try {
    const response = await fetch(
      `${JOBS_TAGIFY_URL}?search=${encodeURIComponent(query)}`
    );
    const data = await response.json();
    const results = data.results.map((job) => ({
      value: job.name,
      id: job.id
    }));

    cache.set(query, results); // Cache results
    return results;
  } catch (error) {
    console.error('Error fetching whitelist:', error);
    return [];
  }
}

// Debounce function to prevent excessive API calls
function debounce(func, delay) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), delay);
  };
}

// Handle input event (debounced API requests)
const onInputDebounced = debounce(async (e) => {
  const query = e.detail.value.trim();

  if (query.length < 2) {
    return;
  } // Only search when more than 2 characters

  tagify.loading(true);
  tagify.whitelist = [];

  const results = await fetchWhitelist(query);
  tagify.settings.whitelist = results;
  tagify.whitelist = [...results];
  tagify.loading(false);
  tagify.dropdown.show(query);
}, 300); // Delay API calls by 300ms

// Attach input event
tagify.on('input', onInputDebounced);

tagify.on('isTagDuplicate', (e) => {
  console.log('Duplicate tag detected:', e.detail.data.value);
});
