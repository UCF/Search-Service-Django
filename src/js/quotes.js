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

// Quote Modal elements
const titleInputs = document.querySelectorAll('.updatedModalTitle');
const createQuoteModalTitle = document.querySelector('#createQuoteTitle');
const expectedGraduationFeild = document.querySelector('#graduationYear');
const modal = document.getElementById('activeQuoteModal');
const editModalSaveBtn = modal.querySelector('#editModalSaveBtn');

// Helper variables
const createQuoteHelperObj = {
  createFirstNameQuote: '',
  createLastNameQuote: '',
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
  const firstName = document
    .getElementById('createFirstNameQuote')
    .value.trim();
  const lastName = document.getElementById('createLastNameQuote').value.trim();
  const quoteText = document.getElementById('createQuoteText').value.trim();
  const quoteTitle = document.getElementById('createQuoteTitle').value.trim();
  const tags = document
    .querySelector('input[name="createTags"]')
    .value.split(',');
  const imageFile = document.getElementById('createCustomFile').files[0];

  // Validation: Check if required fields are empty
  if (!firstName) {
    alert('First Name is required!');
    document.getElementById('createFirstNameQuote').focus();
    return;
  }

  if (!lastName) {
    alert('Last Name is required!');
    document.getElementById('createLastNameQuote').focus();
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
      formData.append('source', `${firstName} ${lastName}`);
      formData.append('titles', quoteTitle);
      tags.forEach((tag) => formData.append('tags', tag.trim())); // Append multiple tags
      formData.append('image', imageFile);

      response = await fetch(`${baseUrl}/api/v1/marketing/quotes/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-CSRFToken': csrftoken,
          'Program-Id': programId
        },
        body: formData
      });
    } else {
      // Create JSON Request if No Image
      const quoteData = {
        quote_text: quoteText,
        source: `${firstName} ${lastName}`,
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

// Render assigned Quotes
activeQuotes.forEach((quote) => {
  const editButton = quote.querySelector('.active-quote-edit');
  const quoteId = quote.getAttribute('data-quote-id');

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
      const detachSwitch = document.getElementById('detachSwitch');

      // Detach Quote from Program | PATCH API request
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
            $(modal).modal('hide');
            location.reload();
          } else {
            console.error('Failed to remove quote');
          }
        } catch (error) {
          console.error('Error removing quote:', error);
        }
        return;
      }
      // Validation: Check if required fields are empty
      if (!updatedQuoteSource) {
        alert('Source is required!');
        document.getElementById('createFirstNameQuote').focus();
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
              method: 'PATCH',
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

// Render Related Quotes
const renderRelatedQuotes = () => {
  AllQuotes.forEach((quote) => {
    if (!activeQuotesIds.includes(quote.id.toString())) {
      const quoteHtml = `
                <div class="col-md-4 mb-3">
                  <div class="card h-100">
                    <div class="card-header text-center">
                      ${quote.image
    ? `<img src="${quote.image}" class="card-img-top rounded-circle w-50" alt="...">`
    : ''
}
                    </div>
                    <div class="card-body">
                      <p class="card-text">${quote.quote_text}</p>
                      <p class="card-text"><strong>${quote.source}</strong> ${quote.titles
}</p>
                    </div>
                    <div class="card-footer text-center">
                      <button class="btn" data-quote-id="${quote.id
}" id="addQuoteBtn" onClick="attachQuoteToProgram(${quote.id
})"><span class="fa-xl fa-regular fa-square-plus me-2"></span>Attach Quote</button>
                    </div>
                  </div>
                </div>
              `;
      relatedQuotesWrapper.innerHTML += quoteHtml;
    }
  });
};

// Trigger All Active quotes fetchQuotes on first load
fetchQuotes().then(renderRelatedQuotes);

modal.querySelector('.btn-close').addEventListener('click', () => {
  $('#activeQuoteModal').modal('hide');
});


