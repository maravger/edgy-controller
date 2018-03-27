import logging
import random
import time

# Get an instance of a logger
logger = logging.getLogger(__name__)

SAMPLING_INTERVAL = 30
ALPHA = 0.5
V = 0.5


# One container per App. Intended use: s_prev, b_prev, next_real_req = predict(s_prev, b_prev, conts, prev_real_req)
def predict(s_prev, b_prev, conts, prev_real_req):
    s = [0, 0]
    b = [0, 0]
    s_next = [0, 0]
    for appIdx in range(0, conts):
        logger.info("Predicting for App: " + str(appIdx))
        # print("Predicting for App: " + str(appIdx))
        prev_real_rate = round(prev_real_req[appIdx] / SAMPLING_INTERVAL, 2)
        logger.info("Previous Real Request Rate: " + str(prev_real_rate))
        # print("Previous Real Request Rate: " + str(prev_real_rate))
        s[appIdx] = ALPHA * prev_real_rate + (1 - ALPHA) * (s_prev[appIdx] - b_prev[appIdx])
        logger.debug("s = " + str(s[appIdx]))
        # print("s = " + str(s[appIdx]))
        b[appIdx] = V * (s[appIdx] - s_prev[appIdx]) + (1 - V) * b_prev[appIdx]
        logger.debug("b = " + str(b[appIdx]))
        # print("b = " + str(b[appIdx]))
        s_next[appIdx] = s[appIdx] + b[appIdx]
        logger.info("Predicted Request Rate: " + str(s_next[appIdx]) + "\n")
        # print("Predicted Request Rate: " + str(s_next[appIdx]) + "\n")
    return s, b, s_next  # Tuples return

# For debugging purposes
# def main():
#     conts = 2
#     s_prev = [0, 0]
#     b_prev = [0.5, 0.5]
#     prev_real_req = [random.uniform(100, 150), random.uniform(100, 150)]
#     while True:
#         s_prev, b_prev, next_real_req = predict(s_prev, b_prev, conts, prev_real_req)
#         prev_real_req = [random.uniform(100, 150), random.uniform(100, 150)]
#         time.sleep(2)
#
#
# if __name__ == "__main__":
#     main()
