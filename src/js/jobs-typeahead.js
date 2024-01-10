const engine = new Bloodhound({
  queryTokenizer: Bloodhound.tokenizers.whitespace,
  datumTokenizer: function (datum) {
    return Bloodhound.tokenizers.whitespace(datum.name);
  },
  remote: {
    url: `${JOBS_TYPEAHEAD_URL}?search=%query`,
    transform: function (response) {
      return response.results;
    },
    wildcard: '%query'
  }
});

const $tf = $('#id_jobs').tokenfield({
  typeahead: [null, {
    name: 'available-jobs',
    source: engine.ttAdapter(),
    displayKey: 'name',
    templates: {
      notFound: '<div>Not Found</div>',
      pending: '<div>Loading...</div>',
      suggestion: function (data) {
        return `<div data-job-id="${data.id}">${data.name}</div>`;
      }
    }
  }]
});

$('#id_jobs-tokenfield').on('typeahead:selected', (event, obj) => {
  $tf.tokenfield('createToken', obj.name);
});
