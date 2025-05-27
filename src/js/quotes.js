import Tagify from '@yaireo/tagify';
// Variables
// Global Variables
const baseUrl = window.location.origin;
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
const programId = document.querySelector('[name=quote-section]').getAttribute('data-program-id');

// Active Quotes variables
const activeQuotes = document.querySelectorAll('.active-quotes');
const activeQuotesIds = Array.from(activeQuotes).map((quote) =>
  quote.getAttribute('data-quote-id')
);

// Related Quotes variables
const relatedQuotesWrapper = document.querySelector('#related-quotes-wrapper');
const quoteSearch = document.querySelector('#related-quote-search');

// Quote Modal elements
const titleInputs = document.querySelectorAll('.updatedModalTitle');
const createQuoteModalTitle = document.querySelector('#createQuoteTitle');
const createQuoteTag = document.querySelector('[name="createTags"]');
const expectedGraduationFeild = document.querySelector('#graduationYear');
const modal = document.getElementById('activeQuoteModal');
const editModalSaveBtn = modal.querySelector('#editModalSaveBtn');

// Helper variables
const createQuoteHelperObj = {
  createSouceQuote: '',
  graduationYear: ''
};
const AllQuotes = [];

// API calls
// Retrieve All quotes
const fetchQuotes = async () => {
  try {
    const response = await fetch(`${baseUrl}/api/v1/marketing/quotes/`);
    if (response.ok) {
      const data = await response.json();
      if (data) {
        AllQuotes.push(...data.results);
      }
    } else {
      console.error('Failed to fetch quotes');
    }
  } catch (error) {
    console.error('Error fetching quotes:', error);
  }
};

// Create new quote | POST API request
const createQuote = async (event) => {
  event.preventDefault(); // Prevent form submission
  const sourceName = document
    .getElementById('createSourceQuote')
    .value.trim();
  const quoteText = document.getElementById('createQuoteText').value.trim();
  const quoteTitle = document.getElementById('createQuoteTitle').value.trim();
  const tags = document
    .querySelector('input[name="createTags"]')
    .value.split(',');
  const imageFile = document.getElementById('createCustomFile').files[0];
  const imageAlt = document.getElementById('imageAlt').value.trim();
  // Validation: Check if required fields are empty
  if (!sourceName) {
    alert('Souce Name is required!');
    document.getElementById('createSourceQuote').focus();
    return;
  }
  if (imageFile && !imageAlt) {
    alert('Image Alt Text is required!');
    document.getElementById('imageAlt').focus();
    return;
  }
  if (!quoteTitle) {
    alert('Title is required!');
    document.getElementById('createQuoteTitle').focus();
    return;
  }

  if (!quoteText) {
    alert('Quote text is required!');
    document.getElementById('createQuoteText').focus();
    return;
  }

  if (!tags.length) {
    alert('Tag is required!');
    document.getElementById('createQuoteTitle').focus();
    return;
  }


  try {
    let response;

    if (imageFile) {
      // Create FormData Request if Image Exists
      const formData = new FormData();
      formData.append('quote_text', quoteText);
      formData.append('source', sourceName);
      formData.append('titles', quoteTitle);
      formData.append('image_alt', imageAlt);
      tags.forEach((tag) => formData.append('tags', tag.trim())); // Append multiple tags
      formData.append('image', imageFile);
      response = await fetch(`${baseUrl}/api/v1/marketing/quotes/create/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
          'Program-Id': programId
        },
        body: formData
      });
    } else {
      // Create JSON Request if No Image
      const quoteData = {
        quote_text: quoteText,
        source: sourceName,
        titles: quoteTitle,
        tags: tags.map((tag) => tag.trim())
      };

      response = await fetch(`${baseUrl}/api/v1/marketing/quotes/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
          'Program-Id': programId
        },
        body: JSON.stringify(quoteData)
      });
    }

    if (!response.ok) {
      throw new Error('Failed to create quote.');
    } else {
      location.reload();
    }
  } catch (error) {
    console.log(quoteData);
    console.error('Error:', error);
    alert('Failed to create quote. Please try again.');
  }
};

// Attach Quote to Program | PATCH API request
const attachQuoteToProgram = async (quoteId) => {
  try {
    const response = await fetch(
      `${baseUrl}/api/v1/marketing/quotes/${quoteId}/`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
          'Program-Id': programId,
          'Attr-Quote': 'attachQuote'
        }
      }
    );

    if (response.ok) {
      console.log('Quote attached successfully:', response);
      location.reload();
    } else {
      console.error('Failed to attach quote');
    }
  } catch (error) {
    console.error('Error attaching quote:', error);
  }
};

