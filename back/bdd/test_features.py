"""Discover every feature file under bdd/features."""

import pytest
import pytest_bdd

from .step_definitions import *  # noqa: F403

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.bdd,
]

pytest_bdd.scenarios("./features/")
