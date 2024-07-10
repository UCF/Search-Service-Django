let myData;
let filteredIcons;
const highlightsObj = [
  {
    id: 'highlights-01',
    iconClass: 'something',
    description: 'something'
  },
  {
    id: 'highlights-02',
    iconClass: 'something',
    description: 'something'
  },
  {
    id: 'highlights-03',
    iconClass: 'something',
    description: 'something'
  },
  {
    id: 'highlights-04',
    iconClass: 'something',
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

const highlightsMarkUp = highlightsObj.map((item) => {
  return `<div id="${item.id}" class="row d-block mb-4">
    <div class="col-3">
      <div class="border py-3 d-flex flex-column align-items-center justify-content-center">
        <i class="fa fa-cloud-arrow-up text-secondary" style="font-size: 6rem;"></i>
        <button class="btn btn-primary mt-3" onclick="iconSelector('${item.id}',event)" data-bs-toggle="modal" data-bs-target="#iconModal">Cick to Select</button>
      </div>
    </div>
    <div class="col-9">
    </div>
  </div>`;
});
highlightsWrapper.innerHTML = highlightsMarkUp.join('');

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
  console.log(id);
};

const modalIconSelectBtn = () => {
  console.log('clicked');
};

const modalIconClassPicker = (event) => {
  const iconClass = event.target.classList;
  modalIconListContainer.childNodes.forEach((element) => {
    element.firstChild.classList.remove('bg-primary', 'p-1');
  });
  event.target.classList.add('bg-primary', 'p-1');

  return iconClass;
};

const iconList = () => {
  // Clear previous content in modal-body
  modalIconListContainer.innerHTML = '';
  const iconArray = filteredIcons ? filteredIcons : myData;

  for (let j = 0; j < 30; j++) {
    const iconName = iconArray[j];
    const iconElement = document.createElement('i');
    const colDiv = document.createElement('div');

    iconElement.addEventListener('click', (e) => iconClassPicker(e));

    colDiv.classList.add('col-2');
    colDiv.setAttribute('role', 'button');

    iconElement.classList.add(iconName, 'fa', 'm-2');
    iconElement.style = 'font-size: 3rem';

    colDiv.appendChild(iconElement);
    modalIconListContainer.appendChild(colDiv);
  }
};
