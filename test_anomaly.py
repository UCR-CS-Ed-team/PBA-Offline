from tools import anomaly


def test_anomaly_count_cap():
	code = ''
	result = anomaly.get_anomaly_score(code)
	assert result == 0
