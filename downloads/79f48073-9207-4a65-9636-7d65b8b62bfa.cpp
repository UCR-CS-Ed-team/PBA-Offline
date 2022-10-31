#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;
   
   cin >> firstName;
   cin >> genericLocation;
   cin >> pluralNoun;
   cin >> wholeNumber;
   
   return 0;
}