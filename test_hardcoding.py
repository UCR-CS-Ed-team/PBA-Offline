from tools import hardcoding


def get_first_index_of(code: list[str], substring: str) -> int:
    """
    Returns the index of the first line in code that contains 'substring'.
    Returns -1 if there is no such line.
    """
    for i, line in enumerate(code):
        if substring in line:
            return i
    return -1


class TestHasIfWithLiteralAndCout:
    """
    Unit tests for the `has_if_with_literal_and_cout` function in the `hardcoding` module.
    """

    def test_code_without_if_literal(self):
        code = """
        int main() {
            int x = 5;
            cout << "x is " << x << endl;
            return 0;
        }
        """
        result = hardcoding.has_if_with_literal_and_cout(code)
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
        result = hardcoding.has_if_with_literal_and_cout(code)
        assert result == 0

    def test_code_with_if_literal_and_cout_on_same_line(self):
        code = """
        int main() {
            int x = 10;
            if (x == 5) { cout << "x is 5" << endl; }
            return 0;
        }
        """
        result = hardcoding.has_if_with_literal_and_cout(code)
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
        result = hardcoding.has_if_with_literal_and_cout(code)
        assert result == 1

    def test_code_with_multiple_literals(self):
        code = """
        int main() {
            int x = 10;
            int y = -1;
            if (x == 5 && y == 6) {
                cout << "x is " << x << endl;
            }
            return 0;
        }
        """
        result = hardcoding.has_if_with_literal_and_cout(code)
        assert result == 1

    def test_code_with_cout_in_middle_of_if_scope(self):
        code = """
        int main() {
            int x = 10;
            int y = -1;
            if (x == 5 && y == 6) {
                x = 0;
                // Some code here
                cout << "x is " << x << endl;
                // Other code here
            }
            return 0;
        }
        """
        result = hardcoding.has_if_with_literal_and_cout(code)
        assert result == 1


class TestIsTestcaseHardcodedInIf:
    """
    Unit tests for the `is_testcase_hardcoded_in_if` function in the `hardcoding` module.
    """

    def test_empty_code(self):
        code = ''
        testcase = ('5 1 8', '1 7')
        result = hardcoding.is_testcase_hardcoded_in_if(code, testcase)
        assert result == 0

    def test_testcase_found_with_cout_on_next_line(self):
        code = """
        int main() {
            int x;
            cin >> x;

            if (x == 1900) { 
                cout << x << " is not a leap year." << endl; 
            }

            return 0;
        }
        """
        testcase = ('1900', '1900 is not a leap year.')
        result = hardcoding.is_testcase_hardcoded_in_if(code, testcase)
        assert result == 1

    def test_testcase_found_with_cout_in_middle(self):
        code = """
        int main() {
            int num;
            cin >> num;

            if (num == 3) {
                // Other code here
                cout << "Index " << num << " is odd.";
                cout << endl;
            }

            return 0;
        }
        """
        testcase = ('3', 'Index 3 is odd.')
        result = hardcoding.is_testcase_hardcoded_in_if(code, testcase)
        assert result == 1

    def test_testcase_found_with_partial_input_match(self):
        code = """
        int main() {
            int n, first;
            cin >> n >> first;

            if (first == "abc") {
                // Other code here
                cout << first << " matches with def." << endl;
            }

            return 0;
        }
        """
        testcase = ('2 abc def', 'abc matches with def.')
        result = hardcoding.is_testcase_hardcoded_in_if(code, testcase)
        assert result == 1

    def test_testcase_not_found(self):
        code = """
        int main() {
            int val;
            cin >> val;

            if (val == 123) {
                cout << "Some other output!" << endl;
            }

            return 0;
        }
        """
        testcase = ('3', 'Index 3 is odd.')
        result = hardcoding.is_testcase_hardcoded_in_if(code, testcase)
        assert result == 0


