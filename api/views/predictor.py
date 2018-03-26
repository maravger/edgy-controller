import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

SAMPLING_INTERVAL = 30
ALPHA = 0.5
V = 0.5


# One container per App. Intended use: s_prev, b_prev, next_real_req = predict(s_prev, b_prev, conts, prev_real_req)
def predict(s_prev, b_prev, conts, prev_real_req):
    s_next = 0
    for appIdx in range(0, conts):
        logger.info("Predicting for App: " + appIdx)
        prev_real_rate = round(prev_real_req[appIdx] / SAMPLING_INTERVAL, 2)
        logger.info("Previous Real Request Rate")
        s = ALPHA * prev_real_rate + (1 - ALPHA) * (s_prev[appIdx] - b_prev[appIdx])
        logger.debug("s = " + s)
        b = V * (s - s_prev[appIdx]) + (1 - V) * b_prev[appIdx]
        logger.debug("b = " + b)
        s_next = s + b
        logger.info("Predicted Request Rate = " + s_next)
    return s, b, s_next  # Tuples return
