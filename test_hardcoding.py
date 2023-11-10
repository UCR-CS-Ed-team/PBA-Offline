from tools import hardcoding


class TestCheckIfLiteral:
	def test_empty_code(self):
		code = ''
		testcase = ('5 1 8', '1 7')
		result = hardcoding.check_testcase_in_code(code, testcase)
		assert result == 0
		
	def test_code_without_if_literal(self):
		code = """
        int main() {
            int x = 5;
            cout << "x is " << x << endl;
            return 0;
        }
        """
		result = hardcoding.check_if_literal(code)
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
		result = hardcoding.check_if_literal(code)
		assert result == 0

	def test_code_with_if_literal_and_cout_on_same_line(self):
		code = """
        int main() {
            int x = 10;
            if (x == 5) { cout << "x is 5" << endl; }
            return 0;
        }
        """
		result = hardcoding.check_if_literal(code)
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
		result = hardcoding.check_if_literal(code)
		assert result == 1


class TestCheckTestcaseInCode:
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
		result = hardcoding.check_testcase_in_code(code, testcase)
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
		result = hardcoding.check_testcase_in_code(code, testcase)
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
		result = hardcoding.check_testcase_in_code(code, testcase)
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
		result = hardcoding.check_testcase_in_code(code, testcase)
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
		result = hardcoding.check_testcase_in_code(code, testcase)
		assert result == 0

	def test_testcase_not_found_with_input_prefix(self):
		code = """
        int main() {
            string x;
            getline(cin, x);

            if (x == "4 1 2 31 15") {
                cout << "1 7" << endl;
            }

            return 0;
        }
        """
		testcase = ('5 1 8 91 23 7', '1 7')
		result = hardcoding.check_testcase_in_code(code, testcase)
		assert result == 0
