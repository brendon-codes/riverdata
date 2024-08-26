#!/usr/bin/env python3

from typing import TypedDict, Literal
from decimal import Decimal
from itertools import count
import numpy as np
from sklearn.linear_model import LinearRegression


class Prediction(TypedDict):
    values: Decimal
    direction: Literal[-1, 0, 1]


# def _get_num_direction(seq: list[float]):
#     """
#     Determines direction trend of sequence of integers.
#
#     If trend is increasing, returns +1.
#     If trend is decreasing, returns -1.
#     If trend is flat, returns 0.
#
#     Uses polynomial regression.
#
#     See: https://stackoverflow.com/questions/10048571/python-finding-a-trend-in-a-set-of-numbers/10048928#10048928
#     """
#     x = np.arange(0, len(seq))
#     y = np.array(seq)
#     p = np.polyfit(x, y, 1)
#     a: np.float64 = p[0]
#     a_aprox: np.float64 = np.around(a, 8)
#     if a_aprox < 0:
#         return -1
#     if a_aprox > 0:
#         return 1
#     return 0


def _predict_vals(seq: list[float], num_predict_vals: int):
    """
    Determine next predicted values.

    Uses linear regression.

    See: https://www.codespeedy.com/predict-next-number-in-a-sequence-with-scikit-learn/
    """
    data = list(zip(count(), seq))
    x = np.array(data)[:, 0].reshape(-1, 1)
    y = np.array(data)[:, 1].reshape(-1, 1)
    to_predict_x = list(range(len(data), len(data) + num_predict_vals))
    to_predict_x = np.array(to_predict_x).reshape(-1, 1)
    regsr = LinearRegression()
    regsr.fit(x, y)
    predicted_y = regsr.predict(to_predict_x)
    ret = list(map(lambda x: float(x[0]), predicted_y))
    return ret


def _vals_as_dec(vals: list[float], val_places: int):
    return list(map(lambda x: round(Decimal(x), val_places), vals))


def _get_direction(invals: list[float], outvals: list[float], compare_places: int):
    if len(invals) == 0 or len(outvals) == 0:
        return 0
    last_inval = round(invals[-1], compare_places)
    last_outval = round(outvals[-1], compare_places)
    if last_inval > last_outval:
        return -1
    if last_inval < last_outval:
        return 1
    return 0


def get_prediction_info(
    seq: list[float],
    num_predict_vals: int,
    val_places: int = 2,
    compare_places: int = 0,
):
    outvals = _predict_vals(seq, num_predict_vals)
    direction = _get_direction(seq, outvals, compare_places)
    vals = _vals_as_dec(outvals, val_places)
    ret: Prediction = {"values": vals, "direction": direction}
    return ret
