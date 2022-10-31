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
  cin >> wholeNumber; /* Type your code here. */
   
   cout << firstName << " went to " << genericLocation << " to buy " << pluralNoun << " different types of " << wholeNumber << "." << endl;

   return 0;
}