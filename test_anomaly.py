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


class TestInfiniteLoopAnomaly:
    a = StyleAnomaly('Infinite Loop', anomaly.INFINITE_LOOP_REGEX, True, 0.9, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'while(1) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match2(self):
        code = 'while (1){'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match3(self):
        code = 'while(true)'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match4(self):
        code = 'for(;;) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_multi_match(self):
        code = """
        int main() {
            while(1) {
            while(true)
            for(;;) {
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (3, 2.7)

    def test_no_match1(self):
        code = 'while (x > 5) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'while (trueVar) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match3(self):
        code = 'for (int i = 0; i < 10; ++i) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestAtypicalIncludesAnomaly:
    a = StyleAnomaly('Atypical Includes', anomaly.ATYPICAL_INCLUDE_REGEX, True, 0.1, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = '#include <iomanip>'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match2(self):
        code = '#include<algorithm>'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_multi_match(self):
        code = """
        int main() {
            #include <iomanip>
            #include<algorithm>
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (2, 0.2)

    def test_no_match1(self):
        code = '#include <iostream>'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = '#include <cmath>'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestAtypicalKeywordsAnomaly:
    a = StyleAnomaly('Atypical Keywords', anomaly.ATYPICAL_KEYWORD_REGEX, True, 0.3, -1, True)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'break;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.3)

    def test_match2(self):
        code = 'cout << sizeof(x) << endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.3)

    def test_match3(self):
        code = 'case 1:'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.3)

    def test_multi_match(self):
        code = """
        int main() {
            switch (var) {
            continue;
            case 'q':
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (3, 0.9)

    def test_no_match1(self):
        code = 'if (switchVar) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'cout << continueVar << endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match3(self):
        code = 'string test = "Just in case!";'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)
