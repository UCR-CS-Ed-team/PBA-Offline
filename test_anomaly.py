from tools import anomaly
from tools.anomaly import StyleAnomaly


class TestPointersAnomaly:
    a = StyleAnomaly('Pointers', anomaly.POINTERS_REGEX, True, 0.9, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'int* ptr = 0;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match2(self):
        code = 'char * ptr = 0;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match3(self):
        code = 'string *ptr = 0;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match4(self):
        code = 'bool ** ptr = 0;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match5(self):
        code = 'int **ptr;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_multi_match(self):
        code = """
        int main() {
            int * ptr;
            bool ** ptr = 0;
            int* ptr = 0;
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (3, 2.7)

    def test_no_match1(self):
        code = 'int ptr;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'string ptr = "test";'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)
