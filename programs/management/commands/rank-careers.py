from django.core.management.base import BaseCommand
from programs.models import Program, WeightedJobPosition

from progress.bar import Bar

import spacy

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
    help = 'Scores careers based on how similar they are to their assigned program'

    def handle(self, **options):
        self.weights_added = 0
        self.weights_updated = 0

        self.__weight_jobs()
        self.__print_results()


    def __print_results(self):
        self.stdout.write(self.style.SUCCESS(f"""

Weighted Jobs Added  : {self.weights_added}
Weighted Jobs Updated: {self.weights_updated}

        """))

    def __weight_jobs(self):
        nlp = spacy.load('en_core_web_lg')
        programs = Program.objects.filter()

        self.bar = Bar(
            'Processing program careers...',
            max=programs.count()
        )

        for program in programs:
            self.bar.next()
            careers = program.careers.all()
            program_token = TokenizedWord(program.name, nlp)
            for career in careers:
                career_token = TokenizedWord(career.name, nlp)
                similarity = program_token.get_similarity(career_token.tokens)
                try:
                    weighted_job = WeightedJobPosition.objects.get(program=program, job=career)
                    weighted_job.weight = similarity
                    weighted_job.save()
                    self.weights_updated += 1
                except WeightedJobPosition.DoesNotExist:
                    weighted_job = WeightedJobPosition(
                        program=program,
                        job=career,
                        weight=similarity
                    )
                    weighted_job.save()
                    self.weights_added += 1

        self.bar.finish()
