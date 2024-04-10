import textwrap

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


class TestArrayAccessesAnomaly:
    a = StyleAnomaly('Array Accesses', anomaly.ARRAY_ACCESSES_REGEX, True, 0.9, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'int arr[];'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match2(self):
        code = 'cout << stringArr[i] << endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_match3(self):
        code = 'if (input[cnt + (cnt - 1)])'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.9)

    def test_multi_match(self):
        code = """
        int main() {
            listTwo.push_back(list[i]);
            cin >> arr[i];
            res = res + to_string(temp[i]) + ", ";
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (3, 2.7)

    def test_no_match1(self):
        code = 'cout << res.substr(0, res.size() - 2) << endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'cin >> x;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match3(self):
        code = 'newVector.push_back(inputVector.at(i));'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestNamespaceStdAnomaly:
    a = StyleAnomaly('Namespace Std', anomaly.NAMESPACE_STD_REGEX, True, 0.1, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'std::vector<int> vect;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match2(self):
        code = ' std::cout << "Hello " << first_name << "!" << std::endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match3(self):
        code = 'using std::cout;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_multi_match(self):
        code = """
        int main() {
            std::cin >> first_name;
            using std::cout;
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (2, 0.2)

    def test_no_match1(self):
        code = 'using namespace std;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'void A::fun()'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match3(self):
        code = 'cout << "Value of static x is " << Test::x;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestBraceStylingAnomaly:
    a = StyleAnomaly('Brace Styling', anomaly.BRACE_STYLING_REGEX, True, 0.1, -1, True)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = '   {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match2(self):
        code = 'cout << "Hello World!" << endl; }'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match3(self):
        code = 'if (tempVar == -1) { break; }'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match4(self):
        code = 'if (tempVar == -1) break; cout << endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_multi_match(self):
        code = """
        int main() {
            for (int i = 0; i < x; ++i) { break; }
            for (int i = 0; i < x; ++i) break; cout << endl;
            if (tempVar == -1) cout << endl;
            } else {
            else return 0;
            else cout << x << endl;
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (6, 0.6)

    def test_no_match1(self):
        code = 'if (tempVar == -1) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'for (i = 0; i < x; ++i) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match3(self):
        code = 'int main() {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_multi_not_match(self):
        code = """
        int main() {
            else if {
            else {
            else
            }
               }
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestUserDefinedFunctionsAnomaly:
    a = StyleAnomaly('User-Defined Functions', anomaly.USER_DEFINED_FUNCTIONS_REGEX, True, 0.8, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'unsigned int add(int x, int y) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.8)

    def test_match2(self):
        code = ' void printStatement(string s) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.8)

    def test_match3(self):
        code = 'void printMenu();'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.8)

    def test_multi_match(self):
        code = """
        int main() {
            long double pow(float x)
            int GetVectorMin(const vector<int>& Vec) {
            float max(float num1, float num2);
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (3, 2.4)

    def test_no_match1(self):
        code = 'int main() {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'vector<int> vect;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match3(self):
        code = 'int num = pow(2, 2);'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestTernaryOperatorAnomaly:
    a = StyleAnomaly('Ternary Operator', anomaly.TERNARY_OPERATOR_REGEX, True, 0.2, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'variable = Expression1 ? Expression2 : Expression3'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.2)

    def test_match2(self):
        code = '(condition) ? (variable = Expression2) : (variable = Expression3)'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.2)

    def test_match3(self):
        code = 'cout << (test ? fvalue : 0) << endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.2)

    def test_multi_match(self):
        code = """
        int main() {
            variable = (condition) ? Expression2 : Expression3
            cout << "Second character " << (test ? 3 : '1') << endl;
            cout << (test ? "A String" : 0) << endl;
            int max = a > b ? a : b;
            string result = (marks >= 40) ? "passed" : "failed";
            result = (number > 0) ? "Positive Number!" : "Negative Number!";
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (6, 1.2)

    def test_no_match1(self):
        code = 'string testString = "How do you do? Consider this: this test should fail."'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'cout << "This is a test ? " << "This is also a test:" << std::endl;  '
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestCommandLineArgumentsAnomaly:
    a = StyleAnomaly('Command-Line Arguments', anomaly.COMMAND_LINE_ARGUMENTS_REGEX, True, 0.8, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'int main(int argc, char* argv[])'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.8)

    def test_match2(self):
        code = 'int main(int argc, char** argv)'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.8)

    def test_multi_match(self):
        code = """
        int main() {
            int main(int argc, char *argv[]) {
            int main(int argc,char * argv[])
            int main(int argc, char **argv) {
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (3, 2.4)

    def test_no_match1(self):
        code = 'int main() {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'int max(int argc, char* argv[]) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match3(self):
        code = 'cout << "int argc, char** argv" << endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestNullsAnomaly:
    a = StyleAnomaly('Nulls', anomaly.NULLS_REGEX, True, 0.4, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'int* ptr = nullptr;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.4)

    def test_match2(self):
        code = 'int* ptr = NULL;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.4)

    def test_multi_match(self):
        code = """
        int main() {
            "x[0] = '\\0'"
            if (NULL == nullptr) {
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (2, 0.8)


class TestScopeOperatorAnomaly:
    a = StyleAnomaly('Scope Operator', anomaly.SCOPE_OPERATOR_REGEX, True, 0.25, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'void A::fun()'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.25)

    def test_match2(self):
        code = 'cout << "Value of static x is " << Test::x;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.25)

    def test_multi_match(self):
        code = """
        int main() {
            foo::foo()
            x = cstdlib::atoi(y);
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (2, 0.5)

    def test_no_match1(self):
        code = 'std::cout << "Hello" << std::endl;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'if (pos != string::npos) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestLineSpacingAnomaly:
    a = StyleAnomaly('Line Spacing', anomaly.LINE_SPACING_REGEX, True, 0.1, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_line_spacing_score(code, self.a)
        assert result == (0, 0)

    def test_multi_match1(self):
        # dedent() removes common leading space from each line
        # This makes the testcase code
        code = textwrap.dedent("""
        // Comment
        int main() {
        int x;      // Match 1
        cin >> x;   // Match 2
        }
        """)
        result = anomaly.get_line_spacing_score(code, self.a)
        assert result == (2, 0.2)

    def test_multi_match2(self):
        code = textwrap.dedent("""
        // Comment
        int user_func() {
            int x;
        cout << y;      // Match 1
        x = pow(1, 2);  // Match 2
        }
        """)
        result = anomaly.get_line_spacing_score(code, self.a)
        assert result == (2, 0.2)

    def test_multi_no_match(self):
        code = textwrap.dedent("""
        // Comment
        int user_func() 
        {
            return 0;
        }
        """)
        result = anomaly.get_line_spacing_score(code, self.a)
        assert result == (0, 0)


class TestMultipleDeclarationsSameLineAnomaly:
    a = StyleAnomaly('Multiple Declarations Same Line', anomaly.MULTIPLE_DECLARATIONS_REGEX, True, 0.3, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'int size,i,num,first,second;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.3)

    def test_match2(self):
        code = 'int a[x] , min, minx;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.3)

    def test_match3(self):
        code = 'int min = userNums[0], secondMin = userNums[1], temp;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.3)

    def test_multi_match(self):
        code = """
        int main() {
            int a[n],min,min2;
            int size, i, num, first, second;
            int n = vecs[0], n1 = vecs[1], current , temp;
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (3, 0.9)

    def test_no_match1(self):
        code = 'int i = 0; int j = 1;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'string testStr = "testing, with commas";'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestMultipleCinSameLineAnomaly:
    a = StyleAnomaly('Multiple Cin Same Line', anomaly.MULTIPLE_CIN_SAME_LINE_REGEX, True, 0.3, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'cin >> size >> min1 >> min2;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.3)

    def test_multi_match(self):
        code = """
        int main() {
            cin >> size >> min1 >> min2;
            cin >> smallest >> secSmallest >>x; 
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (2, 0.6)

    def test_no_match1(self):
        code = 'cin >> var;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestAndOrAnomaly:
    a = StyleAnomaly('and & or', anomaly.AND_OR_REGEX, True, 0.1, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'if (x and y) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match2(self):
        code = 'if (x or y) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_multi_match(self):
        code = """
        int main() {
            if (x && y and z) {
            if(arr[i]>=min and arr[i]<=max){
            if(arr[i]>=min || arr[i]<=max and arr[i] == max || arr[i] != max){
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (3, 0.3)

    def test_no_match1(self):
        code = 'if ( x && y ) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'if (x || y) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_multi_no_match(self):
        code = """
        int main() {
            if (string1 == "and" && string2 == "or") {
            if (string1 == "x or y" && string2 == "x and y") {
            if (string1 == "x and y" and string2 == "x or y") {
            if (string1 == "x and y" or string2 == "x or y") {
            if ("x and y" == string1 || "y or x" == string2) {
            if (string1 == 'x' and string2 == 'y' and string3 == 'z') {
            if (x && y && z || x && y && z) {
            if (varNameIncludesandHere && var2 == true) {
            if (var1and == true || orvar2 == false) {
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestListInitializationAnomaly:
    a = StyleAnomaly('List Initialization', anomaly.LIST_INIT_REGEX, True, 0.8, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'int numInput {};'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.8)

    def test_match2(self):
        code = 'bool var {0};'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.8)

    def test_multi_match(self):
        code = """
        int main() {
            float numTarget{};
            string var {"test"};
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (2, 1.6)

    def test_no_match1(self):
        code = 'vector<int> v{ 1, 2, 3 };'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = "char charArray[size]={'a', 'b'};"
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match3(self):
        code = 'int var = 0;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestVectorNameSpacingAnomaly:
    a = StyleAnomaly('Vector Name Spacing', anomaly.VECTOR_NAME_SPACING_REGEX, True, 0.1, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'vector<string>vectorName;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match2(self):
        code = 'vector<int>vect(n,10);'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_multi_match(self):
        code = """
        int main() {
            vector<double>vect{ 10, 20, 30 };
            vector<vector<string>>vect1(10);
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (2, 0.2)

    def test_no_match1(self):
        code = 'vector<string> vectorName;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'vector<int> vect(n,10);'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestSpacelessOperatorAnomaly:
    a = StyleAnomaly('Spaceless Operator', anomaly.SPACELESS_OPERATOR_REGEX, True, 0.1, -1, True)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'for(i=0;i<n;i++){'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match2(self):
        code = 'int n = (sizeof(A)/sizeof(A[0]));'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match3(self):
        code = 'if (x&&y) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_multi_match1(self):
        code = """
        int main() {
            if(A[i]<min){
            else if ( a[i]<minx) {
            while (i>=x) {
            while (sizeof(x)>=sizeof(y)) {
            if (x[i]||y[j]) {
            if (myVec[i]%2==0) {
            while (2!=0) {
            cout<<x<<y<<endl;
            cin>>x;
            cout << a[0]*b[1] << endl;
            varName-=1;
            j+=2;
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (12, 1.2)

    def test_multi_match2(self):
        code = """
        int main() {
            cout << "Hello" << x-10 << "World!" << endl;
            cout << "Hello World!" << 11-100 << endl;
            cout << "Hello World!" << 11-100 << "Hello Again!" << endl;
            cout << "Outputting " << a[i]-10 << " for testing." << endl;
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (4, 0.4)

    def test_no_match1(self):
        code = '#include <iostream>'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'vector<int> vec;'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_multi_no_match(self):
        code = """
        int main() {
            if(a[0] > a[1]) {
            if(a[i] <= min) {
            for ( int i = 0 ; i < x ; i++) {
            while (i < 10) {
            j += 2;
            cin >> x;
            cout << x << y << endl;
            string str1 = "Input must be 11-100";
            string str2 = "Input must be 11-100, please."
            cout << "Outputting a[i]-10" << endl;
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)


class TestControlStatementSpacingAnomaly:
    a = StyleAnomaly('Control Statement Spacing', anomaly.CONTROL_STATEMENT_SPACING_REGEX, True, 0.1, -1)

    def test_empty(self):
        code = ''
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_match1(self):
        code = 'for(int i = 0; i < n; i++){'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_match2(self):
        code = 'if(a[0] > a[1]) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (1, 0.1)

    def test_multi_match(self):
        code = """
        int main() {
            else if(a[i]<min2){
            while(x>y) {
        }
        """
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (2, 0.2)

    def test_no_match1(self):
        code = 'for (int i=0;i<n;i++) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)

    def test_no_match2(self):
        code = 'if (a[0] > a[1]) {'
        result = anomaly.get_single_anomaly_score(code, self.a)
        assert result == (0, 0)
