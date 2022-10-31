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
   wholeNumber = 12;
   
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}