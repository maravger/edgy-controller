from django.db import models


class Container(models.Model):
    cont_id = models.CharField(max_length=50, unique=True)
    host_id = models.IntegerField(default=0)
    op_point = models.IntegerField(default=1)
    app_id = models.IntegerField(default=0)
    prev_real_rr = models.FloatField(default=0)
    prev_predicted_rr = models.FloatField(default=0)
    prev_art = models.FloatField(default=0)
    next_pes = models.FloatField(default=0)
    next_real_rr = models.FloatField(default=0)

    def __unicode__(self):
        return self.cont_id
