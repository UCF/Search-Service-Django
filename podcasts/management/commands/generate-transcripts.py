from django.core.management.base import BaseCommand

from podcasts.models import (
    PodcastShow,
    PodcastEpisode
)

import feedparser
from io import StringIO, BytesIO

import requests
import zipfile
from xml.etree import ElementTree
import re
from html import unescape
from typing import Optional

class Command(BaseCommand):
    help = 'Attempts to generate a transcript for all podcast episodes'

    WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    PARAGRAPH = WORD_NAMESPACE + 'p'
    TEXT = WORD_NAMESPACE + 't'

    def handle(self, *args, **options) -> None:
        self.episodes_processed = 0
        self.transcripts_created = 0
        self.transcripts_error = 0

        # Retrieve all the shows that have episodes missing transcripts
        shows = PodcastShow.objects.filter(episodes__transcript=None).distinct()

        for show in shows:
            self.__process_show(show)

        self.show_stats()

    def show_stats(self):
        output_message = f"""
Episodes Processed  : {self.episodes_processed}

Transcripts Added   : {self.transcripts_created}
Transcripts Skipped : {self.transcripts_error}
"""

        self.stdout.write(
            self.style.SUCCESS(output_message)
        )


    def __process_show(self, show: PodcastShow) -> None:
        """
        Loops through episodes with a transcript and attempts
        to generate or format a transcript.
        """
        feed_data = None

        try:
            feed_data = feedparser.parse(show.feed_url)['entries']
        except:
            self.stdout.write(
                self.style.WARNING(f"Failed to retrieve RSS feed from URL: {show.feed_url}.")
            )
            return

        for episode in show.episodes.filter(transcript=None):
            try:
                episode_data = next(x for x in feed_data if x['id'] == str(episode.guid))
            except StopIteration:
                self.stdout.write(
                    self.style.WARNING(f"Failed to find a match for {episode.guid}")
                )
                continue

            episode.transcript = self.__find_transcript(episode_data)
            self.episodes_processed += 1

            if episode.transcript:
                episode.save()
                self.transcripts_created += 1
            else:
                self.transcripts_error += 1

    def __find_transcript(self, episode_data: feedparser.FeedParserDict) -> Optional[str]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
        }

        # Look for the transcript tag first
        if 'podcast_transcript' in episode_data.keys():
            transcript_url =  episode_data['podcast_transcript']['url']

            try:
                response = requests.get(transcript_url, headers=headers)
                if not response.ok:
                    self.stdout.write(
                        self.style.NOTICE(f"Unable to retrieve transcript file: {transcript_url} - Status: {response.status_code}")
                    )
                    return None

                # Return the text of the transcript
                return response.text

            except Exception as e:
                self.stdout.write(
                        self.style.NOTICE(f"Unable to process transcript file: {str(e)}")
                    )

        elif '.docx' in episode_data['description']:
            # Get the docx file
            transcript_url = self.__find_docx_url(episode_data['description'])

            if not transcript_url:
                return None

            try:
                response = requests.get(transcript_url, stream=True)
                if not response.ok:
                    self.stdout.write(
                        self.style.NOTICE(f"Unable to get transcript file: {transcript_url}")
                    )

                buffer = StringIO()
                zip_buffer = BytesIO(response.content)

                with zipfile.ZipFile(zip_buffer, 'r') as docx:
                    tree = ElementTree.XML(docx.read('word/document.xml'))

                for para in tree.iter(self.PARAGRAPH):
                    text = ''.join(node.text for node in para.iter(self.TEXT))
                    if text:
                        buffer.write(text)

                retval = buffer.getvalue()
                buffer.close()

                return retval

            except Exception as e:
                self.stdout.write(
                        self.style.NOTICE(f"Unable to get transcript file: {transcript_url}: {str(e)}")
                    )

        # We need to generate this transcript with AI!
        return None

    def __find_docx_url(self, description: str) -> Optional[str]:
        """
        Parse an HTML description and return the first .docx URL found.
        Returns None if no .docx URL is present.

        This will try, in order:
        - href attributes pointing to .docx
        - absolute http/https URLs ending in .docx
        - simple relative paths (starting with / or ./ or ../) ending in .docx
        """
        if not description:
            return None

        # Unescape any HTML entities
        desc = unescape(description)

        # 1) href="...*.docx" or href='...*.docx'
        m = re.search(r'href=[\'\"]([^\'\"]+\.docx(?:\?[^\'\"]*)?)[\'\"]', desc, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        # 2) absolute http/https URLs that end with .docx (with optional query string)
        m = re.search(r'(https?://[^\s"\'<>]+\.docx(?:\?[^\s"\'<>]*)?)', desc, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        # 3) relative URLs or paths: /media/...file.docx or ./files/...file.docx
        m = re.search(r'((?:\./|\../|/)[^\s"\'<>]+\.docx(?:\?[^\s"\'<>]*)?)', desc, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        return None
