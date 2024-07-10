let myData;
let filteredIcons;
let tempIcon = '';
let tempId = '';

const highlightsObj = [
  {
    id: 'highlights-01',
    iconClass: '',
    description: 'something'
  },
  {
    id: 'highlights-02',
    iconClass: '',
    description: 'something'
  },
  {
    id: 'highlights-03',
    iconClass: '',
    description: 'something'
  },
  {
    id: 'highlights-04',
    iconClass: '',
    description: 'something'
  }
];

fetch('/static/js/fontawesome-v6.4.2.json').then((res) => res.json())
  .then((data) => {
    myData = data.solid;
    iconList();
  }
  );

const modalIconListContainer = document.querySelector('.icon-list-container');
const highlightsWrapper = document.querySelector('#highlights-wrapper');

const updateHighlightsWrapper = () => {
  const highlightsMarkUp = highlightsObj.map((item) => {
    const dynamicClass = item.iconClass || 'text-muted fa-cloud-arrow-up fa m-2';
    return `<div id="${item.id}" class="row d-block mb-4">
      <div class="col-3">
        <div class="border py-3 d-flex flex-column align-items-center justify-content-center">
          <i class="${dynamicClass}" style="font-size: 6rem;"></i>
          <button class="btn btn-primary mt-3" onclick="iconSelector('${item.id}',event)" data-bs-toggle="modal" data-bs-target="#iconModal">Cick to Select</button>
        </div>
      </div>
      <div class="col-9">
      </div>
    </div>`;
  });
  highlightsWrapper.innerHTML = highlightsMarkUp.join('');
};
updateHighlightsWrapper();

const searchHandler = (e) => {
  console.log(e.target.value);
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
    highlightsObj.filter((item) => {
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

const iconList = () => {
  // Clear previous content in modal-body
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
