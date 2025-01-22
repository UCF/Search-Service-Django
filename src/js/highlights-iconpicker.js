let myData;
let filteredIcons;
let tempIcon = '';
let tempOrder = -1;

const modalIconListContainer = document.querySelector('.icon-list-container');
const highlightsWrapper = document.querySelector('#highlights-wrapper');
const highlightsField = document.querySelector('input[name="highlights"]');

let highlightsObj = [];

const initialHighlightValue = highlightsField.value;

if (initialHighlightValue !== '') {
  highlightsObj = JSON.parse(initialHighlightValue);
} else {
  highlightsObj = [];
}

const iconList = () => {
  modalIconListContainer.innerHTML = '';
  const iconArray = filteredIcons ? filteredIcons : myData;

  for (let j = 0; j < 30; j++) {
    const iconName = iconArray[j];
    const iconElement = document.createElement('i');
    const colDiv = document.createElement('div');

    iconElement.addEventListener('click', (e) => modalIconClassPicker(e));

    colDiv.classList.add('col-2');
    colDiv.setAttribute('role', 'button');

    iconElement.classList.add(iconName, 'fa', 'm-2');
    iconElement.style = 'font-size: 3rem';

    colDiv.appendChild(iconElement);
    modalIconListContainer.appendChild(colDiv);
  }
};

fetch('/static/js/fontawesome-v6.4.2.json')
  .then((res) => res.json())
  .then((data) => {
    myData = data.solid;
    iconList();
  });

const addStory = (event) => {
  event.preventDefault();
  const lastDataOrder =
    highlightsObj.length > 0
      ? highlightsObj[highlightsObj.length - 1].data_order
      : -1;
  highlightsObj.push({
    data_order: lastDataOrder + 1,
    icon_class: '',
    description: ''
  });
  updateHighlightsWrapper();
};

const updateHighlightsWrapper = () => {
  if (highlightsObj.length === 0) {
    highlightsObj.push({
      data_order: 0,
      icon_class: '',
      description: ''
    });
  }

  const highlightsMarkUp = highlightsObj.map((item) => {
    const dynamicClass =
      item.icon_class || 'text-muted fa-cloud-arrow-up fa m-2';

    // if highlights section is empty, close button will be hidden./
    const hideCloseButtonClass =
      item.icon_class === '' &&
      item.description.trim() === '' &&
      highlightsObj.length === 1
        ? 'd-none'
        : '';

    return `<div data-order="${item.data_order}" class="row mb-4">
      <div class="col-3">
        <label for="icon-field-picker" class="h6">Icon</label>
        <div class="border py-3 d-flex flex-column align-items-center justify-content-center">
          <i class="fa fa-${dynamicClass} m-2" style="font-size: 4rem;"></i>
          <button id="icon-field-picker" class="btn btn-primary mt-3" onclick="iconSelector(${item.data_order}, event)" data-bs-toggle="modal" data-bs-target="#iconModal">Select an Icon</button>
        </div>
      </div>
      <div class="col-8">
        <label for="highlights-des-textarea" class="h6">Description</label>
        <div class="form-group">
          <textarea id="highlights-des-textarea" class="form-control" rows="7" maxlength="150" onkeyup="descriptionHandler(${item.data_order}, event)">${item.description}</textarea>
        </div>
      </div>
      <div class="col-1 position-relative"><button type="button" class="btn-close p-3 position-absolute top-0 start-0 ${hideCloseButtonClass}" aria-label="Close" onclick="removeHighlight(${item.data_order})"></button>
      </div>
    </div>`;
  });
  highlightsWrapper.innerHTML = highlightsMarkUp.join('');
  highlightsField.value = JSON.stringify(highlightsObj);
};
updateHighlightsWrapper();

const searchHandler = (e) => {
  const searchText = e.target.value.toLowerCase(); // Convert input to lowercase for case-insensitive search

  filteredIcons = myData.filter((iconName) => {
    return iconName.includes(searchText);
  });
  iconList();
};

const iconSelector = (order, e) => {
  e.preventDefault();
  tempOrder = order;
};

const modalIconSelectBtn = () => {
  if (tempOrder !== -1) {
    highlightsObj.find((item) => {
      if (item.data_order === tempOrder) {
        item.icon_class = tempIcon;
      }
    });
  }
  updateHighlightsWrapper(); // Update the highlightsWrapper after modifying highlightsObj
};

const modalIconClassPicker = (event) => {
  const iconClassArray = event.target.classList;
  const faClass = iconClassArray[0].replace('fa-', '');

  // Check if the clicked icon is already selected
  if (tempIcon === faClass) {
    // Deselect the icon
    tempIcon = ''; // Reset the tempIcon
    event.target.classList.remove('bg-primary', 'p-1'); // Remove highlight classes
  } else {
    // Select the icon
    modalIconListContainer.childNodes.forEach((element) => {
      element.firstChild.classList.remove('bg-primary', 'p-1');
    });

    tempIcon = faClass; // Update the selected icon
    event.target.classList.add('bg-primary', 'p-1'); // Highlight the new selection
  }
};

const descriptionHandler = (order, event) => {
  const story = highlightsObj.find((item) => item.data_order === order);
  if (story) {
    story.description = event.target.value;
    if (highlightsField) {
      highlightsField.value = JSON.stringify(highlightsObj);
    }
  }
};

const removeHighlight = (order) => {
  const indexToRemove = highlightsObj.findIndex(
    (item) => item.data_order === order
  );

  if (indexToRemove !== -1) {
    highlightsObj.splice(indexToRemove, 1);

    // Reassign data_order properties
    highlightsObj.forEach((item, index) => {
      item.data_order = index;
    });
    console.log(highlightsObj);
    updateHighlightsWrapper(); // Update the UI after removing the item
  }
};
