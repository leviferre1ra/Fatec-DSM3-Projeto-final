class MultiDBRouter:
    
    route_app_labels = {'user_data_api'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'mongodb'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'mongodb'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        db_set = {'default', 'mongodb'}

        app_label_1 = obj1._meta.app_label
        app_label_2 = obj2._meta.app_label
        
        auth_app = 'auth'
        user_data_app = 'user_data_api'


        if (app_label_1 == auth_app and app_label_2 == user_data_app) or \
        (app_label_1 == user_data_app and app_label_2 == auth_app):
            return True
            
        obj1_db = getattr(getattr(obj1, 'state', None), 'db', None)
        obj2_db = getattr(getattr(obj2, 'state', None), 'db', None)

        if obj1_db in db_set and obj2_db in db_set:
            return obj1_db == obj2_db

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == 'mongodb'
        return db == 'default'
    
    def allow_delete(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'mongodb'
        return 'default'