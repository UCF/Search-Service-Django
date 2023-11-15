# -*- coding: utf-8 -*-


from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        import core.signals
        return super().ready()
