#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   cin >> firstName >> genericLocation;
   cin >> wholeNumber;
   cin >> pluralNoun;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}