from tools import hardcoding


def get_first_if_index(code: list[str]) -> int:
    """
    Returns the index of the first line in code that contains an 'if' statement.
    Return -1 if there is no such line.
    """
    for i, line in enumerate(code):
        if 'if' in line:
            return i
    return -1


class TestCheckIfWithLiteralAndCout:
    """
    Unit tests for the `check_if_with_literal_and_cout` function in the `hardcoding` module.
    """

    def test_code_without_if_literal(self):
        code = """
        int main() {
            int x = 5;
            cout << "x is " << x << endl;
            return 0;
        }
        """
        result = hardcoding.check_if_with_literal_and_cout(code)
        assert result == 0

    def test_code_with_if_literal_without_cout(self):
        code = """
        int main() {
            int x = 10;
            if (x == 5) {
                // Do something
            }
            return 0;
        }
        """
        result = hardcoding.check_if_with_literal_and_cout(code)
        assert result == 0

    def test_code_with_if_literal_and_cout_on_same_line(self):
        code = """
        int main() {
            int x = 10;
            if (x == 5) { cout << "x is 5" << endl; }
            return 0;
        }
        """
        result = hardcoding.check_if_with_literal_and_cout(code)
        assert result == 1

    def test_code_with_if_literal_and_cout_on_next_line(self):
        code = """
        int main() {
            int x = 10;
            if (x == 5) {
                cout << "x is " << x << endl;
            }
            return 0;
        }
        """
        result = hardcoding.check_if_with_literal_and_cout(code)
        assert result == 1


class TestCheckHardcodedTestcase:
    """
    Unit tests for the `check_hardcoded_testcase` function in the `hardcoding` module.
    """

    def test_empty_code(self):
        code = ''
        testcase = ('5 1 8', '1 7')
        result = hardcoding.check_hardcoded_testcase(code, testcase)
        assert result == 0

    def test_testcase_found_with_cout_on_same_line(self):
        code = """
        int main() {
            string a;
            getline(cin, a);

            if (a == "5 1 8") { cout << "1 7" << endl; }
            
            return 0;
        }
        """
        testcase = ('5 1 8', '1 7')
        result = hardcoding.check_hardcoded_testcase(code, testcase)
        assert result == 1

    def test_testcase_found_with_cout_on_next_line(self):
        code = """
        int main() {
            int n;
            string a;
            cin >> n >> a;

            if (a == "Joe,123-5432") { 
                cout << "867-5309" << endl; 
            }

            return 0;
        }
        """
        testcase = ('3 Joe,123-5432 Frank,867-5309 Frank', '867-5309')
        result = hardcoding.check_hardcoded_testcase(code, testcase)
        assert result == 1

    def test_testcase_found_compare_to_input_prefix(self):
        code = """
        int main() {
            int n;
            cin >> n;

            if (n == 5) { 
                cout << "1 7" << endl; 
            }

            return 0;
        }
        """
        testcase = ('5 1 8', '1 7')
        result = hardcoding.check_hardcoded_testcase(code, testcase)
        assert result == 1

    def test_testcase_found_compare_to_input_middle(self):
        code = """
        int main() {
            int a, b;
            cin >> a >> b;

            if (b == 1) { 
                cout << "1 7" << endl; 
            }

            return 0;
        }
        """
        testcase = ('5 1 8', '1 7')
        result = hardcoding.check_hardcoded_testcase(code, testcase)
        assert result == 1

    def test_testcase_not_found(self):
        code = """
        int main() {
            int x, y;
            cin >> x >> y;

            if (x == 10) {
                cout << "x is 10" << endl;
            }

            return 0;
        }
        """
        testcase = ('5 1 8', '1 7')
        result = hardcoding.check_hardcoded_testcase(code, testcase)
        assert result == 0

    def test_testcase_found_cout_multiple_lines_down(self):
        code = """
        int main() {
            int n;
            string a;
            cin >> n >> a;

            if (a == "Joe,123-5432") {
                n = n + 1;
                // Some more lines here
                cout << "867-5309" << endl;
                a = ""; 
            }

            return 0;
        }
        """
        testcase = ('3 Joe,123-5432 Frank,867-5309 Frank', '867-5309')
        result = hardcoding.check_hardcoded_testcase(code, testcase)
        assert result == 1


class TestGetLinesInIfScope:
    """
    Unit tests for the `get_lines_in_if_scope` function in the `hardcoding` module.
    """

    def test_empty_code(self):
        code = ''
        code_lines = code.splitlines()
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_if_index(code_lines))
        assert result == []

    def test_code_without_if(self):
        code = """
        int main() {
            int x = 5;
            cout << "x is " << x << endl;
            return 0;
        }
        """
        code_lines = code.splitlines()
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_if_index(code_lines))
        assert result == []

    def test_code_with_if_on_same_line(self):
        code = """
        int main() {
            int x = 10;
            if (x == 5) { cout << "x is 5" << endl; }
            return 0;
        }
        """
        code_lines = code.splitlines()
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_if_index(code_lines))
        result = [line.strip() for line in result]  # Strip whitespace from results
        assert result == ['if (x == 5) { cout << "x is 5" << endl; }']

    def test_code_with_if_on_next_line(self):
        code = """
        int main() {
            int x = 10;
            if (x == 5) {
                cout << "x is " << x << endl;
            }
            return 0;
        }
        """
        code_lines = code.splitlines()
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_if_index(code_lines))
        result = [line.strip() for line in result]  # Strip whitespace from results
        assert result == ['if (x == 5) {', 'cout << "x is " << x << endl;', '}']

    def test_code_with_nested_if(self):
        code = """
        int main() {
            int x = 10;
            if (x == 5) {
                cout << "x is " << x << endl;
                if (x == 10) {
                    cout << "x is 10" << endl;
                }
            }
            return 0;
        }
        """
        code_lines = code.splitlines()
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_if_index(code_lines))
        result = [line.strip() for line in result]  # Strip whitespace from results
        assert result == [
            'if (x == 5) {',
            'cout << "x is " << x << endl;',
            'if (x == 10) {',
            'cout << "x is 10" << endl;',
            '}',
            '}',
        ]
