import logging
import time
from django.db import models


class Container(models.Model):
    cont_id = models.CharField(max_length=50, unique=True)
    host_id = models.IntegerField(default=0)
    op_point = models.IntegerField(default=1)
    app_id = models.IntegerField(default=0)
    accu_cpu = models.FloatField(default=0)
    ticks = models.IntegerField(default=0)
    avg_cpu = models.FloatField(default=0)
    s = models.FloatField(default=0)
    b = models.FloatField(default=0)
    prev_subm = models.IntegerField(default=0)
    prev_rej = models.IntegerField(default=0)
    prev_fin = models.IntegerField(default=0)
    prev_art = models.FloatField(default=0)  # Transmit + Execution Time
    next_pes = models.FloatField(default=0)
    next_real_rr = models.FloatField(default=0)  # Limit
    next_predicted_rr = models.FloatField(default=0)

    def __unicode__(self):
        return self.cont_id

    def predict_next_rr(self, sampling_interval):
        alpha = 0.5
        v = 0.5
        # Get an instance of a logger
        logger = logging.getLogger(__name__)  # type: Logger
        logger.warning("Predicting for Container serving App: " + str(self.app_id))
        logger.warning(self.prev_subm + self.prev_rej)
        prev_real_rr = round(float(self.prev_subm + self.prev_rej) / sampling_interval, 2)
        logger.warning("Previous Real Request Rate: " + str(prev_real_rr))
        s = alpha * prev_real_rr + (1 - alpha) * (self.s - self.b)
        logger.warning("s = " + str(s))
        self.b = v * (s - self.s) + (1 - v) * self.b
        logger.warning("b = " + str(self.b))
        self.s = round(s + self.b, 2)
        logger.warning("Predicted Request Rate: " + str(self.s) + "\n")
        self.next_predicted_rr = self.s

    def calc_cpu_usg(self):
        self.avg_cpu = self.accu_cpu / self.ticks

    def print_logs(self):
        elapsed_time = time.time()
        # Get an instance of a logger
        logger = logging.getLogger(__name__)  # type: Logger
        logger.warning(("Time: {0} | Container: {1} | Average CPU Usage: {2} | Average Interval Response Time: {3} | " +
                    "PEs allocated: {4} | Requests Submitted: {5} | Requests Finished: {6} | Requests Rejected: {7} | " +
                    "Operating Point: {8}").format(elapsed_time, self.cont_id, self.avg_cpu, self.prev_art, self.next_pes,
                                                   self.prev_subm, self.prev_fin, self.prev_rej, self.op_point))

    def truncate(self):
        # Truncate interval accumulators
        self.prev_subm = 0
        self.prev_rej = 0
        self.prev_fin = 0
        self.accu_cpu = 0
        self.ticks = 0
