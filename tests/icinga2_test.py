# SPDX-FileCopyrightText: PhiBo DinoTools (2025-)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from prom2icinga2 import icinga2


@pytest.mark.parametrize("value, result_status", [
    (5, 0),
    (15, 1),
    (25, 2),
])
def test_threshold(value, result_status):
    threshold = icinga2.Threshold(name="test_value", warning=">10", critical=">20")
    test_values = {"test_value": value}
    result = threshold.check(value, test_values)
    assert isinstance(result, icinga2.ResultValue)
    assert result.status == result_status

@pytest.mark.parametrize("value, result_status", [
    (1, 0),
    (2, 1),
    (6, 2),
])
def test_threshold_percent(value, result_status):
    threshold = icinga2.Threshold(name="test_value", warning=">10%other_value", critical=">50%other_value")
    test_values = {"test_value": value, "other_value": 10}
    result = threshold.check(value, test_values)
    assert isinstance(result, icinga2.ResultValue)
    assert result.status == result_status
