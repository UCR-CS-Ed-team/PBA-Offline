#include <iostream>
using namespace std;

int main() {
   int firstName;
   int genericLocation;
   int wholeNumber;
   int pluralNoun;
   cin >> firstName;
   cin >> genericLocation;
   cin >> wholeNumber;
   cin >> pluralNoun;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}