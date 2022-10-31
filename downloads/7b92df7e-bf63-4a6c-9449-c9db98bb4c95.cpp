#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   cin >> firstName;
   cin >> genericLocation;
   cin >> int wholeNumber;
   cin >> string pluralNoun;
   
   
   cout << firstName << " went to " << genericLocation << " to buy " << int wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}