#include <iostream>
using namespace std;

int main() {
   int firstName;
   cin >> firstName;
   int genericLocation;
   cin >> genericLocation;
   int wholeNumber;
   cin >> wholeNumber;
   int pluralNoun;
   cin >> pluralNoun;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}