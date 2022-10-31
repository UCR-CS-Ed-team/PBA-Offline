#include <iostream>
#include <string>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   string wholeNumber;
   string pluralNoun;
   
   cin >> firstName >> genericLocation >> wholeNumber >> pluralNoun;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}