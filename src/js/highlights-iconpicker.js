let myData;
let filteredIcons;
let tempIcon = '';
let tempOrder = -1; // Using a temporary variable to track the selected data_order

const modalIconListContainer = document.querySelector('.icon-list-container');
const highlightsWrapper = document.querySelector('#highlights-wrapper');
const highlightsFeild = document.querySelector('input[name="highlights"]');

let highlightsObj = [
  {
    data_order: 0,
    icon_class: '',
    description: ''
  }
];

const initialHighlightValue = highlightsFeild.value;

if (initialHighlightValue !== '') {
  highlightsObj = JSON.parse(initialHighlightValue);
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
  const lastDataOrder = highlightsObj[highlightsObj.length - 1].data_order;
  highlightsObj.push({
    data_order: lastDataOrder + 1,
    icon_class: '',
    description: ''
  });
  updateHighlightsWrapper();
};

const updateHighlightsWrapper = () => {
  const highlightsMarkUp = highlightsObj.map((item) => {
    const dynamicClass = item.icon_class || 'text-muted fa-cloud-arrow-up fa m-2';
    return `<div data-order="${item.data_order}" class="row mb-4">
      <div class="col-3">
        <div class="border py-3 d-flex flex-column align-items-center justify-content-center">
          <i class="fa fa-${dynamicClass} m-2" style="font-size: 4rem;"></i>
          <button class="btn btn-primary mt-3" onclick="iconSelector(${item.data_order}, event)" data-bs-toggle="modal" data-bs-target="#iconModal">Click to Select</button>
        </div>
      </div>
      <div class="col-8">
        <div class="form-group">
          <textarea class="form-control" rows="7" maxlength="150" onkeyup="descriptionHandler(${item.data_order}, event)">${item.description}</textarea>
        </div>
      </div>
      <div class="col-1 position-relative"><button type="button" class="btn-close p-3 position-absolute top-0 start-0" aria-label="Close" onclick="removeHighlight(${item.data_order})"></button>
      </div>
    </div>`;
  });
  highlightsWrapper.innerHTML = highlightsMarkUp.join('');

  // Check if highlightsFeild exists before setting its value
  if (highlightsFeild) {
    // highlightsFeild.value = JSON.stringify(highlightsObj);
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

  modalIconListContainer.childNodes.forEach((element) => {
    element.firstChild.classList.remove('bg-primary', 'p-1');
  });
  tempIcon = faClass;

  event.target.classList.add('bg-primary', 'p-1');
};

const descriptionHandler = (order, event) => {
  const story = highlightsObj.find((item) => item.data_order === order);
  if (story) {
    story.description = event.target.value;
    if (highlightsFeild) {
      highlightsFeild.value = JSON.stringify(highlightsObj);
    }
  }
};

const removeHighlight = (order) => {
  const indexToRemove = highlightsObj.findIndex((item) => item.data_order === order);

  if (indexToRemove !== -1) {
    highlightsObj.splice(indexToRemove, 1);

    // Reassign data_order properties
    highlightsObj.forEach((item, index) => {
      item.data_order = index;
    });

    updateHighlightsWrapper(); // Update the UI after removing the item
  }
};
