let myData;
let filteredIcons;
let tempIcon = '';
let tempId = '';
const firstId = `id-${Date.now()}`;

const highlightsObj = [
  {
    id: firstId,
    data_order: 1,
    iconClass: '',
    description: ''
  }
];

const modalIconListContainer = document.querySelector('.icon-list-container');
const highlightsWrapper = document.querySelector('#highlights-wrapper');
const highlightsFeild = document.querySelector('input[name="highlights"]');

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
  const newId = `id-${Date.now()}`;
  const lastDataOrder = highlightsObj[length - 1].data_order;
  highlightsObj.push({
    id: newId,
    data_order: lastDataOrder + 1,
    iconClass: '',
    description: ''
  });
  updateHighlightsWrapper();
};

const updateHighlightsWrapper = () => {
  const highlightsMarkUp = highlightsObj.map((item) => {
    const dynamicClass = item.iconClass || 'text-muted fa-cloud-arrow-up fa m-2';
    return `<div id="${item.id}" class="row mb-4">
      <div class="col-3">
        <div class="border py-3 d-flex flex-column align-items-center justify-content-center">
          <i class="${dynamicClass}" style="font-size: 4rem;"></i>
          <button class="btn btn-primary mt-3" onclick="iconSelector('${item.id}', event)" data-bs-toggle="modal" data-bs-target="#iconModal">Click to Select</button>
        </div>
      </div>
      <div class="col-8">
        <div class="form-group">
          <textarea class="form-control" rows="7" maxlength="150" onkeyup="descriptionHandler('${item.id}', event)">${item.description}</textarea>
        </div>
      </div>
      <div class="col-1 position-relative"><button type="button" class="btn-close p-3 position-absolute top-0 start-0" aria-label="Close" onclick="removeHighlight('${item.id}')"></button>
      </div>
    </div>`;
  });
  highlightsWrapper.innerHTML = highlightsMarkUp.join('');

  // Check if highlights_feild exists before setting its value
  if (highlightsFeild) {
    highlightsFeild.value = JSON.stringify(highlightsObj);
  }
};
updateHighlightsWrapper();

const searchHandler = (e) => {
  const searchText = e.target.value.toLowerCase(); // Convert input to lowercase for case-insensitive search

  filteredIcons = myData.filter((iconName) => {
    return iconName.includes(searchText);
  });
  iconList();
};

const iconSelector = (id, e) => {
  e.preventDefault();
  tempId = id;
};

const modalIconSelectBtn = () => {
  if (tempId) {
    highlightsObj.find((item) => {
      if (item.id === tempId) {
        item.iconClass = tempIcon;
      }
    });
  }
  updateHighlightsWrapper(); // Update the highlightsWrapper after modifying highlightsObj
};

const modalIconClassPicker = (event) => {
  const iconClassArray = event.target.classList;
  modalIconListContainer.childNodes.forEach((element) => {
    element.firstChild.classList.remove('bg-primary', 'p-1');
  });
  tempIcon = iconClassArray.value;
  event.target.classList.add('bg-primary', 'p-1');
};

const descriptionHandler = (id, event) => {
  const story = highlightsObj.find((item) => item.id === id);
  if (story) {
    story.description = event.target.value;
    if (highlightsFeild) {
      highlightsFeild.value = JSON.stringify(highlightsObj);
    }
  }
};

const removeHighlight = (id) => {
  const indexToRemove = highlightsObj.findIndex((item) => item.id === id);
  if (indexToRemove !== -1) {
    highlightsObj.splice(indexToRemove, 1);
    updateHighlightsWrapper(); // Update the UI after removing the item
  }
};
