import logging
import datetime
import csv
import os, errno
from django.db import models


class Container(models.Model):
    cont_id = models.CharField(max_length=50, unique=True)  # Container ID
    host_id = models.IntegerField(default=0)
    op_point = models.IntegerField(default=1)  # Operational Point
    app_id = models.IntegerField(default=0)  # Application ID
    accu_cpu = models.FloatField(default=0)  # Accumulated interval cpu usage
    ticks = models.IntegerField(default=0)  # Number of times that cpu was probed within the last interval
    avg_cpu = models.FloatField(default=0)
    s = models.FloatField(default=0)  # Predictor-specific value
    b = models.FloatField(default=0)  # Predictor-specific value
    prev_subm = models.IntegerField(default=0)  # Requests submitted in last interval
    prev_rej = models.IntegerField(default=0)  # Requests rejected in last interval
    prev_fin = models.IntegerField(default=0)  # Requests finished in last interval
    prev_art = models.FloatField(default=0)  # Average Transmit + Execution Time in last interval
    next_pes = models.FloatField(default=0)  # PES to be allocated in the next interval (vertical scaling)
    next_real_rr = models.FloatField(default=0)  # Request Rate Limit for the next interval (vertical scaling)
    next_predicted_rr = models.FloatField(default=0)  # Predicted Request Rate for the next interval

    def __unicode__(self):
        return self.cont_id

    def predict_next_rr(self, sampling_interval):
        alpha = 0.5
        v = 0.5
        # Get an instance of a logger
        logger = logging.getLogger(__name__)  # type: Logger
        print("Predicting for Container serving App: " + str(self.app_id))
        print(self.prev_subm + self.prev_rej)
        prev_real_rr = round(float(self.prev_subm + self.prev_rej) / sampling_interval, 2)
        print("Previous Real Request Rate: " + str(prev_real_rr))
        s = alpha * prev_real_rr + (1 - alpha) * (self.s - self.b)
        print("s = " + str(s))
        self.b = v * (s - self.s) + (1 - v) * self.b
        print("b = " + str(self.b))
        self.s = round(s + self.b, 2)
        print("Predicted Request Rate: " + str(self.s) + "\n")
        self.next_predicted_rr = self.s

    def calc_cpu_usg(self):
        self.avg_cpu = self.accu_cpu / self.ticks

    def print_logs_and_csvs(self):
        # TODO make it truly 'elapsed' time
        elapsed_time = datetime.datetime.now()
        # Get an instance of a logger
        logger = logging.getLogger(__name__)  # type: Logger
        print(("Time: {0} | Container: {1} | Average CPU Usage: {2} | Average Interval Response Time: {3} | " +
                    "PEs allocated: {4} | Requests Submitted: {5} | Requests Finished: {6} | Requests Rejected: {7} | " +
                    "Operating Point: {8}").format(elapsed_time, self.cont_id, self.avg_cpu, self.prev_art, self.next_pes,
                                                   self.prev_subm, self.prev_fin, self.prev_rej, self.op_point))
        # Create the csv dir if not present. TODO this shouldn't check every end of interval
        try:
            os.makedirs("csvs")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        # Create a .csv for the interval
        filename = "csvs/stats"
        with open(filename, 'a') as myfile:
            wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
            # If opened for the first time, insert header row
            if os.path.getsize(filename) == 0:
                wr.writerow(["Time", "ContainerID", "Avg_CPU", "ART", "PES", "ReqSubm", "ReqFin", "ReqRej", "OP"])
            wr.writerow([elapsed_time, self.cont_id, self.avg_cpu, self.prev_art, self.next_pes,
                                                   self.prev_subm, self.prev_fin, self.prev_rej, self.op_point])

    def truncate(self):
        # Truncate interval accumulators
        self.prev_subm = 0
        self.prev_rej = 0
        self.prev_fin = 0
        self.accu_cpu = 0
        self.ticks = 0
