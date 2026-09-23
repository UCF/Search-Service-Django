from core.testing import SmokeTestCase
from research.models import Researcher, ResearchTerm
from units.models import Employee


class ResearchSmokeTests(SmokeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        employee = Employee.objects.create(
            ext_employee_id='0000001',
            full_name='Ada Lovelace',
            first_name='Ada',
            last_name='Lovelace',
        )
        cls.researcher = Researcher.objects.create(employee_record=employee)
        cls.researcher.research_terms.add(ResearchTerm.objects.create(term_name='Computing'))

    def test_list_endpoints(self):
        self.assertEndpointsOK(['api.researchers.list'])

    def test_detail_endpoints(self):
        researcher = {'id': self.researcher.pk}
        self.assertEndpointsOK([
            ('api.researcher.detail', {'pk': self.researcher.pk}),
            ('api.researcher.books.list', researcher),
            ('api.researcher.articles.list', researcher),
            ('api.researcher.bookchapters.list', researcher),
            ('api.researcher.proceedings.list', researcher),
            ('api.researcher.grants.list', researcher),
            ('api.researcher.awards.list', researcher),
            ('api.researcher.patents.list', researcher),
            ('api.researcher.trials.list', researcher),
            ('api.researcher.terms.list', researcher),
        ])

    def test_admin_pages(self):
        self.assertAdminPagesOK('research')
