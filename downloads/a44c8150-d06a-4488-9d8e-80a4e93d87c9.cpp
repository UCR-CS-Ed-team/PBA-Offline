#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   getline (cin, firstName);
   cin >> wholeNumber;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}