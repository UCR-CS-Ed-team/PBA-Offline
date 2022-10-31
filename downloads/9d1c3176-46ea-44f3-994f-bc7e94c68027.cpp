#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   cin >> firstName;
   cin >> genericLocation;
   cin >> pluralNoun;
   cin >> wholeNumber;
   
   cout << firstName << " went to " << genericLocation << " to buy " << string wholeNumber << " different types of " << string pluralNoun << "." << endl;

   return 0;
}