// Modals
// Create Quote Modal - Image Upload Preview
function handleImageUpload(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      const imageDataUrl = e.target.result;
      sessionStorage.setItem('uploadedImage', imageDataUrl);
      // Update the image preview in the UI
      document.getElementById('createSelectedAvatar').src = imageDataUrl;
    };
    reader.readAsDataURL(file);
    document.getElementById('imageAlt').removeAttribute('disabled');
  }
}
// User Input Event Listeners for Create Quote Modal
titleInputs.forEach((input) => {
  input.addEventListener('change', (e) => {
    if (e.target.classList.contains('form-check-input')) {
      switch (e.target.value) {
        case 'student':
          expectedGraduationFeild.removeAttribute('disabled');

          $('.yearpicker').yearpicker({
            // Default CSS classes
            selectedClass: 'selected text-black bg-primary',
            template: `<div class="yearpicker-container">
                  <div class="yearpicker-header">
                      <div class="yearpicker-prev" data-view="yearpicker-prev">&lsaquo;</div>
                      <div class="yearpicker-current" data-view="yearpicker-current">SelectedYear</div>
                      <div class="yearpicker-next" data-view="yearpicker-next">&rsaquo;</div>
                  </div>
                  <div class="yearpicker-body">
                      <ul class="yearpicker-year" data-view="years">
                      </ul>
                  </div>
              </div>
              `
          });

          $('.yearpicker').on('change', function () {
            createQuoteHelperObj.graduationYear = $(this).val().slice(-2);
            graduationYear
              ? createQuoteModalTitle.value = `${createQuoteHelperObj.graduationYear}'`
              : createQuoteModalTitle.value = '';
          });
          break;

        case 'other':
          createQuoteHelperObj.graduationYear = '';
          expectedGraduationFeild.setAttribute('disabled', '');
          createQuoteModalTitle.value = '';
          break;
      }
    }

    createQuoteHelperObj[e.target.id] = e.target.value;
  });
});

$('.yearpicker').on('change', function () {
  createQuoteHelperObj.graduationYear = $(this).val().slice(-2);
  graduationYear
    ? createQuoteModalTitle.value = `${createQuoteHelperObj.graduationYear}'`
    : createQuoteModalTitle.value = '';
});

// Create Quote Modal - Tagify
new Tagify(createQuoteTag, {
  originalInputValueFormat: (valuesArr) => valuesArr.map((item) => item.value).join(','),
  maxTags: 10
});

// Render assigned Quotes
activeQuotes.forEach((quote) => {
  const editButton = quote.querySelector('.active-quote-edit');
  const quoteId = quote.getAttribute('data-quote-id');

  // Detach assigned Quote | PATCH API request
  const detachButton = quote.querySelector('#detachButton');
  const detachModal = document.getElementById('detachQuoteModal');
  const detachSwitch = document.getElementById('detachSwitch');
  const detachSaveButton = document.querySelector('#detachSaveButton');

  detachButton.addEventListener('click', (event) => {
    $(detachModal).modal('show');
  });
  // Detach Quote from Program | PATCH API request
  detachSaveButton.addEventListener('click', async () => {
    if (detachSwitch.checked) {
      try {
        const response = await fetch(
          `${baseUrl}/api/v1/marketing/quotes/${quoteId}/`,
          {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrftoken,
              'Program-Id': programId,
              'Attr-Quote': 'detachQuote'
            }
          }
        );

        if (response.ok) {
          console.log('Quote updated successfully:', response);
          $(detachModal).modal('hide');
          location.reload();
        } else {
          console.error('Failed to remove quote', response);
        }
      } catch (error) {
        console.error('Error removing quote:', error);
      }
      return;
    }
    $(detachModal).modal('hide');

  });

  // Quotes - Edit button event
  editButton.addEventListener('click', () => {
    const quoteSource = quote.querySelector(
      '.active-quotes-quoteSource'
    ).innerText;
    const quoteText = quote.querySelector('.active-quotes-quoteText').innerHTML;
    const quoteTitle = quote.querySelector(
      '.active-quotes-quoteTitle'
    ).innerHTML;

    document.getElementById('quoteText').value = quoteText;
    document.getElementById('quoteSource').value = quoteSource;
    document.getElementById('quoteTitle').value = quoteTitle;

    $(modal).modal('show');

    // Save button click event
    editModalSaveBtn.onclick = async () => {
      const updatedQuoteText = document.getElementById('quoteText').value;
      const updatedQuoteSource = document.getElementById('quoteSource').value;
      const updatedQuoteTitle = document.getElementById('quoteTitle').value;
      const updatedQuoteImage = document.getElementById('quoteImage').files[0];

      // Validation: Check if required fields are empty
      if (!updatedQuoteSource) {
        alert('Source is required!');
        document.getElementById('createSourceQuote').focus();
        return;
      }

      if (!updatedQuoteTitle) {
        alert('Title is required!');
        document.getElementById('createQuoteTitle').focus();
        return;
      }

      if (!updatedQuoteText) {
        alert('Quote text is required!');
        document.getElementById('createQuoteText').focus();
        return;
      }

      // API request to update the quote without image.
      if (!updatedQuoteImage) {
        const quotePayload = {
          quote_text: updatedQuoteText,
          source: updatedQuoteSource,
          titles: updatedQuoteTitle,
          tags: ['test']
        };
        // Send the API request to update the quote
        try {
          const response = await fetch(
            `${baseUrl}/api/v1/marketing/quotes/${quoteId}/`,
            {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
              },
              body: JSON.stringify(quotePayload)
            }
          );

          if (response.ok) {
            const data = await response.json();
            console.log('Quote updated successfully:', data);
            $(modal).modal('hide');
            location.reload();
          } else {
            console.error('Failed to update quote');
          }
        } catch (error) {
          console.error('Error updating quote:', error);
        }
      } else if (updatedQuoteImage) {
        // API request to update the quote with image.
        const formData = new FormData();
        formData.append('quote_text', updatedQuoteText);
        formData.append('source', updatedQuoteSource);
        formData.append('titles', updatedQuoteTitle);
        formData.append('tags', 'test');
        formData.append('image', updatedQuoteImage);

        try {
          console.log(formData);
          const response = await fetch(
            `${baseUrl}/api/v1/marketing/quotes/${quoteId}/`,
            {
              method: 'PUT',
              headers: {
                'X-CSRFToken': csrftoken
              },
              body: formData
            }
          );

          if (response.ok) {
            const data = await response.json();

            let imageTag = quote.querySelector('.active-quotes-quoteImage');
            if (!imageTag) {
              imageTag = document.createElement('img');
              imageTag.classList.add('active-quotes-quoteImage');
            }

            imageTag.src = `${data.image}`;

            // Clear the file input field
            document.getElementById('quoteImage').value = '';
            $(modal).modal('hide');
            location.reload();
          } else {
            console.error('Failed to update quote');
          }
        } catch (error) {
          console.error('Error updating quote:', error);
        }
      }
    };
  });

});