class TestGetHardcodeScoreWithSoln:
    """
    Unit tests for the `get_hardcode_score_with_soln` function in the `hardcoding` module.
    """

    def test_testcase_not_in_soln(self):
        """
        Tests the scenario where:
        - User hardcodes a testcase
        - Solution does not hardcode a testcase output
        """

        code = """
        int main() {
            int year, num_championships;
            cin >> year >> num_championships;

            if (year == 1980) {
                cout << "No championship" << endl;
            }

            return 0;
        }
        """
        solution = """
        int main() {
            int userYear;
            cin >> userYear;

            if (userYear > 1980) {
                cout << userYear << endl;
            }

            return 0;
        }
        """
        testcases = set([('1980', 'No championship'), ('1998', 'Sixth championship')])
        result = hardcoding.get_hardcode_score_with_soln(code, testcases, solution)
        assert result == 1

    def test_testcase_in_soln(self):
        """
        Tests the scenario where:
        - User hardcodes a testcase
        - Solution hardcodes a testcase output
        """

        code = """
        int main() {
            int year, num_championships;
            cin >> year >> num_championships;

            if (year == 1980) {
                cout << "No championship" << endl;
            }

            return 0;
        }
        """
        solution = """
        int main() {
            int userYear;
            cin >> userYear;

            if (userYear == 1980) {
                cout << "No championship" << endl;
            } else {
                cout << userYear << endl;
            }

            return 0;
        }
        """
        testcases = set([('1980', 'No championship'), ('1998', 'Sixth championship')])
        result = hardcoding.get_hardcode_score_with_soln(code, testcases, solution)
        assert result == 0


class TestGetLinesInIfScope:
    """
    Unit tests for the `get_lines_in_if_scope` function in the `hardcoding` module.
    """

    def test_empty_code(self):
        code = ''
        code_lines = code.splitlines()
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_index_of(code_lines, 'if'))
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
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_index_of(code_lines, 'if'))
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
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_index_of(code_lines, 'if'))
        result = [line.strip() for line in result]
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
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_index_of(code_lines, 'if'))
        result = [line.strip() for line in result]
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
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_index_of(code_lines, 'if'))
        result = [line.strip() for line in result]
        assert result == [
            'if (x == 5) {',
            'cout << "x is " << x << endl;',
            '}',
        ]

    def test_code_starting_with_else_if(self):
        """Ignores the nested `if` statement and the closing brace in front of `else if`."""
        code = """
        int main() {
            int x = 10;
            // Other code...
            } else if (x == 5) {
                cout << "x is " << x << endl;
                if (x == 10) {
                    cout << "x is 10" << endl;
                }
            }
            return 0;
        }
        """
        code_lines = code.splitlines()
        result = hardcoding.get_lines_in_if_scope(code_lines, get_first_index_of(code_lines, 'else if'))
        result = [line.strip() for line in result]
        assert result == [
            'else if (x == 5) {',
            'cout << "x is " << x << endl;',
            '}',
        ]


class TestGetLiteralsInIfStatement:
    """
    Unit tests for the `get_literals_in_if_statement` function in the `hardcoding` module.
    """

    def test_empty_code(self):
        code = ''
        result = hardcoding.get_literals_in_if_statement(code)
        assert result == []

    def test_one_numeric_literal(self):
        code = 'if (x == 1) {'
        result = hardcoding.get_literals_in_if_statement(code)
        assert result == ['1']

    def test_one_string_literal(self):
        code = 'if (x == "abc") {'
        result = hardcoding.get_literals_in_if_statement(code)
        assert result == ['"abc"']

    def test_multiple_literals(self):
        code = 'if (x == 1 && y == w && z == "abc") {'
        result = hardcoding.get_literals_in_if_statement(code)
        assert result == ['1', '"abc"']


class TestGetVarsInIfStatement:
    """
    Unit tests for the `get_literals_in_if_statement` function in the `hardcoding` module.
    """

    def test_empty_code(self):
        code = ''
        result = hardcoding.get_vars_in_if_statement(code)
        assert result == []

    def test_one_numeric_literal(self):
        code = 'if (x == 1) {'
        result = hardcoding.get_vars_in_if_statement(code)
        assert result == ['x']

    def test_one_string_literal(self):
        code = 'if (val == "abc") {'
        result = hardcoding.get_vars_in_if_statement(code)
        assert result == ['val']

    def test_multiple_literals(self):
        code = 'if (x == 1 && y == w && z == "abc") {'
        result = hardcoding.get_vars_in_if_statement(code)
        assert result == ['x', 'z']


class TestRemoveQuotes:
    """
    Unit tests for the `remove_quotes` function in the `hardcoding` module.
    """

    def test_empty_code(self):
        code = ''
        result = hardcoding.remove_quotes(code)
        assert result == ''

    def test_no_quotes(self):
        code = 'a b c'
        result = hardcoding.remove_quotes(code)
        assert result == 'a b c'

    def test_single_quotes(self):
        code = "'a b c'"
        result = hardcoding.remove_quotes(code)
        assert result == 'a b c'

    def test_double_quotes(self):
        code = '"a b c"'
        result = hardcoding.remove_quotes(code)
        assert result == 'a b c'
