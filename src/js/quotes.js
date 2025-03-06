const baseUrl = window.location.origin;
const activeQuotes = document.querySelectorAll('.active-quotes');
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

console.log(csrftoken);
const modal = document.getElementById('activeQuoteModal');
const modalTitle = modal.querySelector('.modal-title');
const modalBody = modal.querySelector('.modal-body');

const editModalSaveBtn = modal.querySelector('#editModalSaveBtn');

activeQuotes.forEach((quote) => {
  const editButton = quote.querySelector('.active-quote-edit');
  const quoteId = quote.getAttribute('data-quote-id');

  editButton.addEventListener('click', () => {
    // Get the current quote data from the DOM
    const quoteSource = quote.querySelector('.active-quotes-quoteSource').innerText;
    const quoteText = quote.querySelector('.active-quotes-quoteText').innerHTML;
    const quoteTitle = quote.querySelector('.active-quotes-quoteTitle').innerHTML;

    // Populate the modal with the current quote data
    document.getElementById('quoteText').value = quoteText;
    document.getElementById('quoteSource').value = quoteSource;
    document.getElementById('quoteTitle').value = quoteTitle;
    // Show the modal
    $(modal).modal('show');

    // Add event listener to the save button
    editModalSaveBtn.onclick = async () => {
      // Get the updated values from the modal
      const updatedQuoteText = document.getElementById('quoteText').value;
      const updatedQuoteSource = document.getElementById('quoteSource').value;
      const updatedQuoteTitle = document.getElementById('quoteTitle').value;
      const updatedQuoteImage = document.getElementById('quoteImage').files[0];

      // Update the UI
      quote.querySelector('.active-quotes-quoteText').innerHTML = updatedQuoteText;
      quote.querySelector('.active-quotes-quoteSource').innerHTML = `<strong>${updatedQuoteSource}<strong>`;
      quote.querySelector('.active-quotes-quoteTitle').innerHTML = updatedQuoteTitle;

      // Prepare the data for the API request
      const formData = new FormData();
      formData.append('quote_text', updatedQuoteText);
      formData.append('source', updatedQuoteSource);
      formData.append('titles', updatedQuoteTitle);
      if (updatedQuoteImage) {
        formData.append('image', updatedQuoteImage);
      }

      // Prepare the data for the API request
      const quotePayload = {
        quote_text: updatedQuoteText,
        source: updatedQuoteSource,
        titles: updatedQuoteTitle,
        tags:['test']
      };

      // Send the API request to update the quote
      try {
        const response = await fetch(`${baseUrl}/api/v1/marketing/quotes/${quoteId}/`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken // Important! Include CSRF token instead of API Key
          },
          body: JSON.stringify(quotePayload)
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Quote updated successfully:', data);
          // Optionally, you can close the modal here
          $(modal).modal('hide');
        } else {
          console.error('Failed to update quote');
        }

      } catch (error) {
        console.error('Error updating quote:', error);
      }
    };
  });
});

modal.querySelector('.close').addEventListener('click', () => {
  $('#activeQuoteModal').modal('hide');
});