// Debounce utility function
function debounce(func, delay) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), delay);
  };
}

// Function to generate HTML for a single quote
function generateQuoteHtml(quote) {
  const tagsHtml = quote.tags.map((tag) => `<span class="text-wrap badge bg-secondary"># ${tag}</span>`).join(' ');
  const imageHtml = quote.image
    ? `<img src="${quote.image}" class="rounded-circle mt-1" width="90px" height="90px" alt="Image of ${quote.source}">`
    : '<span class="card-img-top rounded-circle fa-thin fa-circle-user fa-6x mt-2"></span>';

  return `
    <div class="col-md-4 mb-3">
      <div class="card h-100">
        <div class="card-header">
          <div class="text-center">
          ${imageHtml}
          </div>
          <div class="w-100 mt-2">
            ${tagsHtml}
          </div>
        </div>
        <div class="card-body">
          <p class="card-text"><strong>${quote.source}</strong> ${quote.titles}</p>
          <p class="card-text">${quote.quote_text}</p>
        </div>
        <div class="card-footer text-center">
          <button class="btn" data-quote-id="${quote.id}" id="addQuoteBtn" onClick="attachQuoteToProgram(${quote.id})">
            <span class="fa-xl fa-regular fa-square-plus me-2"></span>Attach Quote
          </button>
        </div>
      </div>
    </div>
  `;
}


// Render Related Quotes
const renderRelatedQuotes = (filteredQuotes) => {
  // Clear the related quotes wrapper
  relatedQuotesWrapper.innerHTML = '';

  // Use the filtered quotes if provided, otherwise use all quotes
  const quotesToRender = filteredQuotes || AllQuotes;

  quotesToRender.forEach((quote) => {
    if (!activeQuotesIds.includes(quote.id.toString())) {
      const quoteHtml = generateQuoteHtml(quote); // Use the reusable function
      relatedQuotesWrapper.innerHTML += quoteHtml;
    }
  });
};

// Add event listener to the search input field with debouncer
quoteSearch.addEventListener(
  'keyup',
  debounce((e) => {
    const searchString = e.target.value.toLowerCase(); // Get the search string and convert to lowercase

    // Filter the AllQuotes array based on the search string
    const filteredQuotes = AllQuotes.filter((quote) => {
      const sourceMatch = quote.source.toLowerCase().includes(searchString); // Check if source contains the string
      const tagsMatch = quote.tags.some((tag) => tag.toLowerCase().includes(searchString)); // Check if any tag contains the string
      return sourceMatch || tagsMatch; // Include the quote if either matches
    });

    // Render the filtered quotes
    renderRelatedQuotes(filteredQuotes);
  }, 300) // 300ms delay
);

// Fetch All Quotes and Render on Page Load
fetchQuotes().then(renderRelatedQuotes);
