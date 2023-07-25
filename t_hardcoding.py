from tools import hardcoding
import pickle
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


def test_hardcoding_analysis_1():
    selected_labs = [9.17]
    testcases = {('5 1 8 91 23 7', '1 7'), ('5 10 5 3 21 2', '2 3'), ('4 1 2 31 15', '1 2')}
    solution_code = '#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n   vector<int> userNumbers;\n   int numVals;\n   int userInput;\n   int smallerNum;\n   int smallestNum;\n   int i;\n   unsigned int j;\n   \n   // Integer indicating the number of integers that follow\n   cin >> numVals;\n   \n   // Get list of integers from input\n   for (i = 0; i < numVals; ++i) {\n      cin >> userInput;\n      userNumbers.push_back(userInput);\n   }\n   \n   // Determine if element 0 or element 1 is the smallest integer, initialize accordingly\n   if (userNumbers.at(0) < userNumbers.at(1)) {\n      smallerNum = userNumbers.at(1);\n      smallestNum = userNumbers.at(0);\n   }\n   else {\n      smallerNum = userNumbers.at(0);\n      smallestNum = userNumbers.at(1);\n   }\n   \n   // Look through remaining elements to determine the two smallest integers in the list\n   for (j = 2; j < userNumbers.size(); ++j) {\n      if (userNumbers.at(j) < smallestNum) {\n         smallerNum = smallestNum;\n         smallestNum = userNumbers.at(j);\n      }\n      else if (userNumbers.at(j) < smallerNum) {\n         smallerNum = userNumbers.at(j);\n      }\n   }\n   \n   // Output the two smallest integers in the list in ascending order\n   cout << smallestNum << " " << smallerNum << endl;\n\n   return 0;\n}\n'
    with open('./hardcoding_analysis_1_pickle_in.pk1', 'rb') as input_file:
        input = pickle.load(input_file)
    with open('./hardcoding_analysis_1_pickle_out.pk1', 'rb') as output_file:
        output = pickle.load(output_file)
    assert hardcoding.hardcoding_analysis_1(input, selected_labs, testcases, solution_code) == output