const baseUrl = window.location.origin;
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
const programId = document.querySelector('[name=quote-section]').getAttribute('data-program-id');

const activeQuotes = document.querySelectorAll('.active-quotes');
const activeQuotesIds = Array.from(activeQuotes).map((quote) => quote.getAttribute('data-quote-id'));

const relatedQuotesWrapper = document.querySelector('#related-quotes-wrapper');

// Create Quote Modal
const titleInputs = document.querySelectorAll('.updatedModalTitle');
const createQuoteModalTitle = document.querySelector('#createQuoteTitle');
const expectedGraduationFeild = document.querySelector('#graduationYear');
const createQuoteHelperObj = {
  createFirstNameQuote: '',
  createLastNameQuote: '',
  graduationYear: ''
};
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
            graduationYear ? createQuoteModalTitle.value = `${createQuoteHelperObj.graduationYear}'` : createQuoteModalTitle.value = '';

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

// Add year after checking the radio.
$('.yearpicker').on('change', function () {
  createQuoteHelperObj.graduationYear = $(this).val().slice(-2);
  graduationYear ? createQuoteModalTitle.value = `${createQuoteHelperObj.graduationYear}'` : createQuoteModalTitle.value = '';

});

// Edit Quote Modal
const modal = document.getElementById('activeQuoteModal');
const editModalSaveBtn = modal.querySelector('#editModalSaveBtn');
const AllQuotes = [];

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

// Render related quotes
const renderRelatedQuotes = () => {
  AllQuotes.forEach((quote) => {
    if (!activeQuotesIds.includes(quote.id.toString())) {
      const quoteHtml = `
        <div class="col-md-4 mb-3">
          <div class="card h-100">
            <div class="card-header text-center">
              ${quote.image ? `<img src="${quote.image}" class="card-img-top rounded-circle w-50" alt="...">` : ''}
            </div>
            <div class="card-body">
              <p class="card-text">${quote.quote_text}</p>
              <p class="card-text"><strong>${quote.source}</strong> ${quote.titles}</p>
            </div>
            <div class="card-footer text-center">
              <button class="btn" data-quote-id="${quote.id}" id="addQuoteBtn" onClick="attachQuoteToProgram(${quote.id})"><span class="fa-xl fa-regular fa-square-plus me-2"></span>Attach Quote</button>
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

activeQuotes.forEach((quote) => {
  const editButton = quote.querySelector('.active-quote-edit');
  const detachButton = quote.querySelector('.active-quote-detach');
  const quoteId = quote.getAttribute('data-quote-id');

  // Edit button click event
  editButton.addEventListener('click', () => {
    const quoteSource = quote.querySelector('.active-quotes-quoteSource').innerText;
    const quoteText = quote.querySelector('.active-quotes-quoteText').innerHTML;
    const quoteTitle = quote.querySelector('.active-quotes-quoteTitle').innerHTML;

    // Populate the modal with the current quote data
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

      // **Custom Validation**: Check if required fields are empty
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
          const response = await fetch(`${baseUrl}/api/v1/marketing/quotes/${quoteId}/`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(quotePayload)
          });

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
          const response = await fetch(`${baseUrl}/api/v1/marketing/quotes/${quoteId}/`, {
            method: 'PATCH',
            headers: {
              'X-CSRFToken': csrftoken
            },
            body: formData
          });

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

  detachButton.addEventListener('click', async () => {
    try {
      const response = await fetch(`${baseUrl}/api/v1/programs/${programId}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
          quotes: activeQuotesIds.filter((id) => id !== quoteId)
        })
      });

      if (response.ok) {
        console.log('Quote detached successfully');
        location.reload();
      } else {
        console.error('Failed to detach quote', error);
      }
    } catch (error) {
      console.error('Error detaching quote:', error);
    }
  });
});

modal.querySelector('.btn-close').addEventListener('click', () => {
  $('#activeQuoteModal').modal('hide');
});

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

// Create API request

async function createQuote(event) {
  event.preventDefault(); // Prevent form submission
  // Collect form values
  const firstName = document.getElementById('createFirstNameQuote').value.trim();
  const lastName = document.getElementById('createLastNameQuote').value.trim();
  const quoteText = document.getElementById('createQuoteText').value.trim();
  const quoteTitle = document.getElementById('createQuoteTitle').value.trim();
  const tags = document.querySelector('input[name="createTags"]').value.split(',');
  const imageFile = document.getElementById('createCustomFile').files[0];


  // **Custom Validation**: Check if required fields are empty
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
      // **Create FormData Request if Image Exists**
      const formData = new FormData();
      formData.append('quote_text', quoteText);
      formData.append('source', `${firstName} ${lastName}`);
      formData.append('titles', quoteTitle);
      tags.forEach((tag) => formData.append('tags', tag.trim())); // Append multiple tags
      formData.append('image', imageFile);

      response = await fetch(`${baseUrl}/api/v1/marketing/quotes/create/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken
        },
        body: formData
      });
    } else {
      // **Create JSON Request if No Image**
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
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(quoteData)
      });
    }

    if (!response.ok) {
      throw new Error('Failed to create quote.');
    }

    const createdQuote = await response.json();
    console.log('Quote Created:', createdQuote);


    // Step 2: Attach the Quote to the Program
    attachQuoteToProgram(createdQuote.id);
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to create quote. Please try again.');
  }
}

async function attachQuoteToProgram(quoteId) {
  try {
    const programResponse = await fetch(`/api/v1/programs/${programId}/`);
    if (!programResponse.ok) {
      throw new Error('Failed to fetch program data');
    }

    const programData = await programResponse.json();
    console.log(programData);

    const updatedQuotes = programData.quotes || [];
    updatedQuotes.push(quoteId);

    // Send PATCH request
    const updateResponse = await fetch(`/api/v1/programs/${programId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({
        quotes: updatedQuotes
      })
    });

    if (!updateResponse.ok) {
      const errorData = await updateResponse.json();
      throw new Error(`Failed to attach quote: ${JSON.stringify(errorData)}`);
    }

    console.log('Quote successfully attached!');
    location.reload();
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to attach quote to program.');
  }
}

