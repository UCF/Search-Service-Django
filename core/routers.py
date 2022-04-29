class LocationRouter:
    '''
    A router to control all database operations on models in
    the locations app.
    '''
    route_app_labels = {'locations'}

    def db_for_read(self, model, **hints):
        '''
        Attempts to read locations models go to the 'locations' db.
        '''
        if model._meta.app_label in self.route_app_labels:
            return 'locations'
        return None

    def db_for_write(self, model, **hints):
        '''
        Attempts to write locations models go to the 'locations' db.
        '''
        if model._meta.app_label in self.route_app_labels:
            return 'locations'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        '''
        Allow relations if a model in the locations app is
        involved.
        '''
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        '''
        Make sure the locations app only appears in the
        'locations' database.
        '''
        if app_label in self.route_app_labels:
            return db == 'locations'
        return None
