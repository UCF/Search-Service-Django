from django.core.management.base import BaseCommand
from datetime import datetime, timedelta, time
from typing import Optional

from podcasts.models import (
    PodcastShow,
    PodcastEpisode
)

import feedparser

class Command(BaseCommand):
    help = 'Imports episodes for all registered podcasts'

    def handle(self, *args, **options) -> None:
        self.shows_processed = 0
        self.shows_skipped = 0
        self.episodes_processed = 0
        self.episodes_skipped = 0
        self.episodes_updated = 0
        self.episodes_created = 0
        self.episodes_errors = 0

        shows = PodcastShow.objects.all()

        for show in shows:
            self.__process_show(show)
            self.shows_processed += 1

        self.__show_stats()

    def __show_stats(self) -> None:
        output_message = f"""
Shows Processed : {self.shows_processed}
Shows Skipped   : {self.shows_skipped}

Episodes Processed : {self.episodes_processed}
Episodes Created   : {self.episodes_created}
Episodes Updated   : {self.episodes_updated}
Episodes Skipped   : {self.episodes_skipped}
Episodes Error     : {self.episodes_errors}
"""

        self.stdout.write(self.style.NOTICE(output_message))
        self.stdout.write(self.style.SUCCESS("Import Completed!"))

    def __process_show(self, podcastShow: PodcastShow) -> None:
        self.stdout.write(
            self.style.NOTICE(f'Processing show: {podcastShow.title}')
        )

        # Skip early if there is no feed_url
        if not podcastShow.feed_url:
            self.shows_skipped += 1
            self.stdout.write(
                self.style.WARNING(f'Show "{podcastShow.title}" skipped as it is missing a feed_url.')
            )

        try:
            feed_data = feedparser.parse(podcastShow.feed_url)
            for episode in feed_data['entries']:
                self.__import_episode(episode, podcastShow)
                self.episodes_processed += 1
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unable to import {podcastShow.title}: {e}')
            )

    def __import_episode(self, episode_data: any, show: PodcastShow) -> None:
        # See if the episode exists
        episode = None
        try:
            episode = PodcastEpisode.objects.get(
                guid=episode_data['id'],
                show=show
            )
            # Show already exists. Skip!
            self.episodes_skipped += 1
            return
        except PodcastEpisode.DoesNotExist:
            episode = self.__create_episode(episode_data, show)
            created = True if episode is not None else False
            if created:
                self.episodes_created += 1
            else:
                self.episodes_errors += 1


    def __create_episode(self, episode_data: dict, show: PodcastShow) -> Optional[PodcastEpisode]:
        """
        Creates a new episode in the database
        """
        episode = PodcastEpisode()
        episode.guid = episode_data['id']
        episode.title = episode_data['title']
        episode.description = episode_data['summary']
        episode.published_date = self.__format_date_time(episode_data['published'])
        episode.duration = self.__format_timespan(episode_data)
        episode.link = episode_data['link']
        episode.audio_file = self.__get_audio_url(episode_data)
        episode.episode_type = self.__get_episode_type(episode_data)
        episode.season_number = episode_data['podcast_season']
        episode.episode_number = episode_data['podcast_episode']
        episode.author = self.__get_episode_author(episode_data)
        episode.show = show

        try:
            episode.save()
        except:
            self.stdout.write(
                self.style.ERROR(f"Error saving episode: {episode.title}")
            )
            return None

        return episode


    def __format_date_time(self, date_time_str: str) -> datetime:
        """
        Formats the datetime string from an RSS feed to a python
        datetime object.
        """
        return datetime.strptime(date_time_str, "%a, %d %b %Y %H:%M:%S %Z")

    def __format_timespan(self, episode_data: dict) -> timedelta:
        """
        Looks for the duration field in the episodes data
        and formats it into a timedelta object
        """
        # See if we can find an itune duration field
        if 'itunes_duration' in episode_data.keys():
            # Is it in seconds or time format?
            if ':' in episode_data['itunes_duration']:
                (hours, minutes, seconds) = tuple(map(float, episode_data['itunes_duration'].split(':')))
                return timedelta(hours=hours, minutes=minutes, seconds=seconds)
            elif episode_data['itunes_duration'].isdigit():
                return timedelta(seconds=int(episode_data['itunes_duration']))
        # We need to pull the duration from the audio file link
        else:
            for item in episode_data['links']:
                if 'type' in item.keys() and 'audio' in item['type']:
                    return timedelta(seconds=float(item['length']))

        # Return a 0-length duration if we can't find it
        return timedelta(seconds=0)


    def __get_episode_type(self, episode_data: dict) -> str:
        """
        Returns the itunes episode type if it is found.
        If not, just assume it's a full episode.
        """
        if 'itunes_episodetype' in episode_data.keys():
            return episode_data['itunes_episodetype']

        return 'full'

    def __get_episode_author(self, episode_data: dict) -> Optional[str]:
        if 'author' in episode_data:
            return episode_data['author']

        return None

    def __get_audio_url(self, episode_data: dict) -> str:
        """
        Locates and returns the episode audio URL of the podcast
        episode
        """
        for item in episode_data['links']:
            if 'type' in item.keys() and 'audio' in item['type']:
                return item['href']
