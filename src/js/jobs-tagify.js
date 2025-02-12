const inputElem = document.querySelector('#id_jobs');
const noticeText = document.querySelector('#career-paths-notice');
// Initialize Tagify
const tagify = new Tagify(inputElem, {
  // Based on the documentation, This helper function is used to format the value of the input field in the comma-separated format.
  originalInputValueFormat: (valuesArr) => valuesArr.map((item) => item.value).join(','),
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
    return cache.get(query);
  }

  try {
    const response = await fetch(
      `${JOBS_TAGIFY_URL}?search=${encodeURIComponent(query)}`
    );
    const data = await response.json();
    const results = data.results.map((job) => job.name);

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

// Attach keydown event
tagify.on('keydown', (e) => {
  if (noticeText.classList.contains('d-none')) {
    return;
  }
  noticeText.classList.add('d-none');
});

// Attach input event
tagify.on('input', onInputDebounced);

// Validate tagify input
tagify.on('invalid', (e) => {
  if (e.detail.data.__isValid === 'already exists') {
    noticeText.classList.remove('d-none');
    noticeText.textContent = 'This career already exists';
  }
  if (e.detail.data.__isValid === 'number of tags exceeded') {
    noticeText.classList.remove('d-none');
    noticeText.textContent = 'Maximum limit reached. You can add up to 10 career paths.';
  }
});
