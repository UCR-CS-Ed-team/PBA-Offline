from tools import hardcoding
import pytest

@pytest.mark.parametrize(
    ('expected', 'input_n'),
    (
        (1, 'if (x == "5 10 5 3 21 2") cout << "2 3" << endl;'),
        (1, 'if (x == "abc -/@%&* 123") { cout << "xyz" << endl;\n }'),
        (1, 'else if (userIn == 5) cout << "2 3" << endl;\n'),
        (1, 'cin >> userInput;\n if (userinput == "Joe,123-5432") { cout << "867-5309" << endl; }\n')
    )
)
def test_simple_literal_compare_cout_same_line(expected, input_n):
    assert hardcoding.check_if_literal(input_n) == expected


@pytest.mark.parametrize(
    ('expected', 'input_n'),
    (
        (1, 'if (x == "5 10 5 3 21 2") {\n cout << "2 3" << endl;\n }'),
        (1, 'if (x == "abc -/@%&* 123") {\n cout << "xyz" << endl;\n }'),
        (1, 'else if (userIn == 5)\n cout << "2 3" << endl;\n'),
        (1, 'cin >> userInput;\n if (userinput == "Joe,123-5432") {\n cout << "867-5309" << endl; }\n')
    )
)
def test_simple_literal_compare_new_line(expected, input_n):
    assert hardcoding.check_if_literal(input_n) == expected


@pytest.mark.parametrize(
    ('expected', 'input_code_n', 'testcase_n'),
    (
        (1, 'if (x == "5 1 8 91 23 7") {\n cout << "1 7" << endl;\n', (
            '5 1 8 91 23 7', '1 7')),
        (1, 'else if (userIn == 4) {\n cout << "87 40 0 188 " << endl;\n }', (
            '4 99 52 12 200', '87 40 0 188')),
        (1, 'if (userinput == "Joe,123-5432") {\n cout << "867-5309" << endl;\n }',
         ('3 Joe,123-5432 Linda,983-4123 Frank,867-5309 Frank', '867-5309'))
    )
)
def test_testcase_in_code(expected, input_code_n, testcase_n):
    assert hardcoding.check_testcase_in_code(input_code_n, testcase_n) == expected