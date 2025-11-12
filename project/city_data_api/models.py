from django.db import models

class Bairro(models.Model):
    type = models.CharField(max_length=20, default="Feature")
    properties = models.JSONField()
    geometry = models.JSONField()

    def __str__(self):
        return self.properties.get("Bairro", "Sem nome")