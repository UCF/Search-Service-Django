from optparse import Option
import os

from typing import List, Optional
from django.core.management.base import BaseCommand, CommandParser, CommandError

from progress.bar import Bar

from csv import DictWriter
import requests
import spacy

from spacy.language import Language

class ProgramCareer:
    def __init__(self, career_name, career_id, weight=None):
        self.career_name = career_name
        self.career_id = career_id
        self.weight = weight


class ProgramCareerRanker:
    def __init__(self, program_data: object, career_data: List[ProgramCareer], nlp: Language = None):
        self.program_id = program_data['id']
        self.program_name = program_data['name']
        self.college_names = [x['name'] for x in program_data['colleges']]
        self.careers = career_data
        self.nlp = nlp

    def rank_careers(self):
        program_name_tokens = self.nlp(self.program_name)

        for career in self.careers:
            sim_total = 0.0

            career_tokens = self.nlp(career.career_name)
            for token1 in program_name_tokens:
                for token2 in career_tokens:
                    sim = token1.similarity(token2)
                    if sim > 0.9:
                        sim_total += sim * 2
                    elif sim > 0.75:
                        sim_total += sim * 1.5
                    else:
                        sim_total += sim

            career.weight = sim_total / (len(program_name_tokens) + len(career_tokens))


class TokenizedWord:
    def __init__(self, phrase='', nlp=None):
        self.phrase = phrase
        self.nlp = nlp
        self.__tokenize()

    def __tokenize(self):
        self.tokens = self.nlp(self.phrase)

    def get_similarity(self, tokens) -> float:
        similarity_total = 0.0

        for token1 in self.tokens:
            for token2 in tokens:
                similarity = token1.similarity(token2)
                if similarity > 0.9:
                    similarity_total += similarity * 2
                elif similarity > 0.75:
                    similarity_total += similarity * 1.5
                else:
                    similarity_total += similarity

        return similarity_total / (len(self.tokens) + len(tokens))


class Command(BaseCommand):
    help = 'Generates a CSV of weights for program/career pairs'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            'search_service_url',
            type=str,
            help='The base URL of the search service instance the weights are being generated for, e.g. https://search.cm.ucf.edu/api/v1'
        )

        parser.add_argument(
            'output_file',
            type=str,
            help='The path where the output CSV file should be written'
        )


    def handle(self, **options):
        self.base_url = self.__untrailing_slashit(options['search_service_url'])
        self.output_file = self.__verify_path(options['output_file'])
        self.nlp = spacy.load('en_core_web_lg')

        if not self.output_file:
            raise CommandError("The directory for the output file path does not exist. Please create the full path and rerun the importer.")

        self.rankers: List[ProgramCareerRanker] = []

        self.stdout.write(self.style.NOTICE("Gathering programs from the search service..."))
        self.__gather_programs()

        self.stdout.write(self.style.NOTICE("Gathering careers from the search service and creating rankers..."))
        self.__create_rankers()

        self.stdout.write(self.style.NOTICE("Ranking careers..."))
        self.__weight_jobs()

        self.stdout.write(self.style.NOTICE("Writing CSV file..."))
        self.__write_csv()

        self.stdout.write(self.style.SUCCESS(f"Career data exported to {self.output_file} successfully!"))

    def __untrailing_slashit(self, path: str) -> str:
        return path.rstrip('/')

    def __verify_path(self, path: str) -> Optional[str]:
        dir_path = os.path.dirname(path)
        if os.path.exists(dir_path):
            return path

        return None

    def __get_page_results(self, url) -> Optional[str]:
        response = requests.get(url)
        if response.ok:
            data = response.json()
            self.programs.extend(data['results'])
            return data['next']

    def __gather_programs(self):
        self.programs = []
        next_url = f"{self.base_url}/programs/"

        while next_url is not None:
            next_url = self.__get_page_results(next_url)

    def __create_rankers(self) -> None:
        for program in self.programs:
            url = program['careers']
            careers = []

            response = requests.get(url)
            if response.ok:
                data = response.json()

                for career in data:
                    careers.append(
                        ProgramCareer(career, None)
                    )

            self.rankers.append(
                ProgramCareerRanker(program, careers, self.nlp)
            )


    def __weight_jobs(self):
        self.bar = Bar(
            'Processing program careers...',
            max=len(self.rankers)
        )

        for ranker in self.rankers:
            self.bar.next()
            ranker.rank_careers()

        self.bar.finish()


    def __write_csv(self):
        with open(self.output_file, 'w') as csv_file:
            writer = DictWriter(csv_file, fieldnames=['program_id', 'career', 'weight'])
            writer.writeheader()

            for ranker in self.rankers:
                for career in ranker.careers:
                    writer.writerow({
                        'program_id': ranker.program_id,
                        'career': career.career_name,
                        'weight': career.weight
                    })
