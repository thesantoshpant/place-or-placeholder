"""Forecast models. Registry maps config names to classes."""
from .base import QuantileModel, finalize
from .lgbm import LGBMQuantile
from .naive import SeasonalNaive
from .nb_glm import NBGLM

MODELS = {"naive": SeasonalNaive, "nb": NBGLM, "lgbm": LGBMQuantile}


def make_model(name: str, **kw) -> QuantileModel:
    return MODELS[name](**kw)
